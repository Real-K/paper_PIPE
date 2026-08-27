# WP13 재실행 사본 (2026-08-27): 원본 wp9a_method_audit.py · 출력만 pipe_wp13 으로 치환 + 표본기간 필터.
# 210 고정은 적용하지 않는다 — 이 배터리의 목적이 **포함규칙별 n 변동**(base3/base12·avg1-12/avg7-12)을 보이는 것이라
# 처치집합을 고용 1차표본으로 못박으면 비교 자체가 사라진다. 대조풀도 legacy mixed 유지(부록 A 의 정의).
# -*- coding: utf-8 -*-
"""P-016 WP9a — 방법론 효율 배터리 (PI 지시: 현상에 맞는 모델 재점검. 조작 아님 — 모든 변형 결과 전부 보고).
(1) 퇴출 census: NPS 탈퇴일자로 처치 vs 매칭대조 12개월 내 퇴출률 (생존자편향 정량화 + 그 자체가 결과)
(2) DHS 성장률 outcome (퇴출=-2 포함, Davis-Haltiwanger) — 퇴출포함 ATT
(3) baseline 12개월 + post 평균 estimand (+1..+12, +7..+12) — 노이즈 감축
(4) QTE p10/25/50/75/90 + bootstrap CI — 분포 모델
(5) k=50 매칭 변형
전부 B=2000. 산출: shared/outputs/pipe_wp13_2026-08-26/wp9a_audit.json
"""
import os,json,warnings; warnings.filterwarnings("ignore")
import numpy as np,pandas as pd
import statsmodels.api as sm
BASE=os.environ.get("P016_BASE", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))   # 원 경로는 제거했다 — 실행 시 P016_BASE 로 지정하거나 기본값 사용
RE=f"{BASE}/shared/outputs/pipe_r1_reextract_2026-08-22"
OUT=f"{BASE}/shared/outputs/pipe_wp13_2026-08-26"; os.makedirs(OUT,exist_ok=True)
RNG=np.random.default_rng(20260823); B=2000
nps=pd.read_parquet(f"{BASE}/shared/data/processed/nps_monthly_matched_v2.parquet",columns=["bn10","data_ym","가입자수","업종","시도","탈퇴일자"])
nps["ym"]=pd.PeriodIndex(nps["data_ym"],freq="M"); nps["le"]=np.log1p(nps["가입자수"].astype(float))
months=pd.period_range(nps.ym.min(),nps.ym.max(),freq="M"); mi={m:j for j,m in enumerate(months)}; NM=len(months)
piv=nps.pivot_table(index="bn10",columns="ym",values="le",aggfunc="mean").reindex(columns=months)
idx=list(piv.index); firm_ix={b:i for i,b in enumerate(idx)}
LE=piv.to_numpy(float)
EMP=nps.pivot_table(index="bn10",columns="ym",values="가입자수",aggfunc="mean").reindex(columns=months).reindex(index=idx).to_numpy(float)
# 퇴출월 (탈퇴일자)
exd=nps.groupby("bn10")["탈퇴일자"].first()
exm=np.full(len(idx),-1,dtype=int)
for b,d in exd.items():
    d=pd.to_datetime(d,errors="coerce")
    if pd.notna(d):
        p=pd.Period(d,'M')
        exm[firm_ix[b]]=mi.get(p, NM if p>months[-1] else -1)
firm_ind=nps.groupby("bn10")["업종"].agg(lambda s:str(s.iloc[0])[:2]); firm_sido=nps.groupby("bn10")["시도"].agg(lambda s:str(s.iloc[0]))
firm_med=np.nanmedian(np.where(np.isfinite(LE),LE,np.nan),axis=1)
pb=pd.read_csv(f"{BASE}/shared/data/processed/pitchbook_all_status_v1.csv",dtype=str)
pbbn=set(pb["bn"].astype(str).str.replace(r'\D','',regex=True).str.zfill(10).dropna())
T=pd.read_csv(f"{RE}/treatment_master_v2.csv",dtype=str); T["k"]=T["k"].str.replace(r'\D','',regex=True).str.zfill(10)
T=T[pd.to_numeric(T.event_dt.astype(str).str[:4],errors="coerce").between(2015,2025)]   # 표본기간 2015–2025(원고 명시) — WP13, 2026-08-27
T["ev"]=pd.to_datetime(T["event_dt"],errors="coerce").dt.to_period("M"); T=T.dropna(subset=["ev"]).drop_duplicates("k"); tb=set(T.k)
def cap(s): return 1.0 if str(s) in ("11","41","28") else 0.0
def man(i):
    try: return 1.0 if 10<=int(i)<=34 else 0.0
    except: return 0.0
def g12(r): d=r[12:]-r[:-12]; return d[np.isfinite(d)]
PRE=3
rec=[]
for r in T.itertuples():
    if r.k not in firm_ix: continue
    fi=firm_ix[r.k]; e=mi.get(r.ev)
    if e is None: continue
    row=LE[fi]; pre=[e-j for j in range(1,PRE+1) if 0<=e-j<NM]
    if sum(np.isfinite(row[i]) for i in pre)<3: continue
    if sum(np.isfinite(row[e+j]) for j in range(1,13) if 0<=e+j<NM)<3 and not(0<exm[fi]<=e+12): continue
    if not(0<=e-1<NM and 0<=e-13<NM and np.isfinite(row[e-1]) and np.isfinite(row[e-13])): continue
    rec.append(dict(k=r.k,fi=fi,e=e,logsize=np.nanmean([row[i] for i in pre]),pregrowth=row[e-1]-row[e-13],cap=cap(firm_sido.get(r.k,"0")),man=man(firm_ind.get(r.k,"99"))))
Tm=pd.DataFrame(rec); print(f"처치 usable {len(Tm)} (퇴출자 포함 규칙)",flush=True)
crows=np.array([i for i,b in enumerate(idx) if (b not in pbbn) and (b not in tb)])
cpg=np.array([np.nanmean(g12(LE[r])) if g12(LE[r]).size else np.nan for r in crows]); cls=firm_med[crows]
ok=np.isfinite(cls)&np.isfinite(cpg); crows=crows[ok]; cls=cls[ok]; cpg=cpg[ok]
ccap=np.array([cap(firm_sido.get(idx[r],"0")) for r in crows]); cman=np.array([man(firm_ind.get(idx[r],"99")) for r in crows])
Xt=np.column_stack([Tm.logsize,Tm.logsize**2,Tm.pregrowth,Tm.cap,Tm.man]); Xc=np.column_stack([cls,cls**2,cpg,ccap,cman])
X=np.vstack([Xt,Xc]); y=np.r_[np.ones(len(Xt)),np.zeros(len(Xc))]; Xs=(X-X.mean(0))/X.std(0)
psm=sm.Logit(y,sm.add_constant(Xs)).fit(disp=0); xb=psm.predict(sm.add_constant(Xs),linear=True); xbt=xb[:len(Xt)]; xbc=xb[len(Xt):]
lo,hi=xbt.min(),xbt.max(); supp=(xbc>=lo)&(xbc<=hi); cr=crows[supp]; xbcs=xbc[supp]; calp=0.2*np.std(xb)
o=np.argsort(xbcs); xs_=xbcs[o]; cs_=cr[o]
def knn(xi,K):
    pos=np.searchsorted(xs_,xi); cand=list(range(max(0,pos-K-2),min(len(xs_),pos+K+2))); dd=np.abs(xs_[cand]-xi); sel=np.argsort(dd)[:K]
    return [cs_[cand[s]] for s in sel if dd[s]<=calp]
M10=[knn(x,10) for x in xbt]; M50=[knn(x,50) for x in xbt]
def bci(vec,fn=np.nanmean):
    v=vec[np.isfinite(vec)]; n=len(v)
    bs=np.array([fn(v[RNG.integers(0,n,n)]) for _ in range(B)])
    return round(float(fn(v)),4),[round(float(np.percentile(bs,2.5)),4),round(float(np.percentile(bs,97.5)),4)],n
def dlog(Tm,matches,base_pre,post_lo,post_hi,single=None):
    out=np.full(len(Tm),np.nan)
    for ii,r in enumerate(Tm.itertuples()):
        m=matches[ii]
        if not m: continue
        e=r.e; bc=[e-j for j in range(1,base_pre+1) if 0<=e-j<NM]
        bt=np.nanmean(LE[r.fi,bc])
        if np.sum(np.isfinite(LE[r.fi,bc]))<max(3,base_pre//2) or not np.isfinite(bt): continue
        if single is not None: tcols=[e+single] if 0<=e+single<NM else []
        else: tcols=[e+j for j in range(post_lo,post_hi+1) if 0<=e+j<NM]
        tv=LE[r.fi,tcols] if tcols else np.array([np.nan])
        if np.sum(np.isfinite(tv))<(1 if single is not None else 3): continue
        Dt=np.nanmean(tv)-bt
        dc=[]
        for c in m:
            cb=np.nanmean(LE[c,bc]); cv=LE[c,tcols] if tcols else np.array([np.nan])
            if np.isfinite(cb) and np.sum(np.isfinite(cv))>=(1 if single is not None else 3): dc.append(np.nanmean(cv)-cb)
        if len(dc)<3: continue
        out[ii]=Dt-np.mean(dc)
    return out
res={}
# (0) 재현: τ+12 단일, base3, k10
d_base=dlog(Tm,M10,3,None,None,single=12); pt,ci,n=bci(d_base); res["A_repro_tau12_base3_k10"]=dict(point=pt,ci=ci,n=n)
# (3a) base12
d_b12=dlog(Tm,M10,12,None,None,single=12); pt,ci,n=bci(d_b12); res["B_tau12_base12"]=dict(point=pt,ci=ci,n=n)
# (3b) 평균 estimand
d_avg=dlog(Tm,M10,12,1,12); pt,ci,n=bci(d_avg); res["C_avg1_12_base12"]=dict(point=pt,ci=ci,n=n)
d_a712=dlog(Tm,M10,12,7,12); pt,ci,n=bci(d_a712); res["D_avg7_12_base12"]=dict(point=pt,ci=ci,n=n)
# (5) k50
d_k50=dlog(Tm,M50,12,7,12); pt,ci,n=bci(d_k50); res["E_avg7_12_base12_k50"]=dict(point=pt,ci=ci,n=n)
print("A τ12/b3/k10:",res["A_repro_tau12_base3_k10"],flush=True)
print("B τ12/b12:",res["B_tau12_base12"],"| C avg1-12:",res["C_avg1_12_base12"],flush=True)
print("D avg7-12:",res["D_avg7_12_base12"],"| E k50:",res["E_avg7_12_base12_k50"],flush=True)
# (4) QTE on best-precision d (avg7_12 base12 k50)
dq=d_k50[np.isfinite(d_k50)]
qte={}
for q in (10,25,50,75,90):
    fn=lambda a,qq=q: np.percentile(a,qq)
    p_,c_,n_=bci(d_k50,fn); qte[f"p{q}"]=dict(point=p_,ci=c_)
res["F_QTE_avg7_12_k50"]=qte; print("F QTE:",qte,flush=True)
# (1) 퇴출 census + (2) DHS
def dhs(Tm,matches):
    out=np.full(len(Tm),np.nan); ex_t=np.full(len(Tm),np.nan); ex_c=np.full(len(Tm),np.nan)
    def g_of(fi,e):
        bc=[e-j for j in range(1,13) if 0<=e-j<NM]; bv=EMP[fi,bc]
        if np.sum(np.isfinite(bv))<6: return None,None
        Yb=np.nanmean(bv)
        if not np.isfinite(Yb) or Yb<=0: return None,None
        ex=exm[fi]; vals=[]
        for j in range(7,13):
            t=e+j
            if not(0<=t<NM): continue
            if 0<ex<=t: vals.append(0.0)
            elif np.isfinite(EMP[fi,t]): vals.append(float(EMP[fi,t]))
        if len(vals)<3: return None,None
        Yp=np.mean(vals)
        g=2*(Yp-Yb)/(Yp+Yb) if (Yp+Yb)>0 else -2.0
        return g, (1.0 if 0<ex<=e+12 else 0.0)
    for ii,r in enumerate(Tm.itertuples()):
        m=matches[ii]
        if not m: continue
        gt,et=g_of(r.fi,r.e)
        if gt is None: continue
        gcs=[];ecs=[]
        for c in m:
            gc,ec=g_of(c,r.e)
            if gc is not None: gcs.append(gc); ecs.append(ec)
        if len(gcs)<3: continue
        out[ii]=gt-np.mean(gcs); ex_t[ii]=et; ex_c[ii]=np.mean(ecs)
    return out,ex_t,ex_c
d_dhs,ex_t,ex_c=dhs(Tm,M50)
pt,ci,n=bci(d_dhs); res["G_DHS_exit_incl_k50"]=dict(point=pt,ci=ci,n=n)
ptm,cim,_=bci(d_dhs,np.nanmedian); res["G_DHS_median"]=dict(point=ptm,ci=cim)
exd_diff=ex_t-ex_c; pt,ci,n=bci(exd_diff); res["H_exit12_risk_diff"]=dict(point=pt,ci=ci,n=n,
    treated_exit_rate=round(float(np.nanmean(ex_t)),4),control_exit_rate=round(float(np.nanmean(ex_c)),4))
pct_neg=round(float(np.nanmean(d_dhs[np.isfinite(d_dhs)]<0)),3); res["G_DHS_pctneg"]=pct_neg
print("G DHS(퇴출포함):",res["G_DHS_exit_incl_k50"],"median:",res["G_DHS_median"],"%neg:",pct_neg,flush=True)
print("H 퇴출률차:",res["H_exit12_risk_diff"],flush=True)
json.dump(res,open(f"{OUT}/wp9a_audit.json","w"),ensure_ascii=False,indent=1)
open(f"{OUT}/wp9a.done","w").write("done")
print("\n=== WP9a 배터리 완료 ===")
