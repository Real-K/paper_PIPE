# -*- coding: utf-8 -*-
"""WP11d — G7/G10/§16. (i) collapse-probability 곡선 ATT_c, c∈[−0.60,−0.10] + uniform band (event & placebo & DDD)
(ii) 결합 multiplicity: (Δmean,Δp10,Δp25,Δp50) max-|t| (iii) outcome 스케일 audit + 소기업 산술 점검.
상장풀(wp10c 방식) 사용. 산출: shared/outputs/pipe_wp11_2026-08-23/wp11d.json
"""
import os,json,csv,re,warnings; warnings.filterwarnings("ignore")
import numpy as np,pandas as pd
import statsmodels.api as sm
BASE=os.environ.get("P016_BASE", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))   # 원 경로는 제거했다 — 실행 시 P016_BASE 로 지정하거나 기본값 사용
RE=f"{BASE}/shared/outputs/pipe_r1_reextract_2026-08-22"
OUT=f"{BASE}/shared/outputs/pipe_wp11_2026-08-23"; os.makedirs(OUT,exist_ok=True)
RNG=np.random.default_rng(20260823)
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
idx=list(piv.index); firm_ix={b:i for i,b in enumerate(idx)}; LE=piv.to_numpy(float)
EMP=nps.pivot_table(index="bn10",columns="ym",values="가입자수",aggfunc="mean").reindex(columns=months).reindex(index=idx).to_numpy(float)
firm_ind=nps.groupby("bn10")["업종"].agg(lambda s:str(s.iloc[0])[:2]); firm_sido=nps.groupby("bn10")["시도"].agg(lambda s:str(s.iloc[0]))
firm_med=np.nanmedian(np.where(np.isfinite(LE),LE,np.nan),axis=1)
pb=pd.read_csv(f"{BASE}/shared/data/processed/pitchbook_all_status_v1.csv",dtype=str)
pbbn=set(pb["bn"].astype(str).str.replace(r'\D','',regex=True).str.zfill(10).dropna())
T=pd.read_csv(f"{RE}/treatment_master_v2.csv",dtype=str); T["k"]=T["k"].str.replace(r'\D','',regex=True).str.zfill(10)
T["ev"]=pd.to_datetime(T["event_dt"],errors="coerce").dt.to_period("M"); T=T.dropna(subset=["ev"]).drop_duplicates("k"); tb=set(T.k)
def cap(s): return 1.0 if str(s) in ("11","41","28") else 0.0
def man(i):
    try: return 1.0 if 10<=int(i)<=34 else 0.0
    except: return 0.0
def g12(r): d=r[12:]-r[:-12]; return d[np.isfinite(d)]
ctrl=[b for b in idx if (b in listed) and (b not in pbbn) and (b not in tb)]
crows=np.array([firm_ix[b] for b in ctrl])
cpg=np.array([np.nanmean(g12(LE[r])) if g12(LE[r]).size else np.nan for r in crows]); cls=firm_med[crows]
okc=np.isfinite(cls)&np.isfinite(cpg); crows=crows[okc]; cls=cls[okc]; cpg=cpg[okc]
ccap=np.array([cap(firm_sido.get(idx[r],"0")) for r in crows]); cman=np.array([man(firm_ind.get(idx[r],"99")) for r in crows])
Xc=np.column_stack([cls,cls**2,cpg,ccap,cman])
def build(shift):
    rec=[]
    for r in T.itertuples():
        if r.k not in firm_ix: continue
        fi=firm_ix[r.k]; e0=mi.get(r.ev)
        if e0 is None: continue
        e=e0-shift
        if e-13<0 or e+12>=NM: continue
        row=LE[fi]
        if not(np.isfinite(row[e-1]) and np.isfinite(row[e-13])): continue
        if sum(np.isfinite(row[e-j]) for j in range(1,4))<3: continue
        if sum(np.isfinite(row[e+j]) for j in range(1,13))<3: continue
        rec.append(dict(k=r.k,fi=fi,e=e,logsize=np.nanmean([row[e-j] for j in range(1,4)]),pregrowth=row[e-1]-row[e-13],cap=cap(firm_sido.get(r.k,"0")),man=man(firm_ind.get(r.k,"99"))))
    return pd.DataFrame(rec)
def structures(Tm):
    """treated별 own Δ(log, avg7-12 - base12), 대조 Δ 리스트, baseline emp, own abs job change 반환"""
    Xt=np.column_stack([Tm.logsize,Tm.logsize**2,Tm.pregrowth,Tm.cap,Tm.man])
    X=np.vstack([Xt,Xc]); y=np.r_[np.ones(len(Xt)),np.zeros(len(Xc))]; Xs=(X-X.mean(0))/X.std(0)
    lgt=sm.Logit(y,sm.add_constant(Xs)).fit(disp=0); xb=np.asarray(lgt.predict(sm.add_constant(Xs),linear=True))
    xbt=xb[:len(Xt)]; xbc=xb[len(Xt):]
    lo,hi=xbt.min(),xbt.max(); supp=(xbc>=lo)&(xbc<=hi); CSr=crows[supp]; xbcs=xbc[supp]; calp=0.2*np.std(xb); K=50
    o=np.argsort(xbcs); XS=xbcs[o]; CS=CSr[o]
    outs=[]
    for ii,r in enumerate(Tm.itertuples()):
        p=np.searchsorted(XS,xbt[ii]); cand=list(range(max(0,p-K-2),min(len(XS),p+K+2)))
        dd=np.abs(XS[cand]-xbt[ii]); sel=np.argsort(dd)[:K]
        m=[CS[cand[s]] for s in sel if dd[s]<=calp]
        if not m: continue
        e=r.e; bc=list(range(e-12,e)); bt_=np.nanmean(LE[r.fi,bc])
        if np.sum(np.isfinite(LE[r.fi,bc]))<6 or not np.isfinite(bt_): continue
        pj=list(range(e+7,e+13)); v=LE[r.fi,pj]
        if np.sum(np.isfinite(v))<3: continue
        ownD=float(np.nanmean(v)-bt_)
        base_emp=np.nanmean(EMP[r.fi,bc]); post_emp=np.nanmean(EMP[r.fi,pj])
        ctD=[]
        for c in m:
            cb=np.nanmean(LE[c,bc]); cv=LE[c,pj]
            if np.isfinite(cb) and np.sum(np.isfinite(cv))>=3: ctD.append(float(np.nanmean(cv)-cb))
        if len(ctD)<3: continue
        outs.append(dict(ownD=ownD,ctD=ctD,base_emp=float(base_emp) if np.isfinite(base_emp) else np.nan,
                         abs_job=float(post_emp-base_emp) if np.isfinite(post_emp) and np.isfinite(base_emp) else np.nan))
    return outs
Sa=structures(build(0)); Sp=structures(build(24))
print(f"event {len(Sa)} · placebo {len(Sp)}",flush=True)
GRID=np.round(np.arange(-0.60,-0.0999,0.05),2)
def att_c(S,c): return float(np.mean([ (1.0 if s["ownD"]<=c else 0.0) - np.mean([1.0 if x<=c else 0.0 for x in s["ctD"]]) for s in S]))
def curve(S): return np.array([att_c(S,c) for c in GRID])
cv_a=curve(Sa); cv_p=curve(Sp); cv_ddd=cv_a-cv_p
B=1200
bca=np.zeros((B,len(GRID))); bcp=np.zeros((B,len(GRID)))
for b in range(B):
    ia=[Sa[j] for j in RNG.integers(0,len(Sa),len(Sa))]; ip=[Sp[j] for j in RNG.integers(0,len(Sp),len(Sp))]
    bca[b]=curve(ia); bcp[b]=curve(ip)
def bands(cv,bc):
    se=bc.std(0,ddof=1); se[se==0]=1e-9
    tmax=np.percentile(np.abs((bc-bc.mean(0))/se).max(1),95)   # sup-t
    return dict(point=[round(float(x),4) for x in cv],
                lo_pw=[round(float(x),4) for x in np.percentile(bc,2.5,0)],hi_pw=[round(float(x),4) for x in np.percentile(bc,97.5,0)],
                lo_unif=[round(float(cv[j]-tmax*se[j]),4) for j in range(len(cv))],hi_unif=[round(float(cv[j]+tmax*se[j]),4) for j in range(len(cv))])
res=dict(grid=[float(c) for c in GRID],event=bands(cv_a,bca),placebo=bands(cv_p,bcp),
         ddd=bands(cv_ddd,bca-bcp))
sig_unif=[float(GRID[j]) for j in range(len(GRID)) if res["ddd"]["lo_unif"][j]>0]  # collapse-prob ATT는 양(+)이 초과붕괴
res["ddd_sig_region_uniform"]=sig_unif
print("DDD uniform-유의 c 영역:",sig_unif,flush=True)
# (ii) 결합 multiplicity (event vs placebo)
da=np.array([s["ownD"]-np.mean(s["ctD"]) for s in Sa]); dp=np.array([s["ownD"]-np.mean(s["ctD"]) for s in Sp])
def stat_vec(a,p):
    return np.array([a.mean()-p.mean(),np.percentile(a,10)-np.percentile(p,10),
                     np.percentile(a,25)-np.percentile(p,25),np.median(a)-np.median(p)])
obs=stat_vec(da,dp); bs=np.zeros((2000,4))
for b in range(2000):
    bs[b]=stat_vec(da[RNG.integers(0,len(da),len(da))],dp[RNG.integers(0,len(dp),len(dp))])
se=bs.std(0,ddof=1); tobs=np.abs(obs)/se
tnull=np.abs((bs-bs.mean(0))/se)
pmax=[round(float(np.mean(tnull.max(1)>=tobs[j])),4) for j in range(4)]
res["joint_multiplicity"]=dict(stats=["mean","p10","p25","median"],obs=[round(float(x),4) for x in obs],
                               maxT_adjusted_p=pmax)
print("결합 max-|t| 조정 p:",dict(zip(["mean","p10","p25","median"],pmax)),flush=True)
# (iii) outcome 스케일 audit (event 표본)
absj=np.array([s["abs_job"] for s in Sa if np.isfinite(s["abs_job"])])
w=np.array([s["base_emp"] for s in Sa if np.isfinite(s["base_emp"])])
dw=np.array([s["ownD"]-np.mean(s["ctD"]) for s in Sa if np.isfinite(s["base_emp"])])
res["outcome_audit"]=dict(abs_job_mean=round(float(absj.mean()),1),abs_job_p10=round(float(np.percentile(absj,10)),1),
    emp_weighted_ATT=round(float(np.average(dw,weights=w)),4),
    firm_weighted_ATT=round(float(da.mean()),4))
# 소기업 산술: 꼬리(하위 사분위 d) 발생률을 baseline 규모 3분위별로
bq=np.quantile([s["base_emp"] for s in Sa if np.isfinite(s["base_emp"])],[1/3,2/3])
tail_cut=np.percentile(da,25)
by={}
for lab,cond in [("small",lambda be:be<=bq[0]),("mid",lambda be:bq[0]<be<=bq[1]),("large",lambda be:be>bq[1])]:
    sel=[(s["ownD"]-np.mean(s["ctD"]))<=tail_cut for s in Sa if np.isfinite(s["base_emp"]) and cond(s["base_emp"])]
    by[lab]=dict(n=len(sel),tail_rate=round(float(np.mean(sel)),3) if sel else None)
res["smallfirm_check"]=by
print("규모별 꼬리율:",by,flush=True)
json.dump(res,open(f"{OUT}/wp11d.json","w"),ensure_ascii=False,indent=1)
open(f"{OUT}/wp11d.done","w").write("done")
print("\n=== WP11d 완료 ===")
