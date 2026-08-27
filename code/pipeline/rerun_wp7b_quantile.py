# WP13 재실행 사본 (2026-08-26): 정규화 마스터(382 dated)로 동일 코드 재실행. 원본 wp7b_quantile.py · 출력 폴더만 pipe_wp13_2026-08-26 으로 치환.
# -*- coding: utf-8 -*-
"""P-016 WP7b — 순위-평균 긴장 규명. 헤드라인 PSM 매칭의 +12 pair difference d_i 분포:
평균·중앙값·10%절사평균·윈저화평균 + 각 bootstrap CI, 분위(p10..p90), %음(-), 왜도.
Γ*≈1.0이 왜도(소수 큰감소) 때문인지, 아니면 중앙값도 음인지 판별 → claim 강도 확정.
산출: shared/outputs/pipe_wp13_2026-08-26/wp7b_quantile.json
"""
import os,json,warnings; warnings.filterwarnings("ignore")
import numpy as np,pandas as pd
import statsmodels.api as sm
from scipy import stats
BASE=os.environ.get("P016_BASE", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))   # 원 경로는 제거했다 — 실행 시 P016_BASE 로 지정하거나 기본값 사용
RE=f"{BASE}/shared/outputs/pipe_r1_reextract_2026-08-22"
OUT=f"{BASE}/shared/outputs/pipe_wp13_2026-08-26"; os.makedirs(OUT,exist_ok=True)
RNG=np.random.default_rng(20260823)
nps=pd.read_parquet(f"{BASE}/shared/data/processed/nps_monthly_matched_v2.parquet",columns=["bn10","data_ym","가입자수","업종","시도"])
nps["ym"]=pd.PeriodIndex(nps["data_ym"],freq="M"); nps["le"]=np.log1p(nps["가입자수"].astype(float))
months=pd.period_range(nps.ym.min(),nps.ym.max(),freq="M"); mi={m:j for j,m in enumerate(months)}
LE=nps.pivot_table(index="bn10",columns="ym",values="le",aggfunc="mean").reindex(columns=months).to_numpy(float)
idx=list(nps.pivot_table(index="bn10",columns="ym",values="le",aggfunc="mean").index); firm_ix={b:i for i,b in enumerate(idx)}
firm_ind=nps.groupby("bn10")["업종"].agg(lambda s:str(s.iloc[0])[:2]); firm_sido=nps.groupby("bn10")["시도"].agg(lambda s:str(s.iloc[0]))
firm_med_le=np.nanmedian(np.where(np.isfinite(LE),LE,np.nan),axis=1)
pb=pd.read_csv(f"{BASE}/shared/data/processed/pitchbook_all_status_v1.csv",dtype=str)
pbbn=set(pb["bn"].astype(str).str.replace(r'\D','',regex=True).str.zfill(10).dropna())
T=pd.read_csv(f"{RE}/treatment_master_v2.csv",dtype=str); T["k"]=T["k"].str.replace(r'\D','',regex=True).str.zfill(10)
T=T[pd.to_numeric(T.event_dt.astype(str).str[:4],errors="coerce").between(2015,2025)]   # 표본기간 2015–2025(원고 명시). 날짜 정규화로 유입된 2010–2014·2026 이벤트 제외 — WP13, 2026-08-27
T["ev"]=pd.to_datetime(T["event_dt"],errors="coerce").dt.to_period("M"); T=T.dropna(subset=["ev"]).drop_duplicates("k"); treated_bn=set(T.k)
T=T[T.k.isin({l.strip() for l in open(f"{BASE}/shared/outputs/pipe_wp13_2026-08-26/emp_primary_k.txt") if l.strip()})]  # WP13: 고정 1차표본(210)
def capital(s): return 1.0 if str(s) in ("11","41","28") else 0.0
def manuf(i):
    try: return 1.0 if 10<=int(i)<=34 else 0.0
    except: return 0.0
def g12(row): d=row[12:]-row[:-12]; return d[np.isfinite(d)]
PRE=3;POST=12;PREW=13
rec=[]
for r in T.itertuples():
    if r.k not in firm_ix: continue
    fi=firm_ix[r.k]; e=mi.get(r.ev)
    if e is None: continue
    row=LE[fi]; pre_idx=[e-j for j in range(1,PRE+1) if 0<=e-j<len(months)]
    npre=sum(np.isfinite(row[i]) for i in pre_idx); npost=sum(np.isfinite(row[e+j]) for j in range(1,POST+1) if 0<=e+j<len(months))
    if npre<3 or npost<3: continue
    if not(0<=e-1<len(months) and 0<=e-PREW<len(months) and np.isfinite(row[e-1]) and np.isfinite(row[e-PREW])): continue
    base=np.nanmean([row[i] for i in pre_idx]); pg=row[e-1]-row[e-PREW]
    rec.append(dict(k=r.k,fi=fi,e=e,logsize=base,base=base,pregrowth=pg,cap=capital(firm_sido.get(r.k,"0")),man=manuf(firm_ind.get(r.k,"99"))))
Tm=pd.DataFrame(rec)
crows=np.array([i for i,b in enumerate(idx) if (b not in pbbn) and (b not in treated_bn)])
cpg=np.array([np.nanmean(g12(LE[r])) if g12(LE[r]).size else np.nan for r in crows]); cls=firm_med_le[crows]
ok=np.isfinite(cls)&np.isfinite(cpg); crows=crows[ok]; cls=cls[ok]; cpg=cpg[ok]
ccap=np.array([capital(firm_sido.get(idx[r],"0")) for r in crows]); cman=np.array([manuf(firm_ind.get(idx[r],"99")) for r in crows])
Xt=np.column_stack([Tm.logsize,Tm.logsize**2,Tm.pregrowth,Tm.cap,Tm.man]); Xc=np.column_stack([cls,cls**2,cpg,ccap,cman])
X=np.vstack([Xt,Xc]); y=np.r_[np.ones(len(Xt)),np.zeros(len(Xc))]; Xs=(X-X.mean(0))/X.std(0)
psm=sm.Logit(y,sm.add_constant(Xs)).fit(disp=0); xb=psm.predict(sm.add_constant(Xs),linear=True); xbt=xb[:len(Xt)]; xbc=xb[len(Xt):]
lo,hi=xbt.min(),xbt.max(); supp=(xbc>=lo)&(xbc<=hi); cr=crows[supp]; xbcs=xbc[supp]; cal=0.2*np.std(xb); K=10
o=np.argsort(xbcs); xs=xbcs[o]; cs=cr[o]
def knn(xi):
    pos=np.searchsorted(xs,xi); cand=list(range(max(0,pos-K-2),min(len(xs),pos+K+2))); d=np.abs(xs[cand]-xi); sel=np.argsort(d)[:K]
    return [cs[cand[s]] for s in sel if d[s]<=cal]
matches=[knn(x) for x in xbt]
# +12 pair difference d_i
d=[]
for ii,r in enumerate(Tm.itertuples()):
    m=matches[ii]
    if not m: continue
    e=r.e; t=e+12
    if not(0<=t<len(months)) or not np.isfinite(LE[r.fi,t]): continue
    bcols=[e-j for j in range(1,PRE+1) if 0<=e-j<len(months)]; Dt=LE[r.fi,t]-np.nanmean([LE[r.fi,b] for b in bcols])
    dc=[]
    for c in m:
        cb=np.nanmean([LE[c,b] for b in bcols]); yc=LE[c,t]
        if np.isfinite(cb) and np.isfinite(yc): dc.append(yc-cb)
    if len(dc)<3: continue
    d.append(Dt-np.mean(dc))
d=np.array(d); n=len(d)
def tmean(a,p=0.10): return float(stats.trim_mean(a,p))
def wins(a,p=0.05):
    loq,hiq=np.percentile(a,[p*100,(1-p)*100]); return float(np.mean(np.clip(a,loq,hiq)))
def bci(fn,B=2000):
    bs=np.array([fn(d[RNG.integers(0,n,n)]) for _ in range(B)]); return [round(float(np.percentile(bs,2.5)),4),round(float(np.percentile(bs,97.5)),4)]
mean_=float(np.mean(d)); med_=float(np.median(d)); tm_=tmean(d); wn_=wins(d)
res=dict(id="P016-WP7b",n=n,
         mean=dict(point=round(mean_,4),ci95=bci(np.mean)),
         median=dict(point=round(med_,4),ci95=bci(np.median)),
         trimmed10=dict(point=round(tm_,4),ci95=bci(lambda a:stats.trim_mean(a,0.10))),
         winsor5=dict(point=round(wn_,4),ci95=bci(lambda a:wins(a,0.05))),
         pct_negative=round(float(np.mean(d<0)),3),
         quantiles={f"p{q}":round(float(np.percentile(d,q)),4) for q in (10,25,50,75,90)},
         skew=round(float(stats.skew(d)),3),
         interpretation="median CI가 0 배제하면 순위-평균 긴장은 왜도 아님(효과 실재). median≈0이면 소수 firm 견인.")
json.dump(res,open(f"{OUT}/wp7b_quantile.json","w"),ensure_ascii=False,indent=1)
open(f"{OUT}/wp7b.done","w").write("done")
print("=== WP7b 완료 ===")
print(f"n={n} mean={mean_:.4f}{res['mean']['ci95']} median={med_:.4f}{res['median']['ci95']} trim10={tm_:.4f}{res['trimmed10']['ci95']} winsor5={wn_:.4f}{res['winsor5']['ci95']}")
print(f"%음={res['pct_negative']} 왜도={res['skew']} 분위={res['quantiles']}")
