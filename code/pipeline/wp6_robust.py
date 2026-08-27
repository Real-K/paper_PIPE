# -*- coding: utf-8 -*-
"""P-016 WP6 — robustness + 메커니즘. 헤드라인 PSM v2 재현 후:
(A) gross-flow 분해: 신규(채용)/상실(이탈) ATT+12 → 채용동결 vs 이탈증가 채널.
(B) Rosenbaum Γ bounds: +12 pair difference 부호랭크 민감도 → Γ*.
(C) placebo: 주주배정/공모 비처치 유상증자 6사 동일설계 → 위(僞)효과 점추정+CI(rule11).
(D) 표본임계 민감도: >=1/>=1, >=6/>=6.
SESOI 동결 0.0559 재사용. 산출: shared/outputs/pipe_wp6_2026-08-23/wp6_robust.json
"""
import os,json,warnings,math; warnings.filterwarnings("ignore")
import numpy as np,pandas as pd
import statsmodels.api as sm
BASE=os.environ.get("P016_BASE", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))   # 원 경로는 제거했다 — 실행 시 P016_BASE 로 지정하거나 기본값 사용
RE=f"{BASE}/shared/outputs/pipe_r1_reextract_2026-08-22"
OUT=f"{BASE}/shared/outputs/pipe_wp6_2026-08-23"; os.makedirs(OUT,exist_ok=True)
RNG=np.random.default_rng(20260823)
SESOI=json.load(open(f"{BASE}/papers/P016_pipe-employment/04_design/wp4_pap_committed.json"))["SESOI"]

nps=pd.read_parquet(f"{BASE}/shared/data/processed/nps_monthly_matched_v2.parquet",
                    columns=["bn10","data_ym","가입자수","신규","상실","업종","시도"])
nps["ym"]=pd.PeriodIndex(nps["data_ym"],freq="M"); nps["le"]=np.log1p(nps["가입자수"].astype(float))
months=pd.period_range(nps.ym.min(),nps.ym.max(),freq="M"); mi={m:j for j,m in enumerate(months)}
def wide(col): return nps.pivot_table(index="bn10",columns="ym",values=col,aggfunc="mean").reindex(columns=months).to_numpy(dtype=float)
LE=wide("le"); EMP=wide("가입자수"); HIRE=wide("신규"); SEP=wide("상실")
idx=list(nps.pivot_table(index="bn10",columns="ym",values="le",aggfunc="mean").index)
firm_ix={b:i for i,b in enumerate(idx)}
firm_ind=nps.groupby("bn10")["업종"].agg(lambda s:str(s.iloc[0])[:2])
firm_sido=nps.groupby("bn10")["시도"].agg(lambda s:str(s.iloc[0]))
firm_med_le=np.nanmedian(np.where(np.isfinite(LE),LE,np.nan),axis=1)
pb=pd.read_csv(f"{BASE}/shared/data/processed/pitchbook_all_status_v1.csv",dtype=str)
pbbn=set(pb["bn"].astype(str).str.replace(r'\D','',regex=True).str.zfill(10).dropna())
def capital(s): return 1.0 if str(s) in ("11","41","28") else 0.0
def manuf(i):
    try: return 1.0 if 10<=int(i)<=34 else 0.0
    except: return 0.0
def g12(row): d=row[12:]-row[:-12]; return d[np.isfinite(d)]
PRE=3;POST=12;PREW=13

# 대조 후보 (never-PIPE, treated_bn 제외)
T=pd.read_csv(f"{RE}/treatment_master_v2.csv",dtype=str)
T["k"]=T["k"].str.replace(r'\D','',regex=True).str.zfill(10)
T["ev"]=pd.to_datetime(T["event_dt"],errors="coerce").dt.to_period("M"); T=T.dropna(subset=["ev"]).drop_duplicates("k")
treated_bn=set(T.k)
crows=np.array([i for i,b in enumerate(idx) if (b not in pbbn) and (b not in treated_bn)])
cpg=np.array([np.nanmean(g12(LE[r])) if g12(LE[r]).size else np.nan for r in crows])
cls=firm_med_le[crows]; okc=np.isfinite(cls)&np.isfinite(cpg)
crows=crows[okc]; cls=cls[okc]; cpg=cpg[okc]
ccap=np.array([capital(firm_sido.get(idx[r],"0")) for r in crows]); cman=np.array([manuf(firm_ind.get(idx[r],"99")) for r in crows])
Xc=np.column_stack([cls,cls**2,cpg,ccap,cman])

def build_treated(df,minpre,minpost):
    rec=[]
    for r in df.itertuples():
        if r.k not in firm_ix: continue
        fi=firm_ix[r.k]; e=mi.get(r.ev)
        if e is None: continue
        row=LE[fi]; pre_idx=[e-j for j in range(1,PRE+1) if 0<=e-j<len(months)]
        npre=sum(np.isfinite(row[i]) for i in pre_idx); npost=sum(np.isfinite(row[e+j]) for j in range(1,POST+1) if 0<=e+j<len(months))
        if npre<minpre or npost<minpost: continue
        if not(0<=e-1<len(months) and 0<=e-PREW<len(months) and np.isfinite(row[e-1]) and np.isfinite(row[e-PREW])): continue
        base=np.nanmean([row[i] for i in pre_idx]); pg=row[e-1]-row[e-PREW]
        rec.append(dict(k=r.k,fi=fi,e=e,base=base,logsize=base,pregrowth=pg,cap=capital(firm_sido.get(r.k,"0")),man=manuf(firm_ind.get(r.k,"99"))))
    return pd.DataFrame(rec)

def psm_match(Tm):
    Xt=np.column_stack([Tm.logsize,Tm.logsize**2,Tm.pregrowth,Tm.cap,Tm.man])
    X=np.vstack([Xt,Xc]); y=np.r_[np.ones(len(Xt)),np.zeros(len(Xc))]
    Xs=(X-X.mean(0))/X.std(0); psm=sm.Logit(y,sm.add_constant(Xs)).fit(disp=0)
    xb=psm.predict(sm.add_constant(Xs),linear=True); xbt=xb[:len(Xt)]; xbc=xb[len(Xt):]
    lo,hi=xbt.min(),xbt.max(); supp=(xbc>=lo)&(xbc<=hi)
    cr=crows[supp]; xbcs=xbc[supp]; cal=0.2*np.std(xb); K=10
    o=np.argsort(xbcs); xs=xbcs[o]; cs=cr[o]
    matches=[]
    for xi in xbt:
        pos=np.searchsorted(xs,xi); cand=list(range(max(0,pos-K-2),min(len(xs),pos+K+2)))
        d=np.abs(xs[cand]-xi); sel=np.argsort(d)[:K]; matches.append([cs[cand[s]] for s in sel if d[s]<=cal])
    return matches,Xt

def es_att(Tm,matches,MAT,col_base,col_lvl,cumulative=False):
    # returns per-treated contribution at +12 (level ATT) ; if cumulative, uses cum flow / baseline emp
    KS=list(range(-12,13)); kidx={k:j for j,k in enumerate(KS)}
    contrib=np.full(len(Tm),np.nan)
    for ii,r in enumerate(Tm.itertuples()):
        m=matches[ii]
        if not m: continue
        e=r.e
        if cumulative:
            base_emp=np.nanmean([EMP[r.fi,e-j] for j in range(1,PRE+1) if 0<=e-j<len(months)])
            post=[e+j for j in range(1,POST+1) if 0<=e+j<len(months)]
            if base_emp is None or not np.isfinite(base_emp) or base_emp<=0: continue
            t_cum=np.nansum([MAT[r.fi,p] for p in post])/base_emp
            dc=[]
            for c in m:
                cbe=np.nanmean([EMP[c,e-j] for j in range(1,PRE+1) if 0<=e-j<len(months)])
                if not np.isfinite(cbe) or cbe<=0: continue
                dc.append(np.nansum([MAT[c,p] for p in post])/cbe)
            if len(dc)<3: continue
            contrib[ii]=t_cum-np.mean(dc)
        else:
            t=e+12
            if not(0<=t<len(months)) or not np.isfinite(LE[r.fi,t]): continue
            bcols=[e-j for j in range(1,PRE+1) if 0<=e-j<len(months)]
            Dt=LE[r.fi,t]-np.nanmean([LE[r.fi,b] for b in bcols])
            dc=[]
            for c in m:
                cb=np.nanmean([LE[c,b] for b in bcols]); yc=LE[c,t]
                if np.isfinite(cb) and np.isfinite(yc): dc.append(yc-cb)
            if len(dc)<3: continue
            contrib[ii]=Dt-np.mean(dc)
    return contrib

def boot_ci(contrib,B=200):
    v=np.where(np.isfinite(contrib))[0]; pt=np.nanmean(contrib[v])
    bs=np.array([np.nanmean(contrib[v[RNG.integers(0,len(v),len(v))]]) for _ in range(B)])
    return round(float(pt),4),[round(float(np.percentile(bs,2.5)),4),round(float(np.percentile(bs,97.5)),4)],int(len(v))

# ===== 헤드라인 표본 재현 (>=3/>=3) =====
Tm=build_treated(T,3,3); matches,Xt=psm_match(Tm)
c_le=es_att(Tm,matches,LE,None,None,False)
pt_le,ci_le,n_le=boot_ci(c_le)
# (A) gross-flow
c_hire=es_att(Tm,matches,HIRE,None,None,True); pt_h,ci_h,_=boot_ci(c_hire)
c_sep =es_att(Tm,matches,SEP ,None,None,True); pt_s,ci_s,_=boot_ci(c_sep)
print(f"[A] ATT+12 logemp={pt_le}{ci_le} · 누적채용/base ATT={pt_h}{ci_h} · 누적이탈/base ATT={pt_s}{ci_s}",flush=True)

# (B) Rosenbaum Γ (부호랭크 민감도, 음효과 방향)
d=c_le[np.isfinite(c_le)]; ad=np.abs(d); q=pd.Series(ad).rank().values; s=(d>0).astype(float)
Tstat=np.sum(s*q)
from math import erf
def pbound(gam):
    # 음(−)효과: T가 작음을 검정. 보수적(최대 p-value) 하한 → p+ = 1/(1+Γ)
    pp=1.0/(1+gam); Ep=np.sum(q*pp); Vp=np.sum(q*q*pp*(1-pp))
    z=(Tstat-Ep)/math.sqrt(Vp)
    return 0.5*(1+erf(z/math.sqrt(2)))   # Φ(z)=P(Z<=z) one-sided (하단)
p_at1=pbound(1.0)
gstar=">3.0"
for gam in np.arange(1.0,3.01,0.05):
    if pbound(gam)>0.05: gstar=round(float(gam),2); break
print(f"[B] Rosenbaum Γ* ≈ {gstar} (T={Tstat:.0f}, n={len(d)}, p@Γ=1={p_at1:.4f})",flush=True)

# (C) placebo: 주주배정/공모 비처치 (r1b rights/public + r1c non_third)
import csv
b=list(csv.DictReader(open(f"{RE}/r1b_classified.csv",encoding='utf-8'))); mb={c.strip().lstrip('﻿'):c for c in b[0].keys()}
def tf(x): return str(x).strip().lower() in ("1","true")
plc=[r[mb["k"]] for r in b if (tf(r.get(mb.get("rights",""),"")) or tf(r.get(mb.get("public",""),""))) and not tf(r.get(mb["is_treat_3rd"],""))]
# placebo는 event_dt 필요 — r1b_classified event_dt
plc_dt={r[mb["k"]]:r.get(mb.get("event_dt",""),"") for r in b if r[mb["k"]] in plc}
Pdf=pd.DataFrame([dict(k=k.replace('-','').zfill(10),ev=pd.Period(dt[:7],'M')) for k,dt in plc_dt.items() if dt])
placebo_res="n<3 (검정력 없음)"
if len(Pdf)>=3:
    Pm=build_treated(Pdf,1,1)
    if len(Pm)>=3:
        pmatch,_=psm_match(Pm); cpl=es_att(Pm,pmatch,LE,None,None,False); ppt,pci,pn=boot_ci(cpl)
        placebo_res=dict(n=pn,ATT_plus12=ppt,ci95=pci,note="주주배정/공모 위약; rule11 점추정+CI. 소표본 저검정력.")
print(f"[C] placebo: {placebo_res}",flush=True)

# (D) 표본임계 민감도 (pre-baseline은 3개월 → npre<=3; POST 깊이 변형이 유효)
sens={}
for (lo,hi,nm) in [(1,1,"ge1pre_ge1post"),(3,6,"basecomplete_ge6post"),(3,12,"basecomplete_ge12post")]:
    Ts=build_treated(T,lo,hi)
    if len(Ts)<10: sens[nm]=dict(n=len(Ts),note="n<10 skip"); continue
    ms,_=psm_match(Ts); cs=es_att(Ts,ms,LE,None,None,False); p,c,n=boot_ci(cs); sens[nm]=dict(n=n,ATT_plus12=p,ci95=c)
print(f"[D] 임계민감도: {sens}",flush=True)

res=dict(id="P016-WP6",date="2026-08-23",SESOI=SESOI,headline_reproduce=dict(n=n_le,ATT_plus12=pt_le,ci95=ci_le),
         A_gross_flow=dict(cum_hire_over_base_ATT=dict(point=pt_h,ci95=ci_h),cum_sep_over_base_ATT=dict(point=pt_s,ci95=ci_s),
                           interpretation="음(−)이면 채용동결(채용↓)이 채널; 이탈 ATT 양(+)이면 layoff 채널."),
         B_rosenbaum=dict(gamma_star=gstar,p_at_gamma1=round(float(p_at1),4),T=float(Tstat),n=int(len(d))),
         C_placebo=placebo_res, D_threshold_sensitivity=sens)
json.dump(res,open(f"{OUT}/wp6_robust.json","w"),ensure_ascii=False,indent=1)
open(f"{OUT}/wp6.done","w").write("done")
print(f"\n=== WP6 완료 ===\nATT+12={pt_le}{ci_le} · 채용ATT={pt_h} 이탈ATT={pt_s} · Γ*={gstar} · placebo={placebo_res if isinstance(placebo_res,str) else placebo_res.get('ATT_plus12')} · 임계 {sens}")
