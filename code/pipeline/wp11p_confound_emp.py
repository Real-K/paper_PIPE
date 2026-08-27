# -*- coding: utf-8 -*-
"""WP11p — 오염 이벤트 제외 후 고용 재추정 (wp11o의 confound_flags.csv 사용).
상장 청정풀·k50·avg(+1..+12)/base12 사양으로 전체 vs 비오염 표본 대조 + 꼬리(p10·collapse@-0.35).
산출: shared/outputs/pipe_wp11_2026-08-23/wp11p_confound_emp.json
"""
import os,json,csv,re,warnings,sys; warnings.filterwarnings("ignore")
import numpy as np,pandas as pd
import statsmodels.api as sm
BASE=os.environ.get("P016_BASE", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))   # 원 경로는 제거했다 — 실행 시 P016_BASE 로 지정하거나 기본값 사용
RE=f"{BASE}/shared/outputs/pipe_r1_reextract_2026-08-22"
OUT=f"{BASE}/shared/outputs/pipe_wp11_2026-08-23"
sys.path.insert(0,f"{BASE}/shared/lib"); from safe_dates import parse_dates
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
idx=list(piv.index); fx={b:i for i,b in enumerate(idx)}; LE=piv.to_numpy(float)
find=nps.groupby("bn10")["업종"].agg(lambda s:str(s.iloc[0])[:2]); fsido=nps.groupby("bn10")["시도"].agg(lambda s:str(s.iloc[0]))
fmed=np.nanmedian(np.where(np.isfinite(LE),LE,np.nan),axis=1)
CL=pd.read_csv(f"{OUT}/controls_clean.csv",dtype={"bn":str}); clean_ctrl=set(CL[CL.third_hist==False].bn)
def cap(s): return 1.0 if str(s) in ("11","41","28") else 0.0
def man(i):
    try: return 1.0 if 10<=int(i)<=34 else 0.0
    except: return 0.0
def g12(r): d=r[12:]-r[:-12]; return d[np.isfinite(d)]
crows=np.array([fx[b] for b in clean_ctrl if b in fx])
cpg=np.array([np.nanmean(g12(LE[r])) if g12(LE[r]).size else np.nan for r in crows]); c0=fmed[crows]
ok=np.isfinite(c0)&np.isfinite(cpg); crows=crows[ok]; c0=c0[ok]; cpg=cpg[ok]
Xc=np.column_stack([c0,c0**2,cpg,[cap(fsido.get(idx[r],"0")) for r in crows],[man(find.get(idx[r],"99")) for r in crows]])
T=pd.read_csv(f"{RE}/treatment_master_v2.csv",dtype=str); T["k"]=T["k"].str.replace(r'\D','',regex=True).str.zfill(10)
T["ev"]=parse_dates(T.event_dt,label="event_dt").dt.to_period("M"); T=T.dropna(subset=["ev"]).drop_duplicates("k")
CF=pd.read_csv(f"{OUT}/confound_flags.csv",dtype=str); CF["k"]=CF.k.str.zfill(10)
CF["cats_l"]=CF.cats.fillna("")
clean_broad=set(CF[CF.confounded=="0"].k)
clean_narrow=set(CF[~CF.cats_l.apply(lambda x: any(c and c!="지배구조" for c in x.split("|")))].k)
print(f"비오염 광의 {len(clean_broad)} · 협의 {len(clean_narrow)}",flush=True)
def run(sub,label):
    rec=[]
    for r in sub.itertuples():
        if r.k not in fx: continue
        e=mi.get(r.ev)
        if e is None or e-13<0 or e+12>=NM: continue
        row=LE[fx[r.k]]
        if not(np.isfinite(row[e-1]) and np.isfinite(row[e-13])): continue
        if sum(np.isfinite(row[e-j]) for j in range(1,4))<3 or sum(np.isfinite(row[e+j]) for j in range(1,13))<3: continue
        rec.append(dict(fi=fx[r.k],e=e,ls=np.nanmean([row[e-j] for j in range(1,4)]),pg=row[e-1]-row[e-13],cp=cap(fsido.get(r.k,"0")),mn=man(find.get(r.k,"99"))))
    Tm=pd.DataFrame(rec)
    if len(Tm)<30: print(f"{label}: n<30 skip"); return None
    Xt=np.column_stack([Tm.ls,Tm.ls**2,Tm.pg,Tm.cp,Tm.mn])
    X=np.vstack([Xt,Xc]); y=np.r_[np.ones(len(Xt)),np.zeros(len(Xc))]; Xs=(X-X.mean(0))/X.std(0)
    lg=sm.Logit(y,sm.add_constant(Xs)).fit(disp=0); xb=np.asarray(lg.predict(sm.add_constant(Xs),which="linear"))
    xbt=xb[:len(Xt)]; xbc=xb[len(Xt):]
    lo,hi=xbt.min(),xbt.max(); sup=(xbc>=lo)&(xbc<=hi); CS0=crows[sup]; xs0=xbc[sup]; calp=0.2*np.std(xb); K=50
    o=np.argsort(xs0); XS=xs0[o]; CS=CS0[o]
    D=[]; Z=[]
    for ii,r in enumerate(Tm.itertuples()):
        p=np.searchsorted(XS,xbt[ii]); cd=list(range(max(0,p-K-2),min(len(XS),p+K+2)))
        dd=np.abs(XS[cd]-xbt[ii]); sel=np.argsort(dd)[:K]
        m=[CS[cd[s]] for s in sel if dd[s]<=calp]
        if not m: continue
        e=r.e; bc=list(range(e-12,e)); bt=np.nanmean(LE[r.fi,bc])
        if np.sum(np.isfinite(LE[r.fi,bc]))<6 or not np.isfinite(bt): continue
        pj=list(range(e+1,e+13)); v=LE[r.fi,pj]
        if np.sum(np.isfinite(v))<3: continue
        own=float(np.nanmean(v)-bt)
        dc=[np.nanmean(LE[c,pj])-np.nanmean(LE[c,bc]) for c in m if np.isfinite(np.nanmean(LE[c,bc])) and np.sum(np.isfinite(LE[c,pj]))>=3]
        if len(dc)<3: continue
        D.append(own-np.mean(dc))
        Z.append((1.0 if own<=-0.35 else 0.0)-np.mean([1.0 if x<=-0.35 else 0.0 for x in dc]))
    D=np.array(D); Z=np.array(Z)
    def ci(a):
        bs=np.array([np.mean(a[RNG.integers(0,len(a),len(a))]) for _ in range(3000)])
        return round(float(a.mean()),4),[round(float(np.percentile(bs,2.5)),4),round(float(np.percentile(bs,97.5)),4)]
    m_,mci=ci(D); z_,zci=ci(Z)
    out=dict(n=len(D),mean=m_,mean_ci=mci,median=round(float(np.median(D)),4),p10=round(float(np.percentile(D,10)),4),
             collapse_035=z_,collapse_ci=zci)
    print(f"{label}: {out}",flush=True)
    return out
print("=== (b) 고용 ===")
res=dict(all=run(T,"전체"),
         clean_broad=run(T[T.k.isin(clean_broad)],"비오염(광의)"),
         clean_narrow=run(T[T.k.isin(clean_narrow)],"비오염(협의)"))
prev=json.load(open(f"{OUT}/wp11o_confound.json"))
prev["employment"]=res
json.dump(prev,open(f"{OUT}/wp11o_confound.json","w"),ensure_ascii=False,indent=1)
open(f"{OUT}/wp11p.done","w").write("done")
print("\n=== WP11p 완료 ===")
