# WP13 재실행 사본 (2026-08-26): 정규화 마스터(382 dated)로 동일 코드 재실행. 원본 wp8d_trajmatch.py · 출력 폴더만 pipe_wp13_2026-08-26 으로 치환.
# -*- coding: utf-8 -*-
"""P-016 트랙① robustness — 다기간 사전경로 매칭. 단일 pregrowth 대신 6개월·12개월 성장 둘 다 매칭에 넣어
사전경로 shape를 흡수 → pooled ATT+12·사전추세·median 재확인. (pooled 사전추세는 이미 평탄; 강건성 확인용.)
SESOI 동결 0.0559. 산출: shared/outputs/pipe_wp13_2026-08-26/wp8d_trajmatch.json
"""
import os,json,warnings; warnings.filterwarnings("ignore")
import numpy as np,pandas as pd
import statsmodels.api as sm
BASE=os.environ.get("P016_BASE", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))   # 원 경로는 제거했다 — 실행 시 P016_BASE 로 지정하거나 기본값 사용
RE=f"{BASE}/shared/outputs/pipe_r1_reextract_2026-08-22"
OUT=f"{BASE}/shared/outputs/pipe_wp13_2026-08-26"
RNG=np.random.default_rng(20260823)
SESOI=json.load(open(f"{BASE}/papers/P016_pipe-employment/04_design/wp4_pap_committed.json"))["SESOI"]
nps=pd.read_parquet(f"{BASE}/shared/data/processed/nps_monthly_matched_v2.parquet",columns=["bn10","data_ym","가입자수","업종","시도"])
nps["ym"]=pd.PeriodIndex(nps["data_ym"],freq="M"); nps["le"]=np.log1p(nps["가입자수"].astype(float))
months=pd.period_range(nps.ym.min(),nps.ym.max(),freq="M"); mi={m:j for j,m in enumerate(months)}
LE=nps.pivot_table(index="bn10",columns="ym",values="le",aggfunc="mean").reindex(columns=months).to_numpy(float)
idx=list(nps.pivot_table(index="bn10",columns="ym",values="le",aggfunc="mean").index); firm_ix={b:i for i,b in enumerate(idx)}
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
def gh(row,h): d=row[h:]-row[:-h]; return d[np.isfinite(d)]
PRE=3;POST=12;KS=list(range(-12,13));kidx={k:j for j,k in enumerate(KS)}
rec=[]
for r in T.itertuples():
    if r.k not in firm_ix: continue
    fi=firm_ix[r.k]; e=mi.get(r.ev)
    if e is None: continue
    row=LE[fi]; pre=[e-j for j in range(1,PRE+1) if 0<=e-j<len(months)]
    if sum(np.isfinite(row[i]) for i in pre)<3: continue
    if sum(np.isfinite(row[e+j]) for j in range(1,POST+1) if 0<=e+j<len(months))<3: continue
    need=[e-1,e-7,e-13]
    if any(not(0<=x<len(months)) or not np.isfinite(row[x]) for x in need): continue
    base=np.nanmean([row[i] for i in pre])
    rec.append(dict(k=r.k,fi=fi,e=e,logsize=base,pg6=row[e-1]-row[e-7],pg12=row[e-1]-row[e-13],cap=cap(firm_sido.get(r.k,"0")),man=man(firm_ind.get(r.k,"99")),base=base))
Tm=pd.DataFrame(rec); print(f"처치 {len(Tm)}",flush=True)
crows=np.array([i for i,b in enumerate(idx) if (b not in pbbn) and (b not in tb)])
c6=np.array([np.nanmean(gh(LE[r],6)) if gh(LE[r],6).size else np.nan for r in crows])
c12=np.array([np.nanmean(gh(LE[r],12)) if gh(LE[r],12).size else np.nan for r in crows])
cls=firm_med[crows]; ok=np.isfinite(cls)&np.isfinite(c6)&np.isfinite(c12); crows=crows[ok]; cls=cls[ok]; c6=c6[ok]; c12=c12[ok]
ccap=np.array([cap(firm_sido.get(idx[r],"0")) for r in crows]); cman=np.array([man(firm_ind.get(idx[r],"99")) for r in crows])
Xt=np.column_stack([Tm.logsize,Tm.logsize**2,Tm.pg6,Tm.pg12,Tm.cap,Tm.man]); Xc=np.column_stack([cls,cls**2,c6,c12,ccap,cman])
X=np.vstack([Xt,Xc]); y=np.r_[np.ones(len(Xt)),np.zeros(len(Xc))]; Xs=(X-X.mean(0))/X.std(0)
psm=sm.Logit(y,sm.add_constant(Xs)).fit(disp=0); xb=psm.predict(sm.add_constant(Xs),linear=True); xbt=xb[:len(Xt)]; xbc=xb[len(Xt):]
lo,hi=xbt.min(),xbt.max(); supp=(xbc>=lo)&(xbc<=hi); cr=crows[supp]; xbcs=xbc[supp]; calp=0.2*np.std(xb); K=10
o=np.argsort(xbcs); xs=xbcs[o]; cs=cr[o]
def knn(xi):
    pos=np.searchsorted(xs,xi); cand=list(range(max(0,pos-K-2),min(len(xs),pos+K+2))); dd=np.abs(xs[cand]-xi); sel=np.argsort(dd)[:K]
    return [cs[cand[s]] for s in sel if dd[s]<=calp]
matches=[knn(x) for x in xbt]
# post-match balance
def smd(a,b): return (a.mean(0)-b.mean(0))/np.sqrt((a.var(0,ddof=1)+b.var(0,ddof=1))/2)
Xc_all=np.column_stack([cls,cls**2,c6,c12,ccap,cman]); cmap={r:j for j,r in enumerate(crows)}
mc=[c for m in matches for c in m]; Xmc=np.array([Xc_all[cmap[c]] for c in mc])
smd_after=smd(Xmc,Xt)
Cmat=np.full((len(Tm),len(KS)),np.nan)
for ii,r in enumerate(Tm.itertuples()):
    m=matches[ii]
    if not m: continue
    e=r.e; bcols=[e-j for j in range(1,PRE+1) if 0<=e-j<len(months)]; bt=np.nanmean([LE[r.fi,b] for b in bcols])
    for k in KS:
        t=e+k
        if not(0<=t<len(months)) or not np.isfinite(LE[r.fi,t]): continue
        dc=[LE[c,t]-np.nanmean([LE[c,b] for b in bcols]) for c in m]; dc=[x for x in dc if np.isfinite(x)]
        if len(dc)<3: continue
        Cmat[ii,kidx[k]]=(LE[r.fi,t]-bt)-np.mean(dc)
valid=np.array([i for i in range(len(Tm)) if matches[i] and np.isfinite(Cmat[i,kidx[12]])])
def tau_of(rows): return np.array([np.nanmean(Cmat[rows,j]) for j in range(len(KS))])
tau=tau_of(valid); B=300; boot=np.array([tau_of(valid[RNG.integers(0,len(valid),len(valid))]) for _ in range(B)])
loci=np.nanpercentile(boot,2.5,0); hici=np.nanpercentile(boot,97.5,0)
npass=sum(1 for k in range(-12,0) if (loci[kidx[k]]>=-SESOI and hici[kidx[k]]<=SESOI))
di12=Cmat[valid,kidx[12]]
res=dict(id="P016-WP8d-trajmatch",n=int(len(valid)),covs=["logsize","logsize2","pg6","pg12","cap","man"],
         max_abs_smd_after=round(float(np.abs(smd_after).max()),4),
         ATT_plus12=dict(point=round(float(tau[kidx[12]]),4),ci95=[round(float(loci[kidx[12]]),4),round(float(hici[kidx[12]]),4)]),
         median_di12=round(float(np.median(di12)),4),pct_neg=round(float(np.mean(di12<0)),3),
         pretrend_equiv=f"{npass}/12",
         event_study=[dict(k=k,tau=round(float(tau[kidx[k]]),4),lo=round(float(loci[kidx[k]]),4),hi=round(float(hici[kidx[k]]),4)) for k in KS])
json.dump(res,open(f"{OUT}/wp8d_trajmatch.json","w"),ensure_ascii=False,indent=1)
open(f"{OUT}/trajmatch.done","w").write("done")
print("=== 사전경로매칭 완료 ===")
print(f"n={len(valid)} balance max|SMD|={np.abs(smd_after).max():.3f} ATT+12={tau[kidx[12]]:.4f}[{loci[kidx[12]]:.4f},{hici[kidx[12]]:.4f}] median={np.median(di12):.4f} 음비율={np.mean(di12<0):.3f} 사전추세등가={npass}/12")
