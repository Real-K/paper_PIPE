# WP13 재실행 사본 (2026-08-26): 정규화 마스터(382 dated)로 동일 코드 재실행. 원본 wp11fg_honest_grid.py · 출력 폴더만 pipe_wp13_2026-08-26 으로 치환.
# -*- coding: utf-8 -*-
"""WP11fg — G6 HonestDiD-RM(근사) mean+tail & G8 frozen placebo grid(equivalence).
(f) 상장풀 event-study τ_k(mean)와 τ^Z_k(collapse율차, c=−0.35): RM 근사 — 월별 위반 ≤ M̄·maxpre(연속 pre변화 최대),
    avg(+7..+12) 누적편의 ≤ M̄·maxpre·9.5 → breakdown M̄*(CI 상단이 0 닿는 M̄). 사전선언: M̄*≥1이면 '관측 최대 사전위반 이상까지 강건'.
(g) placebo grid shift∈{36,30,24,18}: mean d CI vs δ_mean=0.0479(SESOI_listed) · tail ATT(c=−0.35) CI vs δ_tail=0.05(사전선언).
    판정=equivalence(CI⊂±δ), non-rejection 아님(§13·§22).
산출: shared/outputs/pipe_wp13_2026-08-26/wp11fg.json
"""
import os,json,csv,re,warnings; warnings.filterwarnings("ignore")
import numpy as np,pandas as pd
import statsmodels.api as sm
BASE=os.environ.get("P016_BASE", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))   # 원 경로는 제거했다 — 실행 시 P016_BASE 로 지정하거나 기본값 사용
RE=f"{BASE}/shared/outputs/pipe_r1_reextract_2026-08-22"
OUT=f"{BASE}/shared/outputs/pipe_wp13_2026-08-26"
RNG=np.random.default_rng(20260823)
D_MEAN=0.0479; D_TAIL=0.05; CTH=-0.35
listed=set()
with open(f"{BASE}/PI/drops/재무데이터_2009_2025_통합.csv",encoding='utf-8') as f:
    rd=csv.reader(f); next(rd)
    for row in rd:
        if len(row)<6: continue
        if re.match(r'^A\d{6}$',row[0].lstrip('﻿')):
            bn=re.sub(r'\D','',row[5]).zfill(10)
            if len(bn)==10 and bn!="0000000000": listed.add(bn)
nps=pd.read_parquet(f"{BASE}/shared/data/processed/nps_monthly_matched_v2.parquet",columns=["bn10","data_ym","가입자수","업종","시도"])
nps["ym"]=pd.PeriodIndex(nps["data_ym"],freq="M"); nps["le"]=np.log1p(nps["가입자수"].astype(float))
months=pd.period_range(nps.ym.min(),nps.ym.max(),freq="M"); mi={m:j for j,m in enumerate(months)}; NM=len(months)
piv=nps.pivot_table(index="bn10",columns="ym",values="le",aggfunc="mean").reindex(columns=months)
idx=list(piv.index); fx={b:i for i,b in enumerate(idx)}; LE=piv.to_numpy(float)
firm_ind=nps.groupby("bn10")["업종"].agg(lambda s:str(s.iloc[0])[:2]); firm_sido=nps.groupby("bn10")["시도"].agg(lambda s:str(s.iloc[0]))
firm_med=np.nanmedian(np.where(np.isfinite(LE),LE,np.nan),axis=1)
pb=pd.read_csv(f"{BASE}/shared/data/processed/pitchbook_all_status_v1.csv",dtype=str)
pbbn=set(pb["bn"].astype(str).str.replace(r'\D','',regex=True).str.zfill(10).dropna())
T=pd.read_csv(f"{RE}/treatment_master_v2.csv",dtype=str); T["k"]=T["k"].str.replace(r'\D','',regex=True).str.zfill(10)
T=T[pd.to_numeric(T.event_dt.astype(str).str[:4],errors="coerce").between(2015,2025)]   # 표본기간 2015–2025(원고 명시). 날짜 정규화로 유입된 2010–2014·2026 이벤트 제외 — WP13, 2026-08-27
T["ev"]=pd.to_datetime(T["event_dt"],errors="coerce").dt.to_period("M"); T=T.dropna(subset=["ev"]).drop_duplicates("k"); tb=set(T.k)
T=T[T.k.isin({l.strip() for l in open(f"{BASE}/shared/outputs/pipe_wp13_2026-08-26/emp_primary_k.txt") if l.strip()})]  # WP13: 고정 1차표본(210)
def cap(s): return 1.0 if str(s) in ("11","41","28") else 0.0
def man(i):
    try: return 1.0 if 10<=int(i)<=34 else 0.0
    except: return 0.0
def g12(r): d=r[12:]-r[:-12]; return d[np.isfinite(d)]
_cl=set(pd.read_csv(f"{BASE}/shared/outputs/pipe_wp13_2026-08-26/controls_clean.csv",dtype=str).query("third_hist=='False'").bn.str.replace(r"\D","",regex=True).str.zfill(10))  # WP13: clean pool 통일(C-A5)
ctrl=[b for b in idx if (b in listed) and (b not in pbbn) and (b not in tb)]
ctrl=[b for b in ctrl if b in _cl]
crows=np.array([fx[b] for b in ctrl])
cpg=np.array([np.nanmean(g12(LE[r])) if g12(LE[r]).size else np.nan for r in crows]); cls=firm_med[crows]
okc=np.isfinite(cls)&np.isfinite(cpg); crows=crows[okc]; cls=cls[okc]; cpg=cpg[okc]
ccap=np.array([cap(firm_sido.get(idx[r],"0")) for r in crows]); cman=np.array([man(firm_ind.get(idx[r],"99")) for r in crows])
Xc=np.column_stack([cls,cls**2,cpg,ccap,cman])
def build(shift):
    rec=[]
    for r in T.itertuples():
        if r.k not in fx: continue
        e0=mi.get(r.ev)
        if e0 is None: continue
        e=e0-shift
        if e-13<0 or e+12>=NM: continue
        row=LE[fx[r.k]]
        if not(np.isfinite(row[e-1]) and np.isfinite(row[e-13])): continue
        if sum(np.isfinite(row[e-j]) for j in range(1,4))<3 or sum(np.isfinite(row[e+j]) for j in range(1,13))<3: continue
        rec.append(dict(k=r.k,fi=fx[r.k],e=e,logsize=np.nanmean([row[e-j] for j in range(1,4)]),pregrowth=row[e-1]-row[e-13],cap=cap(firm_sido.get(r.k,"0")),man=man(firm_ind.get(r.k,"99"))))
    return pd.DataFrame(rec)
def match_struct(Tm):
    Xt=np.column_stack([Tm.logsize,Tm.logsize**2,Tm.pregrowth,Tm.cap,Tm.man])
    X=np.vstack([Xt,Xc]); y=np.r_[np.ones(len(Xt)),np.zeros(len(Xc))]; Xs=(X-X.mean(0))/X.std(0)
    lgt=sm.Logit(y,sm.add_constant(Xs)).fit(disp=0); xb=np.asarray(lgt.predict(sm.add_constant(Xs),linear=True))
    xbt=xb[:len(Xt)]; xbc=xb[len(Xt):]
    lo,hi=xbt.min(),xbt.max(); supp=(xbc>=lo)&(xbc<=hi); CSr=crows[supp]; xbcs=xbc[supp]; calp=0.2*np.std(xb); K=50
    o=np.argsort(xbcs); XS=xbcs[o]; CS=CSr[o]
    ms=[]
    for ii in range(len(Tm)):
        p=np.searchsorted(XS,xbt[ii]); cand=list(range(max(0,p-K-2),min(len(XS),p+K+2)))
        dd=np.abs(XS[cand]-xbt[ii]); sel=np.argsort(dd)[:K]
        ms.append([CS[cand[s]] for s in sel if dd[s]<=calp])
    return ms
# ===== (f) event-study 경로 (mean & tail indicator) — shift 0 =====
Tm=build(0); M=match_struct(Tm)
KS=list(range(-12,13)); kx={k:j for j,k in enumerate(KS)}
Cm=np.full((len(Tm),len(KS)),np.nan); Cz=np.full((len(Tm),len(KS)),np.nan)
for ii,r in enumerate(Tm.itertuples()):
    m=M[ii]
    if not m: continue
    e=r.e; bc=list(range(e-12,e)); bt_=np.nanmean(LE[r.fi,bc])
    if np.sum(np.isfinite(LE[r.fi,bc]))<6 or not np.isfinite(bt_): continue
    cb={c:np.nanmean(LE[c,bc]) for c in m}
    for k in KS:
        t=e+k
        if not(0<=t<NM) or not np.isfinite(LE[r.fi,t]): continue
        dc=[LE[c,t]-cb[c] for c in m if np.isfinite(cb[c]) and np.isfinite(LE[c,t])]
        if len(dc)<3: continue
        own=LE[r.fi,t]-bt_
        Cm[ii,kx[k]]=own-np.mean(dc)
        Cz[ii,kx[k]]=(1.0 if own<=CTH else 0.0)-np.mean([1.0 if x<=CTH else 0.0 for x in dc])
def path(C):
    tau=np.array([np.nanmean(C[:,j]) for j in range(len(KS))])
    B=800; boot=np.array([[np.nanmean(C[RNG.integers(0,len(C),len(C)),j]) for j in range(len(KS))] for _ in range(B)])
    se=np.nanstd(boot,0,ddof=1)
    return tau,se
tau_m,se_m=path(Cm); tau_z,se_z=path(Cz)
def rm_breakdown(tau,se):
    pre=[tau[kx[k]] for k in range(-12,0)]
    maxpre=max(abs(pre[j+1]-pre[j]) for j in range(len(pre)-1))
    pj=[kx[k] for k in range(7,13)]
    eff=float(np.nanmean(tau[pj])); sef=float(np.sqrt(np.nanmean(se[pj]**2)/len(pj))*np.sqrt(len(pj)))/len(pj)**0  # 근사: 평균 se
    sef=float(np.nanmean(se[pj]))/np.sqrt(len(pj))
    grid=[0,0.25,0.5,0.75,1.0,1.5,2.0]; rows=[]
    for Mb in grid:
        b=Mb*maxpre*9.5
        lo=eff-1.96*sef-b; hi=eff+1.96*sef+b
        rows.append(dict(Mbar=Mb,ci=[round(lo,4),round(hi,4)],excl0=bool(hi<0 or lo>0)))
    # breakdown
    bd=(abs(eff)-1.96*sef)/(maxpre*9.5) if (abs(eff)-1.96*sef)>0 and maxpre>0 else 0.0
    return dict(effect=round(eff,4),se=round(sef,4),maxpre=round(float(maxpre),5),breakdown_Mbar=round(float(bd),3),grid=rows)
f_mean=rm_breakdown(tau_m,se_m); f_tail=rm_breakdown(tau_z,se_z)
print("(f) HonestDiD-RM mean:",{k:f_mean[k] for k in ("effect","maxpre","breakdown_Mbar")},flush=True)
print("(f) HonestDiD-RM tail(c=-0.35):",{k:f_tail[k] for k in ("effect","maxpre","breakdown_Mbar")},flush=True)
# ===== (g) placebo grid =====
grid_res={}
for sh in (36,30,24,18):
    Tp=build(sh); Mp=match_struct(Tp)
    dm=[];dz=[]
    for ii,r in enumerate(Tp.itertuples()):
        m=Mp[ii]
        if not m: continue
        e=r.e; bc=list(range(e-12,e)); bt_=np.nanmean(LE[r.fi,bc])
        if np.sum(np.isfinite(LE[r.fi,bc]))<6 or not np.isfinite(bt_): continue
        pj=list(range(e+7,e+13)); v=LE[r.fi,pj]
        if np.sum(np.isfinite(v))<3: continue
        own=float(np.nanmean(v)-bt_)
        dc=[];zc=[]
        for c in m:
            cb=np.nanmean(LE[c,bc]); cv=LE[c,pj]
            if np.isfinite(cb) and np.sum(np.isfinite(cv))>=3:
                dc.append(float(np.nanmean(cv)-cb)); zc.append(1.0 if (np.nanmean(cv)-cb)<=CTH else 0.0)
        if len(dc)<3: continue
        dm.append(own-np.mean(dc)); dz.append((1.0 if own<=CTH else 0.0)-np.mean(zc))
    dm=np.array(dm); dz=np.array(dz)
    def ci(a,B=2000):
        bs=np.array([np.mean(a[RNG.integers(0,len(a),len(a))]) for _ in range(B)])
        return round(float(a.mean()),4),[round(float(np.percentile(bs,2.5)),4),round(float(np.percentile(bs,97.5)),4)]
    pm,pmci=ci(dm); pz,pzci=ci(dz)
    grid_res[f"t-{sh}"]=dict(n=int(len(dm)),mean=pm,mean_ci=pmci,mean_equiv=bool(pmci[0]>=-D_MEAN and pmci[1]<=D_MEAN),
                             tail=pz,tail_ci=pzci,tail_equiv=bool(pzci[0]>=-D_TAIL and pzci[1]<=D_TAIL))
    print(f"(g) t−{sh}: mean {pm}{pmci} equiv={grid_res[f't-{sh}']['mean_equiv']} · tail {pz}{pzci} equiv={grid_res[f't-{sh}']['tail_equiv']}",flush=True)
res=dict(delta_mean=D_MEAN,delta_tail=D_TAIL,c_tail=CTH,
         f_honest=dict(mean=f_mean,tail=f_tail),g_placebo_grid=grid_res,
         event_tail_avg7_12=round(float(np.nanmean([np.nanmean(Cz[:,kx[k]]) for k in range(7,13)])),4))
json.dump(res,open(f"{OUT}/wp11fg.json","w"),ensure_ascii=False,indent=1)
open(f"{OUT}/wp11fg.done","w").write("done")
print("\n=== WP11fg 완료 === 이벤트 tail ATT(avg7-12, c=-0.35):",res["event_tail_avg7_12"])
