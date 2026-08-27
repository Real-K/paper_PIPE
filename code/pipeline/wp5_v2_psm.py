# -*- coding: utf-8 -*-
"""P-016 WP5 v2 — PSM k-NN(공통지지 제한) 매칭 stacked event study. v1 EB overlap 실패의 측정근거 전환(D-2026-08-22-WP5v1).
SESOI는 wp4_pap_committed.json 동결값(0.0559) 재사용 — 재계산 안 함.
공통지지: 대조 PS를 처치 PS 범위로 제한. 매칭: 선형예측자(Xβ) NN k=10, caliper=0.2×SD(Xβ). 캘린더정렬 DiD. bootstrap 200.
산출: shared/outputs/pipe_wp5_2026-08-22/wp5_v2_psm.json
"""
import os,json,warnings,math; warnings.filterwarnings("ignore")
import numpy as np,pandas as pd
import statsmodels.api as sm
BASE=os.environ.get("P016_BASE", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))   # 원 경로는 제거했다 — 실행 시 P016_BASE 로 지정하거나 기본값 사용
RE=f"{BASE}/shared/outputs/pipe_r1_reextract_2026-08-22"
OUT=f"{BASE}/shared/outputs/pipe_wp5_2026-08-22"
RNG=np.random.default_rng(20260822)
SESOI=json.load(open(f"{BASE}/papers/P016_pipe-employment/04_design/wp4_pap_committed.json"))["SESOI"]
print(f"SESOI(동결) {SESOI}",flush=True)

T=pd.read_csv(f"{RE}/treatment_master_v2.csv",dtype=str)
T["k"]=T["k"].str.replace(r'\D','',regex=True).str.zfill(10)
T["ev"]=pd.to_datetime(T["event_dt"],errors="coerce").dt.to_period("M")
T=T.dropna(subset=["ev"]).drop_duplicates("k")
nps=pd.read_parquet(f"{BASE}/shared/data/processed/nps_monthly_matched_v2.parquet",
                    columns=["bn10","data_ym","가입자수","업종","시도"])
nps["ym"]=pd.PeriodIndex(nps["data_ym"],freq="M"); nps["le"]=np.log1p(nps["가입자수"].astype(float))
months=pd.period_range(nps.ym.min(),nps.ym.max(),freq="M"); mi={m:j for j,m in enumerate(months)}
W=nps.pivot_table(index="bn10",columns="ym",values="le",aggfunc="mean").reindex(columns=months)
firm_ix={b:i for i,b in enumerate(W.index)}; Wv=W.to_numpy(dtype=float)
firm_ind=nps.groupby("bn10")["업종"].agg(lambda s:str(s.iloc[0])[:2])
firm_sido=nps.groupby("bn10")["시도"].agg(lambda s:str(s.iloc[0]))
firm_med_le=np.nanmedian(np.where(np.isfinite(Wv),Wv,np.nan),axis=1)
pb=pd.read_csv(f"{BASE}/shared/data/processed/pitchbook_all_status_v1.csv",dtype=str)
pbbn=set(pb["bn"].astype(str).str.replace(r'\D','',regex=True).str.zfill(10).dropna())
treated_bn=set(T.k)
def capital(s): return 1.0 if str(s) in ("11","41","28") else 0.0
def manuf(i):
    try: return 1.0 if 10<=int(i)<=34 else 0.0
    except: return 0.0
def g12(row): d=row[12:]-row[:-12]; return d[np.isfinite(d)]

PRE=3;POST=12;PREW=13;KS=list(range(-12,13));kidx={k:j for j,k in enumerate(KS)}
# 처치 usable + 공변량
rec=[]
for r in T.itertuples():
    if r.k not in firm_ix: continue
    fi=firm_ix[r.k]; e=mi.get(r.ev)
    if e is None: continue
    row=Wv[fi]
    pre_idx=[e-j for j in range(1,PRE+1) if 0<=e-j<len(months)]
    npre=sum(np.isfinite(row[i]) for i in pre_idx)
    npost=sum(np.isfinite(row[e+j]) for j in range(1,POST+1) if 0<=e+j<len(months))
    if npre<PRE or npost<3: continue
    if not(0<=e-1<len(months) and 0<=e-PREW<len(months)): continue
    if not(np.isfinite(row[e-1]) and np.isfinite(row[e-PREW])): continue
    base=np.nanmean([row[i] for i in pre_idx]); pg=row[e-1]-row[e-PREW]
    rec.append(dict(k=r.k,fi=fi,e=e,base=base,logsize=base,pregrowth=pg,
                    cap=capital(firm_sido.get(r.k,"0")),man=manuf(firm_ind.get(r.k,"99"))))
Tm=pd.DataFrame(rec); print(f"처치 usable {len(Tm)}",flush=True)
# 대조 공변량
crows=np.array([i for i,b in enumerate(W.index) if (b not in pbbn) and (b not in treated_bn)])
cpg=np.array([np.nanmean(g12(Wv[r])) if g12(Wv[r]).size else np.nan for r in crows])
cls=firm_med_le[crows]
ok=np.isfinite(cls)&np.isfinite(cpg); crows=crows[ok]; cls=cls[ok]; cpg=cpg[ok]
ccap=np.array([capital(firm_sido.get(W.index[r],"0")) for r in crows])
cman=np.array([manuf(firm_ind.get(W.index[r],"99")) for r in crows])
print(f"대조 후보 {len(crows)}",flush=True)
# PS logit
Xt=np.column_stack([Tm.logsize,Tm.logsize**2,Tm.pregrowth,Tm.cap,Tm.man])
Xc=np.column_stack([cls,cls**2,cpg,ccap,cman])
X=np.vstack([Xt,Xc]); y=np.r_[np.ones(len(Xt)),np.zeros(len(Xc))]
Xs=(X-X.mean(0))/X.std(0); Xd=sm.add_constant(Xs)
ps=sm.Logit(y,Xd).fit(disp=0)
xb=ps.predict(Xd,linear=True)
xbt=xb[:len(Xt)]; xbc=xb[len(Xt):]
# 공통지지: 대조 xb를 처치 xb 범위로 제한
lo,hi=xbt.min(),xbt.max(); supp=(xbc>=lo)&(xbc<=hi)
crows_s=crows[supp]; xbc_s=xbc[supp]
print(f"공통지지 대조 {len(crows_s)} (범위 [{lo:.2f},{hi:.2f}])",flush=True)
# NN k=10 caliper
K=10; cal=0.2*np.std(xb)
order=np.argsort(xbc_s); xbc_sorted=xbc_s[order]; crows_sorted=crows_s[order]
def knn(xbi):
    pos=np.searchsorted(xbc_sorted,xbi)
    cand=list(range(max(0,pos-K-2),min(len(xbc_sorted),pos+K+2)))
    d=np.abs(xbc_sorted[cand]-xbi); sel=np.argsort(d)[:K]
    idx=[cand[s] for s in sel if d[s]<=cal]
    return [crows_sorted[j] for j in idx]
matches=[knn(x) for x in xbt]
nmatched=sum(1 for m in matches if m)
print(f"매칭된 처치 {nmatched}/{len(Tm)} (caliper {cal:.3f})",flush=True)
# post-match balance (처치 vs 풀드 매칭대조, 균등가중)
mc_rows=[];
for m in matches: mc_rows.extend(m)
mc_rows=np.array(mc_rows)
def smd(a,b):
    return (a.mean(0)-b.mean(0))/np.sqrt((a.var(0,ddof=1)+b.var(0,ddof=1))/2)
Xc_all=np.column_stack([cls,cls**2,cpg,ccap,cman])
cmap={r:j for j,r in enumerate(crows)}
Xmc=np.array([Xc_all[cmap[r]] for r in mc_rows])
smd_before=smd(Xc_all,Xt); smd_after=smd(Xmc,Xt)
print(f"balance post-match max|SMD|={np.abs(smd_after).max():.3f} (before {np.abs(smd_before).max():.3f})",flush=True)
# 캘린더정렬 event study
Cmat=np.full((len(Tm),len(KS)),np.nan)
for ii,r in enumerate(Tm.itertuples()):
    m=matches[ii]
    if not m: continue
    e=r.e; base_t=r.base
    bcols=[e-j for j in range(1,PRE+1) if 0<=e-j<len(months)]
    for k in KS:
        t=e+k
        if not(0<=t<len(months)): continue
        yt=Wv[r.fi,t]
        if not np.isfinite(yt): continue
        Dt=yt-base_t
        dc=[]
        for c in m:
            cb=np.nanmean(Wv[c,bcols]); yc=Wv[c,t]
            if np.isfinite(cb) and np.isfinite(yc): dc.append(yc-cb)
        if len(dc)<3: continue
        Cmat[ii,kidx[k]]=Dt-np.mean(dc)
def tau_of(rows): return np.array([np.nanmean(Cmat[rows,j]) for j in range(len(KS))])
valid=np.array([i for i in range(len(Tm)) if matches[i]])
tau=tau_of(valid)
B=200; boot=np.full((B,len(KS)),np.nan); n=len(valid)
for b in range(B):
    rows=valid[RNG.integers(0,n,n)]; boot[b]=tau_of(rows)
loci=np.nanpercentile(boot,2.5,0); hici=np.nanpercentile(boot,97.5,0); se=np.nanstd(boot,0,ddof=1)
att12=float(tau[kidx[12]]); attavg=float(np.nanmean([tau[kidx[k]] for k in range(1,13)]))
pre_gate=[]
for k in range(-12,0):
    j=kidx[k]; within=(loci[j]>=-SESOI)and(hici[j]<=SESOI)
    pre_gate.append(dict(k=k,tau=round(float(tau[j]),4),lo=round(float(loci[j]),4),hi=round(float(hici[j]),4),within_SESOI=bool(within)))
npass=sum(1 for g in pre_gate if g["within_SESOI"])
es=[dict(k=k,tau=round(float(tau[kidx[k]]),4),lo=round(float(loci[kidx[k]]),4),hi=round(float(hici[kidx[k]]),4)) for k in KS]
res=dict(id="P016-WP5v2",estimator="PSM_kNN_commonsupport_calendar_aligned",SESOI=SESOI,
         n_treated=int(len(Tm)),n_matched=int(nmatched),n_control_support=int(len(crows_s)),k_neighbors=K,caliper=round(float(cal),4),
         balance=dict(covs=["logsize","logsize2","pregrowth","capital","manuf"],
                      smd_before=[round(float(x),4) for x in smd_before],smd_after=[round(float(x),4) for x in smd_after],
                      max_abs_smd_after=round(float(np.abs(smd_after).max()),4)),
         ATT_plus12=dict(point=round(att12,4),ci95=[round(float(loci[kidx[12]]),4),round(float(hici[kidx[12]]),4)],se=round(float(se[kidx[12]]),4)),
         ATT_avg_post1_12=round(attavg,4),event_study=es,pretrend_equivalence_gate=pre_gate,pretrend_pass=f"{npass}/12")
json.dump(res,open(f"{OUT}/wp5_v2_psm.json","w"),ensure_ascii=False,indent=1)
open(f"{OUT}/wp5v2.done","w").write("done")
print(f"\n=== WP5 v2 완료 ===\nATT+12={att12:.4f} CI[{loci[kidx[12]]:.4f},{hici[kidx[12]]:.4f}] · post평균={attavg:.4f} · balance max|SMD|={np.abs(smd_after).max():.3f} · 사전추세 {npass}/12 · 매칭 {nmatched}/{len(Tm)}")
