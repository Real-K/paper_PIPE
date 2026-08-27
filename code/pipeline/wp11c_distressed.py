# -*- coding: utf-8 -*-
"""WP11c — G2/G9 결정 비교 (§20): PIPE-distressed vs non-PIPE-distressed의 꼬리 break.
distressed 비수령 = 청정 상장대조 ∧ (직전FY 손실 or lev>2 or 자본잠식) ∧ 고용 하락(le(e-1)<le(e-13)) ∧ e-1 생존.
비교: 같은 이벤트월 risk set에서 treated ownΔ 분포 vs distressed-비수령 ownΔ 분포 (propensity 가중으로 규모·사전성장·연도 정렬).
산출: collapse-prob 곡선 差 + mean/p10 差 + bootstrap. Pass=treated 초과. Fail=동일 → 'financing identifies fragile phase'(그 자체로 fact).
shared/outputs/pipe_wp11_2026-08-23/wp11c.json
"""
import os,json,warnings; warnings.filterwarnings("ignore")
import numpy as np,pandas as pd
import statsmodels.api as sm
BASE=os.environ.get("P016_BASE", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))   # 원 경로는 제거했다 — 실행 시 P016_BASE 로 지정하거나 기본값 사용
RE=f"{BASE}/shared/outputs/pipe_r1_reextract_2026-08-22"
OUT=f"{BASE}/shared/outputs/pipe_wp11_2026-08-23"
RNG=np.random.default_rng(20260823)
CL=pd.read_csv(f"{OUT}/controls_clean.csv",dtype={"bn":str}); clean=set(CL[CL.third_hist==False].bn)
FIN=pd.read_csv(f"{OUT}/fin_distress_panel.csv",dtype={"bn":str})
fin={(r.bn,int(r.year)):(r.lev,r.roa,r.cash,int(r.impaired),int(r.loss)) for r in FIN.itertuples()}
def fin_asof(bn,yr):
    for y in (yr-1,yr-2):
        v=fin.get((bn,y))
        if v: return v
    return None
nps=pd.read_parquet(f"{BASE}/shared/data/processed/nps_monthly_matched_v2.parquet",columns=["bn10","data_ym","가입자수"])
nps["ym"]=pd.PeriodIndex(nps["data_ym"],freq="M"); nps["le"]=np.log1p(nps["가입자수"].astype(float))
months=pd.period_range(nps.ym.min(),nps.ym.max(),freq="M"); mi={m:j for j,m in enumerate(months)}; NM=len(months)
piv=nps.pivot_table(index="bn10",columns="ym",values="le",aggfunc="mean").reindex(columns=months)
idx=list(piv.index); fx={b:i for i,b in enumerate(idx)}; LE=piv.to_numpy(float)
T=pd.read_csv(f"{RE}/treatment_master_v2.csv",dtype=str); T["k"]=T["k"].str.replace(r'\D','',regex=True).str.zfill(10)
T["ev"]=pd.to_datetime(T["event_dt"],errors="coerce").dt.to_period("M"); T=T.dropna(subset=["ev"]).drop_duplicates("k")
def ownD(b,e):
    if b not in fx: return None,None,None
    row=LE[fx[b]]
    if e-13<0 or e+12>=NM: return None,None,None
    if not(np.isfinite(row[e-1]) and np.isfinite(row[e-13])): return None,None,None
    bc=row[e-12:e]
    if np.sum(np.isfinite(bc))<6: return None,None,None
    bt=np.nanmean(bc); v=row[e+7:e+13]
    if np.sum(np.isfinite(v))<3: return None,None,None
    return float(np.nanmean(v)-bt),float(bt),float(row[e-1]-row[e-13])
# treated 표본
trt=[]
for r in T.itertuples():
    d,ls,pg=ownD(r.k,mi.get(r.ev,-999))
    if d is None: continue
    fv=fin_asof(r.k,r.ev.year)
    trt.append(dict(bn=r.k,e=mi[r.ev],D=d,logsize=ls,pg=pg,yr=r.ev.year,
                    distress=1 if (fv and (fv[4]==1 or (fv[0]==fv[0] and fv[0]>2) or fv[3]==1)) else 0))
TR=pd.DataFrame(trt); print(f"treated usable {len(TR)} (재무distress 플래그 {int(TR.distress.sum())})",flush=True)
# distressed 비수령 risk set: 각 treated 이벤트월에서 청정대조 중 distress+고용하락
evset=sorted(set(TR.e))
drs=[]
for e in evset:
    yr=months[e].year
    for b in clean:
        if b not in fx: continue
        row=LE[fx[b]]
        if e-13<0 or e+12>=NM or not(np.isfinite(row[e-1]) and np.isfinite(row[e-13])): continue
        if row[e-1]>=row[e-13]: continue           # 고용 하락 조건
        fv=fin_asof(b,yr)
        if not fv: continue
        lev,roa,cash,imp,loss=fv
        if not(loss==1 or (lev==lev and lev>2) or imp==1): continue
        d,ls,pg=ownD(b,e)
        if d is None: continue
        drs.append(dict(bn=b,e=e,D=d,logsize=ls,pg=pg,yr=yr))
DR=pd.DataFrame(drs).drop_duplicates(["bn","e"])
print(f"distressed 비수령 firm-event {len(DR)} (고유기업 {DR.bn.nunique()})",flush=True)
# propensity 가중 (treated=1 vs distressed pool): logsize·pg·연도
X=np.vstack([np.column_stack([TR.logsize,TR.pg,TR.yr-2015]),np.column_stack([DR.logsize,DR.pg,DR.yr-2015])])
y=np.r_[np.ones(len(TR)),np.zeros(len(DR))]; Xs=(X-X.mean(0))/X.std(0)
lg=sm.Logit(y,sm.add_constant(Xs)).fit(disp=0); ps=np.asarray(lg.predict(sm.add_constant(Xs)))
w_dr=ps[len(TR):]/(1-ps[len(TR):]); w_dr=np.clip(w_dr,0,np.percentile(w_dr,99)); w_dr=w_dr/w_dr.sum()
da=TR.D.values; db=DR.D.values
GRID=np.round(np.arange(-0.60,-0.0999,0.05),2)
def cprob(d,w=None,c=0.0):
    z=(d<=c).astype(float)
    return float(np.average(z,weights=w))
def curve_diff(da,db,w):
    return np.array([cprob(da,None,c)-cprob(db,w,c) for c in GRID])
cd=curve_diff(da,db,w_dr)
B=1500; bc=np.zeros((B,len(GRID)))
for b in range(B):
    ia=RNG.integers(0,len(da),len(da)); ib=RNG.integers(0,len(db),len(db))
    wb=w_dr[ib]; wb=wb/wb.sum()
    bc[b]=curve_diff(da[ia],db[ib],wb)
se=bc.std(0,ddof=1); se[se==0]=1e-9
tmax=np.percentile(np.abs((bc-bc.mean(0))/se).max(1),95)
lo_u=[round(float(cd[j]-tmax*se[j]),4) for j in range(len(GRID))]
hi_u=[round(float(cd[j]+tmax*se[j]),4) for j in range(len(GRID))]
sig=[float(GRID[j]) for j in range(len(GRID)) if lo_u[j]>0]
# mean/p10 差
def bdiff(fn,B=3000):
    obs=fn(da)-fn(db)
    bs=np.array([fn(da[RNG.integers(0,len(da),len(da))])-fn(db[RNG.integers(0,len(db),len(db))]) for _ in range(B)])
    return round(float(obs),4),[round(float(np.percentile(bs,2.5)),4),round(float(np.percentile(bs,97.5)),4)]
m_,mci_=bdiff(np.mean); p10_,p10ci=bdiff(lambda x:np.percentile(x,10)); md_,mdci=bdiff(np.median)
res=dict(n_treated=int(len(TR)),n_distressed_ne=int(len(DR)),n_distressed_firms=int(DR.bn.nunique()),
         grid=[float(c) for c in GRID],collapse_diff=[round(float(x),4) for x in cd],lo_unif=lo_u,hi_unif=hi_u,
         sig_region=sig,mean_diff=dict(obs=m_,ci=mci_),p10_diff=dict(obs=p10_,ci=p10ci),median_diff=dict(obs=md_,ci=mdci),
         note="가중=propensity odds(logsize·pregrowth·연도). Pass=sig_region 비어있지 않음(treated 초과붕괴). Fail=event-marker 해석.")
json.dump(res,open(f"{OUT}/wp11c.json","w"),ensure_ascii=False,indent=1)
open(f"{OUT}/wp11c.done","w").write("done")
print(f"=== WP11c 완료 === mean diff {m_}{mci_} · p10 diff {p10_}{p10ci} · median {md_}{mdci}")
print("collapse-prob 差 uniform 유의영역:",sig)
for j,c in enumerate(GRID): print(f"  c={c:+.2f}: diff {cd[j]:+.4f} unif[{lo_u[j]:+.4f},{hi_u[j]:+.4f}]")
