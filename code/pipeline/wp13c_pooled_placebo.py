# -*- coding: utf-8 -*-
"""WP13c — 유사시점 통합 대조: 검정력 회복 + 군집추론 + 공통표본.

동기. C-A5(clean pool 통일)로 wp10f 의 placebo 표본이 158→142 로 줄면서 꼬리 대조의 CI 상단이
−0.129 → −0.095 로 밀렸다. 결과는 여전히 0 을 배제하지만, 이 손실은 **설계로 되돌릴 수 있다**:
논문은 이미 t−36/−30/−24/−18 네 유사시점을 쓰는데 공식 대조는 t−24 하나만 쓰고 있었다.

세 가지를 한 번에 고친다.
  (A) 유사시점 **통합** — 네 시점의 매칭쌍 결과를 모아 귀무분포를 만든다. 표본이 ~4배가 되어
      귀무 쪽 추정오차가 줄고, 특정 시점 선택에 의존하지 않는다.
  (B) **기업 군집 부트스트랩** — 한 기업이 최대 5개(실제+유사4) 관측을 내므로 iid 재표본은
      과소 SE 를 준다. 기업 단위로 재표본해 양쪽 팔의 의존성을 반영한다(wp10f 의 iid 보다 보수적).
  (C) **공통표본** — 실제와 네 유사시점 **전부**에서 관측되는 기업만으로 다시 계산한다.
      "시점마다 표본이 달라 비교가 아니다" 라는 지적(리뷰1 C-B)을 원천 차단한다.

사전 예측. 통합으로 p10 대조의 CI 폭이 좁아진다(점추정은 크게 안 변함). 군집 부트는 CI 를 넓힌다.
둘의 순효과가 관건이며, 공통표본에서도 부호·유의가 유지되어야 한다.
기각조건. 통합·군집 기준으로 p10 대조 CI 가 0 을 포함하면 "이벤트 고유 꼬리" 주장을 t−24 단독 대조로
축소 서술해야 한다(주장 철회가 아니라 근거 범위 축소).
"""
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

SHIFTS=[18,24,30,36]
CACHE=f"{OUT}/wp13c_dvec_cache.csv"
if os.path.exists(CACHE):
    A=pd.read_csv(CACHE,dtype={"k":str}); ev=A[A.sh==0].copy(); pl=A[A.sh!=0].copy()
    print(f"캐시 사용 {CACHE}",flush=True)
else:
    print(f"처치 {len(T)} · 유사시점 {SHIFTS}",flush=True)
    Ta=build(0); Da=dvec(Ta)
    ev=pd.DataFrame({"k":Ta.k.values,"d":Da,"sh":0}).dropna(subset=["d"])
    pls=[]
    for s in SHIFTS:
        Ts=build(s); Ds=dvec(Ts)
        p=pd.DataFrame({"k":Ts.k.values,"d":Ds,"sh":s}).dropna(subset=["d"]); pls.append(p)
        print(f"  placebo t−{s}: n={len(p)}",flush=True)
    pl=pd.concat(pls,ignore_index=True)
    pd.concat([ev,pl],ignore_index=True).to_csv(CACHE,index=False)
print(f"event n={len(ev)} · placebo 통합 n={len(pl)} (기업 {pl.k.nunique()})",flush=True)

def stats(a,b):
    return dict(mean=float(np.mean(a)-np.mean(b)),median=float(np.median(a)-np.median(b)),
                p10=float(np.percentile(a,10)-np.percentile(b,10)),p25=float(np.percentile(a,25)-np.percentile(b,25)))
def boot(EV,PL,B=4000,cluster=True):
    a0,b0=EV.d.values,PL.d.values; obs=stats(a0,b0)
    if cluster:
        firms=np.array(sorted(set(EV.k)|set(PL.k)))
        ei={f:EV.index[EV.k==f].to_numpy() for f in firms}; pi={f:PL.index[PL.k==f].to_numpy() for f in firms}
        bs=[]
        for _ in range(B):
            fs=firms[RNG.integers(0,len(firms),len(firms))]
            ia=np.concatenate([ei[f] for f in fs if len(ei[f])]); ib=np.concatenate([pi[f] for f in fs if len(pi[f])])
            if len(ia)<20 or len(ib)<20: continue
            bs.append(stats(EV.d.values[EV.index.get_indexer(ia)],PL.d.values[PL.index.get_indexer(ib)]))
    else:
        bs=[stats(a0[RNG.integers(0,len(a0),len(a0))],b0[RNG.integers(0,len(b0),len(b0))]) for _ in range(B)]
    out={}
    for k in obs:
        v=np.array([x[k] for x in bs]); lo,hi=np.percentile(v,[2.5,97.5])
        out[k]=dict(obs=round(obs[k],4),ci=[round(float(lo),4),round(float(hi),4)],sig=bool(lo>0 or hi<0),sd=round(float(v.std(ddof=1)),4))
    out["n_event"]=int(len(EV)); out["n_placebo"]=int(len(PL)); out["n_boot"]=len(bs)
    out["n_event_firms"]=int(EV.k.nunique()); out["n_placebo_firms"]=int(PL.k.nunique())   # Panel A 헤더 인용용
    return out
R={}
R["A_pooled_cluster"]=boot(ev.reset_index(drop=True),pl.reset_index(drop=True),cluster=True)
R["A_pooled_iid"]=boot(ev.reset_index(drop=True),pl.reset_index(drop=True),cluster=False)
R["B_t24_cluster"]=boot(ev.reset_index(drop=True),pl[pl.sh==24].reset_index(drop=True),cluster=True)
common=set(ev.k)
for s in SHIFTS: common&=set(pl[pl.sh==s].k)
evc=ev[ev.k.isin(common)].reset_index(drop=True); plc=pl[pl.k.isin(common)].reset_index(drop=True)
R["C_common_pooled_cluster"]=boot(evc,plc,cluster=True) if len(evc)>=30 else None
R["C_common_n_firms"]=len(common)
for s in SHIFTS:
    p=pl[pl.sh==s].reset_index(drop=True)
    R[f"D_t{s}_only"]=boot(ev.reset_index(drop=True),p,cluster=True) if len(p)>=30 else None
def line(k,r):
    if not r: print(f"  {k:<26} 표본부족"); return
    print(f"  {k:<26} n {r['n_event']}/{r['n_placebo']} · mean {r['mean']['obs']:+.4f}{r['mean']['ci']}{'✓' if r['mean']['sig'] else '✗'}"
          f" · median {r['median']['obs']:+.4f}{'✓' if r['median']['sig'] else '✗'}"
          f" · p10 {r['p10']['obs']:+.4f}{r['p10']['ci']}{'✓' if r['p10']['sig'] else '✗'}"
          f" · p25 {r['p25']['obs']:+.4f}{'✓' if r['p25']['sig'] else '✗'}",flush=True)
print("\n=== WP13c ===")
for k in ("A_pooled_cluster","A_pooled_iid","B_t24_cluster","C_common_pooled_cluster","D_t18_only","D_t24_only","D_t30_only","D_t36_only"):
    if k in R: line(k,R[k])
a=R["A_pooled_cluster"]["p10"]; b=R["B_t24_cluster"]["p10"]
verdict=(f"통합·군집 p10 {a['obs']}{a['ci']}{'유의' if a['sig'] else '비유의'} vs t−24 단독·군집 {b['obs']}{b['ci']}. "
         f"CI 폭 {round(a['ci'][1]-a['ci'][0],4)} vs {round(b['ci'][1]-b['ci'][0],4)}. "
         f"공통표본 {R['C_common_n_firms']}사.")
json.dump({"id":"WP13c","title":"유사시점 통합 대조(검정력 회복·군집추론·공통표본)","shifts":SHIFTS,"runs":R,"verdict":verdict,
           "design":"매칭쌍 결과는 wp10f 와 동일 구성(clean pool·k50 캘리퍼 매칭·처치 210 고정). 차이는 (A)유사시점 통합 (B)기업 군집 부트 (C)공통표본.",
           "kill":"통합·군집 p10 CI 가 0 포함 → 이벤트 고유 꼬리 주장을 t−24 단독 대조로 축소 서술"},
          open(f"{OUT}/wp13c_pooled_placebo.json","w"),ensure_ascii=False,indent=1)
print("\n"+verdict)
