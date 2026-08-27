# -*- coding: utf-8 -*-
"""P-016 WP5 본분석 — 제3자배정 PIPE의 +12개월 누적 로그고용 풀드 ATT (entropy-balanced 매칭 stacked event study).
사전확정(WP4 PAP): entropy balancing 1차, SESOI=0.20×(대조풀 사전 12m 로그고용변화 SD), block bootstrap 200, rule11 등가성 게이트.
Phase A(outcome-blind): SESOI freeze. Phase B: EB weights → 캘린더정렬 τ_k(-12..+12) → ATT+12 → 사전추세 등가성 → post-weight balance.
산출: shared/outputs/pipe_wp5_2026-08-22/wp5_main.json · wp4_pap_committed.json
"""
import os,json,warnings,math; warnings.filterwarnings("ignore")
import numpy as np,pandas as pd
from scipy.optimize import minimize
BASE=os.environ.get("P016_BASE", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))   # 원 경로는 제거했다 — 실행 시 P016_BASE 로 지정하거나 기본값 사용
RE=f"{BASE}/shared/outputs/pipe_r1_reextract_2026-08-22"
OUT=f"{BASE}/shared/outputs/pipe_wp5_2026-08-22"; os.makedirs(OUT,exist_ok=True)
RNG=np.random.default_rng(20260822)

# ---- 처치 ----
T=pd.read_csv(f"{RE}/treatment_master_v2.csv",dtype=str)
T["k"]=T["k"].str.replace(r'\D','',regex=True).str.zfill(10)
T["ev"]=pd.to_datetime(T["event_dt"],errors="coerce").dt.to_period("M")
T=T.dropna(subset=["ev"]).drop_duplicates("k")

# ---- NPS 패널 → wide 로그고용 (firm×month) ----
nps=pd.read_parquet(f"{BASE}/shared/data/processed/nps_monthly_matched_v2.parquet",
                    columns=["bn10","data_ym","가입자수","업종","시도"])
nps["ym"]=pd.PeriodIndex(nps["data_ym"],freq="M")
nps["le"]=np.log1p(nps["가입자수"].astype(float))
months=pd.period_range(nps.ym.min(),nps.ym.max(),freq="M")
mi={m:j for j,m in enumerate(months)}
W=nps.pivot_table(index="bn10",columns="ym",values="le",aggfunc="mean")
W=W.reindex(columns=months)
firm_ix={b:i for i,b in enumerate(W.index)}
Wv=W.to_numpy(dtype=float)            # (nfirm, nmonth) 로그고용, 결측 NaN
# firm 정적 공변량 (industry2 최빈, 시도 최빈)
firm_ind=nps.groupby("bn10")["업종"].agg(lambda s:str(s.iloc[0])[:2])
firm_sido=nps.groupby("bn10")["시도"].agg(lambda s:str(s.iloc[0]))
firm_med_le=np.nanmedian(np.where(np.isfinite(Wv),Wv,np.nan),axis=1)  # firm median 로그고용

# ---- 대조풀 (never-PIPE) ----
pb=pd.read_csv(f"{BASE}/shared/data/processed/pitchbook_all_status_v1.csv",dtype=str)
pbbn=set(pb["bn"].astype(str).str.replace(r'\D','',regex=True).str.zfill(10).dropna())
treated_bn=set(T.k)
is_ctrl=np.array([ (b not in pbbn) and (b not in treated_bn) for b in W.index])
is_treat_panel=np.array([b in treated_bn for b in W.index])

# ============ Phase A: SESOI freeze (outcome-blind, 대조풀 사전분산) ============
def growth_series_12m(rowvals):
    # 각 t에서 (le[t]-le[t-12]) 관측; 대조풀 전반 분산
    d=rowvals[12:]-rowvals[:-12]
    return d[np.isfinite(d)]
ctrl_rows=np.where(is_ctrl)[0]
alld=[]
for r in ctrl_rows:
    d=growth_series_12m(Wv[r])
    if d.size: alld.append(d)
allc=np.concatenate(alld) if alld else np.array([0.0])
sd_ctrl12=float(np.std(allc,ddof=1))
SESOI=round(0.20*sd_ctrl12,4)
pap=dict(committed="2026-08-22",outcome_blind=True,
         SESOI_rule="0.20 × 대조풀 사전 12개월 로그고용변화 SD",
         control_12m_logchange_sd=round(sd_ctrl12,4),SESOI=SESOI,
         primary_estimator="entropy_balancing",bootstrap_reps=200,
         estimation_sample="usable >=3pre/>=3post",horizon_headline=12)
json.dump(pap,open(f"{BASE}/papers/P016_pipe-employment/04_design/wp4_pap_committed.json","w"),ensure_ascii=False,indent=1)
print(f"[Phase A] SESOI freeze: 대조 12m logΔ SD={sd_ctrl12:.4f} → SESOI={SESOI} (outcome-blind)",flush=True)

# ============ 처치 baseline·공변량·usable 판정 ============
PRE=3; POST=12; PREW=13
rec=[]
for r in T.itertuples():
    if r.k not in firm_ix: continue
    fi=firm_ix[r.k]; e=mi.get(r.ev)
    if e is None: continue
    row=Wv[fi]
    # baseline = e-3..e-1 평균
    if e-PRE<0 or e+POST>=len(months): pass
    pre_idx=[e-j for j in range(1,PRE+1) if 0<=e-j<len(months)]
    post_ok=[e+j for j in range(1,POST+1) if 0<=e+j<len(months)]
    npre=sum(np.isfinite(row[i]) for i in pre_idx)
    npost=sum(np.isfinite(row[e+j]) for j in range(1,POST+1) if 0<=e+j<len(months))
    if npre<PRE or npost<3:   # usable >=3pre/>=3post
        continue
    base=np.nanmean([row[i] for i in pre_idx])
    # pregrowth = le(e-1)-le(e-13)
    pg=np.nan
    if 0<=e-1<len(months) and 0<=e-PREW<len(months) and np.isfinite(row[e-1]) and np.isfinite(row[e-PREW]):
        pg=row[e-1]-row[e-PREW]
    rec.append(dict(k=r.k,fi=fi,e=e,base=base,logsize=base,pregrowth=pg,
                    ind=firm_ind.get(r.k,"99"),sido=firm_sido.get(r.k,"0")))
Tm=pd.DataFrame(rec)
Tm=Tm.dropna(subset=["pregrowth"])
print(f"[표본] usable(>=3/>=3) 처치 {len(Tm)}",flush=True)

# ---- 공변량 행렬 (처치=이벤트baseline, 대조=firm median) ----
def capital(sido): return 1.0 if str(sido) in ("11","41","28") else 0.0
def manuf(ind):
    try: return 1.0 if 10<=int(ind)<=34 else 0.0
    except: return 0.0
# 처치 공변량
Xt=np.column_stack([Tm.logsize.values, Tm.logsize.values**2, Tm.pregrowth.values,
                    Tm.sido.map(capital).values, Tm.ind.map(manuf).values])
# 대조 공변량 (firm median logsize, pregrowth=firm 평균 12m logΔ)
ctrl_pg=[]
for r in ctrl_rows:
    d=growth_series_12m(Wv[r]); ctrl_pg.append(np.nanmean(d) if d.size else np.nan)
ctrl_pg=np.array(ctrl_pg)
ctrl_ls=firm_med_le[ctrl_rows]
ctrl_ind=np.array([manuf(firm_ind.get(W.index[r],"99")) for r in ctrl_rows])
ctrl_cap=np.array([capital(firm_sido.get(W.index[r],"0")) for r in ctrl_rows])
okc=np.isfinite(ctrl_ls)&np.isfinite(ctrl_pg)
ctrl_rows2=ctrl_rows[okc]
Xc=np.column_stack([ctrl_ls[okc],ctrl_ls[okc]**2,ctrl_pg[okc],ctrl_cap[okc],ctrl_ind[okc]])
print(f"[대조] EB 후보 {len(ctrl_rows2)}",flush=True)

# ---- Entropy balancing: 대조 재가중 → 처치 적률 일치 ----
mt=Xt.mean(0); sdx=Xt.std(0,ddof=1); sdx[sdx==0]=1
Zc=(Xc-mt)/sdx           # 처치평균 기준 표준화 (목표 가중평균=0)
def loss(lam):
    a=-Zc@lam; a-=a.max(); w=np.exp(a); Z=w.sum()
    return math.log(Z)      # + lam·0
def grad(lam):
    a=-Zc@lam; a-=a.max(); w=np.exp(a); w/=w.sum()
    return -(w[:,None]*Zc).sum(0)
res=minimize(loss,np.zeros(Zc.shape[1]),jac=grad,method="BFGS",options={"maxiter":500})
a=-Zc@res.x; a-=a.max(); wc=np.exp(a); wc/=wc.sum()
smd_before=(Xc.mean(0)-mt)/np.sqrt((Xt.var(0,ddof=1)+Xc.var(0,ddof=1))/2)
Xc_wm=(wc[:,None]*Xc).sum(0)
smd_after=(Xc_wm-mt)/np.sqrt((Xt.var(0,ddof=1)+Xc.var(0,ddof=1))/2)
ess=1.0/np.sum(wc**2)
print(f"[EB] SMD before max={np.abs(smd_before).max():.3f} after max={np.abs(smd_after).max():.3f} · ESS={ess:.0f}",flush=True)

# ---- 캘린더정렬 event-study: 처치 i별 contribution_i(k) ----
KS=list(range(-12,13))
Cmat=np.full((len(Tm),len(KS)),np.nan)
Wc_mat=Wv[ctrl_rows2]           # (nctrl, nmonth)
for ii,r in enumerate(Tm.itertuples()):
    e=r.e; base_t=r.base
    # 대조 baseline (동일 캘린더 e-3..e-1)
    bcols=[e-j for j in range(1,PRE+1) if 0<=e-j<len(months)]
    cb=np.nanmean(Wc_mat[:,bcols],axis=1)      # (nctrl,)
    for kj,k in enumerate(KS):
        t=e+k
        if not(0<=t<len(months)): continue
        yt=Wv[r.fi,t]
        if not np.isfinite(yt): continue
        Dt=yt-base_t
        yc=Wc_mat[:,t]
        m=np.isfinite(yc)&np.isfinite(cb)
        if m.sum()<30: continue
        ww=wc[m]; ww=ww/ww.sum()
        Dc=np.sum(ww*(yc[m]-cb[m]))
        Cmat[ii,kj]=Dt-Dc
# τ_k = mean_i, block bootstrap (처치 재표집)
def tau_of(rows):
    return np.array([np.nanmean(Cmat[rows,kj]) for kj in range(len(KS))])
tau=tau_of(np.arange(len(Tm)))
B=200; boot=np.full((B,len(KS)),np.nan)
n=len(Tm)
for b in range(B):
    rows=RNG.integers(0,n,n)
    boot[b]=tau_of(rows)
lo=np.nanpercentile(boot,2.5,axis=0); hi=np.nanpercentile(boot,97.5,axis=0)
se=np.nanstd(boot,axis=0,ddof=1)
kidx={k:j for j,k in enumerate(KS)}
att12=float(tau[kidx[12]]); att12_lo=float(lo[kidx[12]]); att12_hi=float(hi[kidx[12]])
post=[kidx[k] for k in range(1,13)]
attavg=float(np.nanmean(tau[post]))
# 사전추세 등가성 게이트 (rule 11): k=-12..-1
pre_gate=[]
for k in range(-12,0):
    j=kidx[k]
    within = (lo[j]>=-SESOI) and (hi[j]<=SESOI)
    pre_gate.append(dict(k=k,tau=round(float(tau[j]),4),lo=round(float(lo[j]),4),hi=round(float(hi[j]),4),
                         within_SESOI=bool(within),
                         margin_up=round(float(SESOI-hi[j]),4),margin_dn=round(float(lo[j]+SESOI),4)))
n_pass=sum(1 for g in pre_gate if g["within_SESOI"])
print(f"[결과] ATT+12={att12:.4f} CI[{att12_lo:.4f},{att12_hi:.4f}] · post평균={attavg:.4f} · 사전추세 등가통과 {n_pass}/12",flush=True)

es=[dict(k=k,tau=round(float(tau[kidx[k]]),4),lo=round(float(lo[kidx[k]]),4),
         hi=round(float(hi[kidx[k]]),4),se=round(float(se[kidx[k]]),4)) for k in KS]
result=dict(id="P016-WP5",date="2026-08-22",estimator="entropy_balancing_calendar_aligned_stacked_ES",
            n_treated=int(len(Tm)),n_control_eb=int(len(ctrl_rows2)),ess_control=round(float(ess),1),
            SESOI=SESOI,
            balance=dict(covs=["logsize","logsize2","pregrowth","capital","manuf"],
                         smd_before=[round(float(x),4) for x in smd_before],
                         smd_after=[round(float(x),4) for x in smd_after],
                         max_abs_smd_after=round(float(np.abs(smd_after).max()),4)),
            ATT_plus12=dict(point=round(att12,4),ci95=[round(att12_lo,4),round(att12_hi,4)],
                            se=round(float(se[kidx[12]]),4)),
            ATT_avg_post1_12=round(attavg,4),
            event_study=es, pretrend_equivalence_gate=pre_gate, pretrend_pass=f"{n_pass}/12")
json.dump(result,open(f"{OUT}/wp5_main.json","w"),ensure_ascii=False,indent=1)
open(f"{OUT}/wp5.done","w").write("done")
print("\n=== WP5 완료 ===")
print(f"ATT+12={att12:.4f} ({att12_lo:.4f},{att12_hi:.4f}) · post평균 ATT={attavg:.4f} · balance max|SMD|→{np.abs(smd_after).max():.3f} · 사전추세 {n_pass}/12")
