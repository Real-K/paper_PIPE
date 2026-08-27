# WP13 재실행 사본 (2026-08-26): 정규화 마스터(382 dated)로 동일 코드 재실행. 원본 wp10f_event_vs_placebo.py · 출력 폴더만 pipe_wp13_2026-08-26 으로 치환.
# -*- coding: utf-8 -*-
"""P-016 WP10f — 실제 이벤트 vs placebo(t−24) 분포 공식 대조 (마지막 결정 검정).
동일 추정기(avg7-12/base12/k50, 상장풀)로 두 d 벡터 재산출·저장 후:
(i) mean diff (궤적 불변 검정: ≈0이면 '평균은 drift') (ii) p10 diff (iii) p25 diff — 각 bootstrap CI.
산출: shared/outputs/pipe_wp13_2026-08-26/wp10f.json + wp10f_dvec.csv
"""
import os,json,csv,re,warnings; warnings.filterwarnings("ignore")
import numpy as np,pandas as pd
import statsmodels.api as sm
BASE=os.environ.get("P016_BASE", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))   # 원 경로는 제거했다 — 실행 시 P016_BASE 로 지정하거나 기본값 사용
RE=f"{BASE}/shared/outputs/pipe_r1_reextract_2026-08-22"
OUT=f"{BASE}/shared/outputs/pipe_wp13_2026-08-26"
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
def dvec(Tm):
    Xt=np.column_stack([Tm.logsize,Tm.logsize**2,Tm.pregrowth,Tm.cap,Tm.man])
    X=np.vstack([Xt,Xc]); y=np.r_[np.ones(len(Xt)),np.zeros(len(Xc))]; Xs=(X-X.mean(0))/X.std(0)
    lgt=sm.Logit(y,sm.add_constant(Xs)).fit(disp=0); xb=np.asarray(lgt.predict(sm.add_constant(Xs),linear=True))
    xbt=xb[:len(Xt)]; xbc=xb[len(Xt):]
    lo,hi=xbt.min(),xbt.max(); supp=(xbc>=lo)&(xbc<=hi); CSr=crows[supp]; xbcs=xbc[supp]; calp=0.2*np.std(xb); K=50
    o=np.argsort(xbcs); XS=xbcs[o]; CS=CSr[o]
    out=np.full(len(Tm),np.nan)
    for ii,r in enumerate(Tm.itertuples()):
        p=np.searchsorted(XS,xbt[ii]); cand=list(range(max(0,p-K-2),min(len(XS),p+K+2)))
        dd=np.abs(XS[cand]-xbt[ii]); sel=np.argsort(dd)[:K]
        m=[CS[cand[s]] for s in sel if dd[s]<=calp]
        if not m: continue
        e=r.e; bc=list(range(e-12,e)); bt_=np.nanmean(LE[r.fi,bc])
        if np.sum(np.isfinite(LE[r.fi,bc]))<6 or not np.isfinite(bt_): continue
        pj=list(range(e+7,e+13)); v=LE[r.fi,pj]
        if np.sum(np.isfinite(v))<3: continue
        dc=[np.nanmean(LE[c,pj])-np.nanmean(LE[c,bc]) for c in m
            if np.isfinite(np.nanmean(LE[c,bc])) and np.sum(np.isfinite(LE[c,pj]))>=3]
        if len(dc)<3: continue
        out[ii]=(np.nanmean(v)-bt_)-np.mean(dc)
    return out
Ta=build(0); Da=dvec(Ta); Tp=build(24); Dp=dvec(Tp)
da=Da[np.isfinite(Da)]; dp=Dp[np.isfinite(Dp)]
pd.DataFrame({"grp":["event"]*len(da)+["placebo"]*len(dp),"d":np.r_[da,dp]}).to_csv(f"{OUT}/wp10f_dvec.csv",index=False)
print(f"event n={len(da)} placebo n={len(dp)}",flush=True)
def diff_boot(fn,B=4000):
    obs=fn(da)-fn(dp)
    bs=np.array([fn(da[RNG.integers(0,len(da),len(da))])-fn(dp[RNG.integers(0,len(dp),len(dp))]) for _ in range(B)])
    return round(float(obs),4),[round(float(np.percentile(bs,2.5)),4),round(float(np.percentile(bs,97.5)),4)]
res={}
res["mean_event"]=round(float(da.mean()),4); res["mean_placebo"]=round(float(dp.mean()),4)
res["diff_mean"],res["diff_mean_ci"]=diff_boot(np.mean)
res["p10_event"]=round(float(np.percentile(da,10)),4); res["p10_placebo"]=round(float(np.percentile(dp,10)),4)
res["diff_p10"],res["diff_p10_ci"]=diff_boot(lambda a:np.percentile(a,10))
res["p25_event"]=round(float(np.percentile(da,25)),4); res["p25_placebo"]=round(float(np.percentile(dp,25)),4)
res["diff_p25"],res["diff_p25_ci"]=diff_boot(lambda a:np.percentile(a,25))
res["median_event"]=round(float(np.median(da)),4); res["median_placebo"]=round(float(np.median(dp)),4)
res["diff_median"],res["diff_median_ci"]=diff_boot(np.median)
json.dump(res,open(f"{OUT}/wp10f.json","w"),ensure_ascii=False,indent=1)
open(f"{OUT}/wp10f.done","w").write("done")
print("=== WP10f 완료 ===")
print(f"mean: 이벤트 {res['mean_event']} vs placebo {res['mean_placebo']} · diff {res['diff_mean']} CI{res['diff_mean_ci']}")
print(f"p10 : 이벤트 {res['p10_event']} vs placebo {res['p10_placebo']} · diff {res['diff_p10']} CI{res['diff_p10_ci']}")
print(f"p25 : 이벤트 {res['p25_event']} vs placebo {res['p25_placebo']} · diff {res['diff_p25']} CI{res['diff_p25_ci']}")
print(f"med : 이벤트 {res['median_event']} vs placebo {res['median_placebo']} · diff {res['diff_median']} CI{res['diff_median_ci']}")
