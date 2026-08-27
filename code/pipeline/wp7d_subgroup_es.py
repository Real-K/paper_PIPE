# -*- coding: utf-8 -*-
"""P-016 WP7d — moderator(사전 고용궤적) 식별 방어. 저성장/고성장 subgroup별 event-study τ_k(-12..+12) + 사전추세 등가(rule11).
핵심 질문: 저성장 subgroup의 −14% 고용감소가 **평탄한 사전추세 뒤에** 오는가(=깨끗한 처치효과) 아니면
사전부터 차등추세인가(=momentum/mean-reversion 오염). 각 subgroup에서 k=-12..-1의 CI⊂±SESOI 판정.
SESOI 동결 0.0559. 산출: shared/outputs/pipe_wp7d_2026-08-23/wp7d_subgroup_es.json
"""
import os,json,warnings; warnings.filterwarnings("ignore")
import numpy as np,pandas as pd
import statsmodels.api as sm
BASE=os.environ.get("P016_BASE", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))   # 원 경로는 제거했다 — 실행 시 P016_BASE 로 지정하거나 기본값 사용
RE=f"{BASE}/shared/outputs/pipe_r1_reextract_2026-08-22"
OUT=f"{BASE}/shared/outputs/pipe_wp7d_2026-08-23"; os.makedirs(OUT,exist_ok=True)
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
T["ev"]=pd.to_datetime(T["event_dt"],errors="coerce").dt.to_period("M"); T=T.dropna(subset=["ev"]).drop_duplicates("k"); tb=set(T.k)
def cap(s): return 1.0 if str(s) in ("11","41","28") else 0.0
def man(i):
    try: return 1.0 if 10<=int(i)<=34 else 0.0
    except: return 0.0
def g12(r): d=r[12:]-r[:-12]; return d[np.isfinite(d)]
PRE=3;POST=12;PREW=13;KS=list(range(-12,13));kidx={k:j for j,k in enumerate(KS)}
rec=[]
for r in T.itertuples():
    if r.k not in firm_ix: continue
    fi=firm_ix[r.k]; e=mi.get(r.ev)
    if e is None: continue
    row=LE[fi]; pre=[e-j for j in range(1,PRE+1) if 0<=e-j<len(months)]
    if sum(np.isfinite(row[i]) for i in pre)<3: continue
    if sum(np.isfinite(row[e+j]) for j in range(1,POST+1) if 0<=e+j<len(months))<3: continue
    if not(0<=e-1<len(months) and 0<=e-PREW<len(months) and np.isfinite(row[e-1]) and np.isfinite(row[e-PREW])): continue
    rec.append(dict(k=r.k,fi=fi,e=e,logsize=np.nanmean([row[i] for i in pre]),pregrowth=row[e-1]-row[e-PREW],cap=cap(firm_sido.get(r.k,"0")),man=man(firm_ind.get(r.k,"99"))))
Tm=pd.DataFrame(rec)
crows=np.array([i for i,b in enumerate(idx) if (b not in pbbn) and (b not in tb)])
cpg=np.array([np.nanmean(g12(LE[r])) if g12(LE[r]).size else np.nan for r in crows]); cls=firm_med[crows]
ok=np.isfinite(cls)&np.isfinite(cpg); crows=crows[ok]; cls=cls[ok]; cpg=cpg[ok]
ccap=np.array([cap(firm_sido.get(idx[r],"0")) for r in crows]); cman=np.array([man(firm_ind.get(idx[r],"99")) for r in crows])
Xt=np.column_stack([Tm.logsize,Tm.logsize**2,Tm.pregrowth,Tm.cap,Tm.man]); Xc=np.column_stack([cls,cls**2,cpg,ccap,cman])
X=np.vstack([Xt,Xc]); y=np.r_[np.ones(len(Xt)),np.zeros(len(Xc))]; Xs=(X-X.mean(0))/X.std(0)
psm=sm.Logit(y,sm.add_constant(Xs)).fit(disp=0); xb=psm.predict(sm.add_constant(Xs),linear=True); xbt=xb[:len(Xt)]; xbc=xb[len(Xt):]
lo,hi=xbt.min(),xbt.max(); supp=(xbc>=lo)&(xbc<=hi); cr=crows[supp]; xbcs=xbc[supp]; calp=0.2*np.std(xb); K=10
o=np.argsort(xbcs); xs=xbcs[o]; cs=cr[o]
def knn(xi):
    pos=np.searchsorted(xs,xi); cand=list(range(max(0,pos-K-2),min(len(xs),pos+K+2))); dd=np.abs(xs[cand]-xi); sel=np.argsort(dd)[:K]
    return [cs[cand[s]] for s in sel if dd[s]<=calp]
matches=[knn(x) for x in xbt]
# 전체 event-study contribution matrix
Cmat=np.full((len(Tm),len(KS)),np.nan)
for ii,r in enumerate(Tm.itertuples()):
    m=matches[ii]
    if not m: continue
    e=r.e; bcols=[e-j for j in range(1,PRE+1) if 0<=e-j<len(months)]; base_t=np.nanmean([LE[r.fi,b] for b in bcols])
    for k in KS:
        t=e+k
        if not(0<=t<len(months)) or not np.isfinite(LE[r.fi,t]): continue
        Dt=LE[r.fi,t]-base_t
        dc=[LE[c,t]-np.nanmean([LE[c,b] for b in bcols]) for c in m]
        dc=[x for x in dc if np.isfinite(x)]
        if len(dc)<3: continue
        Cmat[ii,kidx[k]]=Dt-np.mean(dc)
med=Tm.pregrowth.median()
groups={"저성장(<median)":(Tm.pregrowth<med).values,"고성장(>=median)":(Tm.pregrowth>=med).values}
def es_for(mask):
    rows=np.where(mask)[0]
    def tau_of(rr): return np.array([np.nanmean(Cmat[rr,j]) for j in range(len(KS))])
    tau=tau_of(rows); B=300; n=len(rows); boot=np.full((B,len(KS)),np.nan)
    for b in range(B): boot[b]=tau_of(rows[RNG.integers(0,n,n)])
    loci=np.nanpercentile(boot,2.5,0); hici=np.nanpercentile(boot,97.5,0)
    es=[dict(k=k,tau=round(float(tau[kidx[k]]),4),lo=round(float(loci[kidx[k]]),4),hi=round(float(hici[kidx[k]]),4)) for k in KS]
    pre=[k for k in range(-12,0)]
    npass=sum(1 for k in pre if (loci[kidx[k]]>=-SESOI and hici[kidx[k]]<=SESOI))
    # 사전 slope: pre-기간 τ의 k에 대한 회귀 기울기
    pk=np.array(pre); pv=np.array([tau[kidx[k]] for k in pre]); slope=float(np.polyfit(pk,pv,1)[0])
    return dict(n=int(n),ATT_plus12=dict(point=round(float(tau[kidx[12]]),4),ci95=[round(float(loci[kidx[12]]),4),round(float(hici[kidx[12]]),4)]),
                pretrend_equiv_pass=f"{npass}/12",pretrend_slope_per_month=round(slope,5),event_study=es)
res=dict(id="P016-WP7d",SESOI=SESOI,pregrowth_median=round(float(med),4),
         subgroups={nm:es_for(mask) for nm,mask in groups.items()})
json.dump(res,open(f"{OUT}/wp7d_subgroup_es.json","w"),ensure_ascii=False,indent=1)
open(f"{OUT}/wp7d.done","w").write("done")
print("=== WP7d 완료 ===")
for nm in groups:
    g=res["subgroups"][nm]; print(f"{nm}: n={g['n']} ATT+12={g['ATT_plus12']['point']}{g['ATT_plus12']['ci95']} 사전추세등가={g['pretrend_equiv_pass']} 사전기울기/월={g['pretrend_slope_per_month']}")
