# -*- coding: utf-8 -*-
"""WP11e — G4 pre-prediction 모형감사(§6·§22) + G5 trajectory-break·DR-DiD + G11 합성가중.
G4: 후보모형 fit(e−48..−25) → validation(e−24..−7) OOS MSE로 선택 → freeze → event(e+7..+12) 효과 재산출.
  M1 매칭평균변화(누수차단: 공변량은 fitting창만) M2 firm 선형추세 M3 산업×월 평균 M4 합성가중(NNLS).
G5: 2차차분 A_i=(Y+12−Y0)−(Y0−Y−12) vs 매칭대조 · DR-lite AIPW(distress 공변량, treated vs distressed 청정대조).
산출: shared/outputs/pipe_wp11_2026-08-23/wp11e.json
"""
import os,json,warnings; warnings.filterwarnings("ignore")
import numpy as np,pandas as pd
import statsmodels.api as sm
from scipy.optimize import nnls
BASE=os.environ.get("P016_BASE", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))   # 원 경로는 제거했다 — 실행 시 P016_BASE 로 지정하거나 기본값 사용
RE=f"{BASE}/shared/outputs/pipe_r1_reextract_2026-08-22"
OUT=f"{BASE}/shared/outputs/pipe_wp11_2026-08-23"
RNG=np.random.default_rng(20260822)
CL=pd.read_csv(f"{OUT}/controls_clean.csv",dtype={"bn":str}); clean=list(CL[CL.third_hist==False].bn)
FIN=pd.read_csv(f"{OUT}/fin_distress_panel.csv",dtype={"bn":str})
fin={(r.bn,int(r.year)):(r.lev,r.roa,r.cash,int(r.impaired),int(r.loss)) for r in FIN.itertuples()}
def fin_asof(bn,yr):
    for y in (yr-1,yr-2):
        v=fin.get((bn,y))
        if v: return v
    return None
nps=pd.read_parquet(f"{BASE}/shared/data/processed/nps_monthly_matched_v2.parquet",columns=["bn10","data_ym","가입자수","업종"])
nps["ym"]=pd.PeriodIndex(nps["data_ym"],freq="M"); nps["le"]=np.log1p(nps["가입자수"].astype(float))
months=pd.period_range(nps.ym.min(),nps.ym.max(),freq="M"); mi={m:j for j,m in enumerate(months)}; NM=len(months)
piv=nps.pivot_table(index="bn10",columns="ym",values="le",aggfunc="mean").reindex(columns=months)
idx=list(piv.index); fx={b:i for i,b in enumerate(idx)}; LE=piv.to_numpy(float)
ind2=nps.groupby("bn10")["업종"].agg(lambda s:str(s.iloc[0])[:2])
crow=np.array([fx[b] for b in clean if b in fx]); cbn=[b for b in clean if b in fx]
T=pd.read_csv(f"{RE}/treatment_master_v2.csv",dtype=str); T["k"]=T["k"].str.replace(r'\D','',regex=True).str.zfill(10)
T["ev"]=pd.to_datetime(T["event_dt"],errors="coerce").dt.to_period("M"); T=T.dropna(subset=["ev"]).drop_duplicates("k")
# ===== G4 모형감사 (e>=48 subsample) =====
sub=[]
for r in T.itertuples():
    e=mi.get(r.ev)
    if e is None or r.k not in fx: continue
    if e<48 or e+12>=NM: continue
    row=LE[fx[r.k]]
    fitc=row[e-48:e-24]; valc=row[e-24:e-6]
    if np.sum(np.isfinite(fitc))<16 or np.sum(np.isfinite(valc))<10: continue
    sub.append((r.k,e))
print(f"G4 subsample {len(sub)}",flush=True)
def mse(pred,act):
    ok=np.isfinite(pred)&np.isfinite(act)
    return float(np.mean((pred[ok]-act[ok])**2)) if ok.sum()>=6 else np.nan
CFIT=LE[crow][:,:]
err={m:[] for m in ("M1_match","M2_trend","M3_industry","M4_synth")}
frozen_pred={}
for k,e in sub:
    row=LE[fx[k]]; anchor=row[e-25]
    if not np.isfinite(anchor): continue
    valid_t=np.arange(e-24,e-6); act=row[valid_t]
    # M1: fitting창 공변량 매칭 (누수차단): logsize=avg(e-27..e-25), pg=le(e-25)-le(e-37)
    ls=np.nanmean(row[e-27:e-24]); pg=row[e-25]-row[e-37] if np.isfinite(row[e-37]) else np.nan
    m1=np.full(len(valid_t),np.nan)
    if np.isfinite(ls) and np.isfinite(pg):
        cls=np.nanmean(CFIT[:,e-27:e-24],1); cpg=CFIT[:,e-25]-CFIT[:,e-37]
        okc=np.isfinite(cls)&np.isfinite(cpg)&np.isfinite(CFIT[:,e-25])
        dist=(cls-ls)**2+(cpg-pg)**2; dist[~okc]=np.inf
        nb=np.argsort(dist)[:50]
        base_c=CFIT[nb,e-25][:,None]
        m1=anchor+np.nanmean(CFIT[nb][:,valid_t]-base_c,0)
    # M2: firm 선형추세
    ft=np.arange(e-48,e-24); fy=row[ft]; okf=np.isfinite(fy)
    b1,b0=np.polyfit(ft[okf],fy[okf],1)
    m2=b0+b1*valid_t
    # M3: 산업 평균 변화
    myind=ind2.get(k,"99"); sel=np.array([ind2.get(b,"")==myind for b in cbn])
    if sel.sum()>=10:
        grp=CFIT[sel]; base_g=grp[:,e-25][:,None]
        m3=anchor+np.nanmean(grp[:,valid_t]-base_g,0)
    else: m3=np.full(len(valid_t),np.nan)
    # M4: NNLS 합성 (fitting 경로 상 최근접 200 → nnls)
    fitpath=row[e-48:e-24]
    cand_ok=np.all(np.isfinite(CFIT[:,e-48:e-24]),1)&np.isfinite(CFIT[:,e-25])
    ci_=np.where(cand_ok)[0]
    m4=np.full(len(valid_t),np.nan)
    if len(ci_)>=30 and np.all(np.isfinite(fitpath)):
        d2_=np.sum((CFIT[ci_][:,e-48:e-24]-fitpath)**2,1); near=ci_[np.argsort(d2_)[:200]]
        A=CFIT[near][:,e-48:e-24].T; bvec=fitpath
        try:
            w,_=nnls(A,bvec)
            if w.sum()>0:
                w=w/w.sum(); m4=w@CFIT[near][:,valid_t]
        except Exception: pass
    for nm,pr in [("M1_match",m1),("M2_trend",m2),("M3_industry",m3),("M4_synth",m4)]:
        e_=mse(pr,act)
        if e_==e_: err[nm].append(e_)
    frozen_pred[k]=dict(e=e,anchor=anchor)
oos={nm:round(float(np.mean(v)),5) for nm,v in err.items() if v}
winner=min(oos,key=oos.get)
print("G4 OOS MSE:",oos,"→ winner:",winner,flush=True)
# frozen winner로 event 효과 (예측을 post 창으로 연장)
effs=[]
for k,e in sub:
    row=LE[fx[k]]; anchor=row[e-25]
    postt=np.arange(e+7,e+13); act=row[postt]
    if np.sum(np.isfinite(act))<3 or not np.isfinite(anchor): continue
    if winner=="M2_trend":
        ft=np.arange(e-48,e-24); fy=row[ft]; okf=np.isfinite(fy)
        b1,b0=np.polyfit(ft[okf],fy[okf],1); pred=b0+b1*postt
    elif winner=="M3_industry":
        myind=ind2.get(k,"99"); sel=np.array([ind2.get(b,"")==myind for b in cbn])
        if sel.sum()<10: continue
        grp=CFIT[sel]; pred=anchor+np.nanmean(grp[:,postt]-grp[:,e-25][:,None],0)
    elif winner=="M4_synth":
        fitpath=row[e-48:e-24]
        cand_ok=np.all(np.isfinite(CFIT[:,e-48:e-24]),1)&np.isfinite(CFIT[:,e-25])
        ci_=np.where(cand_ok)[0]
        if len(ci_)<30 or not np.all(np.isfinite(fitpath)): continue
        d2_=np.sum((CFIT[ci_][:,e-48:e-24]-fitpath)**2,1); near=ci_[np.argsort(d2_)[:200]]
        try:
            w,_=nnls(CFIT[near][:,e-48:e-24].T,fitpath)
            if w.sum()==0: continue
            w=w/w.sum(); pred=w@CFIT[near][:,postt]
        except Exception: continue
    else:  # M1
        ls=np.nanmean(row[e-27:e-24]); pg=row[e-25]-row[e-37] if np.isfinite(row[e-37]) else np.nan
        if not(np.isfinite(ls) and np.isfinite(pg)): continue
        cls=np.nanmean(CFIT[:,e-27:e-24],1); cpg=CFIT[:,e-25]-CFIT[:,e-37]
        okc=np.isfinite(cls)&np.isfinite(cpg)&np.isfinite(CFIT[:,e-25])
        dist=(cls-ls)**2+(cpg-pg)**2; dist[~okc]=np.inf
        nb=np.argsort(dist)[:50]
        pred=anchor+np.nanmean(CFIT[nb][:,postt]-CFIT[nb,e-25][:,None],0)
    d=np.nanmean(act)-np.nanmean(pred)
    if np.isfinite(d): effs.append(d)
effs=np.array(effs)
bs=np.array([np.mean(effs[RNG.integers(0,len(effs),len(effs))]) for _ in range(2000)])
g4=dict(oos_mse=oos,winner=winner,n_event=int(len(effs)),
        event_effect=round(float(effs.mean()),4),ci=[round(float(np.percentile(bs,2.5)),4),round(float(np.percentile(bs,97.5)),4)],
        p10=round(float(np.percentile(effs,10)),4),median=round(float(np.median(effs)),4))
print("G4 frozen-model event 효과:",g4,flush=True)
# ===== G5a: trajectory break =====
A_t=[]; A_c=[]
for r in T.itertuples():
    e=mi.get(r.ev)
    if e is None or r.k not in fx or e-15<0 or e+12>=NM: continue
    row=LE[fx[r.k]]
    Y0=np.nanmean(row[e-3:e]); Yp=np.nanmean(row[e+10:e+13]); Ym=np.nanmean(row[e-15:e-12])
    if not(np.isfinite(Y0) and np.isfinite(Yp) and np.isfinite(Ym)): continue
    A_t.append((Yp-Y0)-(Y0-Ym))
# 대조 A: 청정대조 전체, treated 이벤트월 분포에서 무작위 배정 (1000 샘플)
evs=[mi[r.ev] for r in T.itertuples() if mi.get(r.ev) is not None]
for _ in range(2000):
    b=crow[RNG.integers(0,len(crow))]; e=evs[RNG.integers(0,len(evs))]
    if e-15<0 or e+12>=NM: continue
    row=LE[b]
    Y0=np.nanmean(row[e-3:e]); Yp=np.nanmean(row[e+10:e+13]); Ym=np.nanmean(row[e-15:e-12])
    if not(np.isfinite(Y0) and np.isfinite(Yp) and np.isfinite(Ym)): continue
    A_c.append((Yp-Y0)-(Y0-Ym))
A_t=np.array(A_t); A_c=np.array(A_c)
obs=float(A_t.mean()-A_c.mean())
bs=np.array([np.mean(A_t[RNG.integers(0,len(A_t),len(A_t))])-np.mean(A_c[RNG.integers(0,len(A_c),len(A_c))]) for _ in range(2000)])
g5a=dict(n_t=int(len(A_t)),n_c=int(len(A_c)),tau_accel=round(obs,4),
         ci=[round(float(np.percentile(bs,2.5)),4),round(float(np.percentile(bs,97.5)),4)],
         accel_p10_treated=round(float(np.percentile(A_t,10)),4),accel_p10_ctrl=round(float(np.percentile(A_c,10)),4))
print("G5a trajectory-break:",g5a,flush=True)
# ===== G5b: DR-lite AIPW (distress 공변량) =====
rows=[]
for r in T.itertuples():
    e=mi.get(r.ev)
    if e is None or r.k not in fx or e-13<0 or e+12>=NM: continue
    row=LE[fx[r.k]]
    bc=row[e-12:e]; v=row[e+7:e+13]
    if np.sum(np.isfinite(bc))<6 or np.sum(np.isfinite(v))<3: continue
    if not(np.isfinite(row[e-1]) and np.isfinite(row[e-13])): continue
    fv=fin_asof(r.k,r.ev.year)
    if not fv: continue
    lev,roa,cash,imp,loss=[x if x==x else 0 for x in fv]
    rows.append(dict(D=float(np.nanmean(v)-np.nanmean(bc)),treat=1,ls=float(np.nanmean(row[e-3:e])),pg=float(row[e-1]-row[e-13]),
                     lev=min(lev,10),roa=max(min(roa,1),-1),cash=cash,imp=imp,loss=loss,yr=r.ev.year))
evs_arr=[ (mi[r.ev],r.ev.year) for r in T.itertuples() if mi.get(r.ev) is not None]
cnt=0; tries=0
while cnt<3000 and tries<20000:
    tries+=1
    j=RNG.integers(0,len(crow)); b=cbn[j]; e,yr=evs_arr[RNG.integers(0,len(evs_arr))]
    if e-13<0 or e+12>=NM: continue
    row=LE[crow[j]]
    bc=row[e-12:e]; v=row[e+7:e+13]
    if np.sum(np.isfinite(bc))<6 or np.sum(np.isfinite(v))<3: continue
    if not(np.isfinite(row[e-1]) and np.isfinite(row[e-13])): continue
    fv=fin_asof(b,yr)
    if not fv: continue
    lev,roa,cash,imp,loss=[x if x==x else 0 for x in fv]
    rows.append(dict(D=float(np.nanmean(v)-np.nanmean(bc)),treat=0,ls=float(np.nanmean(row[e-3:e])),pg=float(row[e-1]-row[e-13]),
                     lev=min(lev,10),roa=max(min(roa,1),-1),cash=cash,imp=imp,loss=loss,yr=yr)); cnt+=1
DFR=pd.DataFrame(rows).dropna()
Xcols=["ls","pg","lev","roa","cash","imp","loss","yr"]
Xa=(DFR[Xcols]-DFR[Xcols].mean())/DFR[Xcols].std()
lg=sm.Logit(DFR.treat.values,sm.add_constant(Xa.values)).fit(disp=0); ps=np.clip(np.asarray(lg.predict(sm.add_constant(Xa.values))),0.01,0.99)
C0=DFR.treat.values==0; T1=DFR.treat.values==1
orx=sm.OLS(DFR.D.values[C0],sm.add_constant(Xa.values[C0])).fit()
mhat=np.asarray(orx.predict(sm.add_constant(Xa.values)))
w0=ps[C0]/(1-ps[C0])
att=float(np.mean(DFR.D.values[T1]-mhat[T1]) - np.average(DFR.D.values[C0]-mhat[C0],weights=w0))
bsv=[]
tix=np.where(T1)[0]; cix=np.where(C0)[0]
for _ in range(1000):
    ti=tix[RNG.integers(0,len(tix),len(tix))]; ci_=cix[RNG.integers(0,len(cix),len(cix))]
    w=ps[ci_]/(1-ps[ci_])
    bsv.append(float(np.mean(DFR.D.values[ti]-mhat[ti])-np.average(DFR.D.values[ci_]-mhat[ci_],weights=w)))
g5b=dict(n_treat=int(T1.sum()),n_ctrl=int(C0.sum()),ATT_dr=round(att,4),
         ci=[round(float(np.percentile(bsv,2.5)),4),round(float(np.percentile(bsv,97.5)),4)],
         note="AIPW, distress 공변량(lev·roa·cash·impaired·loss)+ls·pg·yr. 재무커버 있는 treated만.")
print("G5b DR-lite:",g5b,flush=True)
json.dump(dict(G4=g4,G5a_trajbreak=g5a,G5b_dr=g5b),open(f"{OUT}/wp11e.json","w"),ensure_ascii=False,indent=1)
open(f"{OUT}/wp11e.done","w").write("done")
print("\n=== WP11e 완료 ===")
