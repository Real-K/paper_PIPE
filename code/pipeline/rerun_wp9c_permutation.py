# WP13 재실행 사본 (2026-08-26): 정규화 마스터(382 dated)로 동일 코드 재실행. 원본 wp9c_permutation.py · 출력 폴더만 pipe_wp13_2026-08-26 으로 치환.
# -*- coding: utf-8 -*-
"""P-016 WP9c — fan-out permutation 벤치마크. pair-diff 분위는 엄밀 QTE가 아니므로,
대조군 pseudo-event로 '무처치 분포'를 만들어 실제 처치 분위(p10..p90)·비대칭·spread가 노이즈 초과인지 검정.
설계: pseudo-처치 = 지지대조에서 propensity-odds 가중 추출, 이벤트월 = 처치 분포에서 추출.
동일 추정기(avg7-12, base12, 50NN 대조평균 차감). 풀 20k → n=205 표본 2000회 → null 분위 분포.
산출: shared/outputs/pipe_wp13_2026-08-26/wp9c_permutation.json
"""
import os,json,warnings; warnings.filterwarnings("ignore")
import numpy as np,pandas as pd
import statsmodels.api as sm
BASE=os.environ.get("P016_BASE", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))   # 원 경로는 제거했다 — 실행 시 P016_BASE 로 지정하거나 기본값 사용
RE=f"{BASE}/shared/outputs/pipe_r1_reextract_2026-08-22"
OUT=f"{BASE}/shared/outputs/pipe_wp13_2026-08-26"
RNG=np.random.default_rng(20260823)
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
# 처치 usable (wp9a와 동일 규칙)
rec=[]
for r in T.itertuples():
    if r.k not in firm_ix: continue
    fi=firm_ix[r.k]; e=mi.get(r.ev)
    if e is None: continue
    row=LE[fi]; pre=[e-j for j in range(1,4) if 0<=e-j<NM]
    if sum(np.isfinite(row[i]) for i in pre)<3: continue
    if sum(np.isfinite(row[e+j]) for j in range(1,13) if 0<=e+j<NM)<3: continue
    if not(0<=e-1<NM and 0<=e-13<NM and np.isfinite(row[e-1]) and np.isfinite(row[e-13])): continue
    rec.append(dict(k=r.k,fi=fi,e=e,logsize=np.nanmean([row[i] for i in pre]),pregrowth=row[e-1]-row[e-13],cap=cap(firm_sido.get(r.k,"0")),man=man(firm_ind.get(r.k,"99"))))
Tm=pd.DataFrame(rec)
crows=np.array([i for i,b in enumerate(idx) if (b not in pbbn) and (b not in tb)])
cpg=np.array([np.nanmean(g12(LE[r])) if g12(LE[r]).size else np.nan for r in crows]); cls=firm_med[crows]
ok=np.isfinite(cls)&np.isfinite(cpg); crows=crows[ok]; cls=cls[ok]; cpg=cpg[ok]
ccap=np.array([cap(firm_sido.get(idx[r],"0")) for r in crows]); cman=np.array([man(firm_ind.get(idx[r],"99")) for r in crows])
Xt=np.column_stack([Tm.logsize,Tm.logsize**2,Tm.pregrowth,Tm.cap,Tm.man]); Xc=np.column_stack([cls,cls**2,cpg,ccap,cman])
X=np.vstack([Xt,Xc]); y=np.r_[np.ones(len(Xt)),np.zeros(len(Xc))]; Xs=(X-X.mean(0))/X.std(0)
psm=sm.Logit(y,sm.add_constant(Xs)).fit(disp=0); xb=psm.predict(sm.add_constant(Xs),linear=True); xbt=xb[:len(Xt)]; xbc=xb[len(Xt):]
lo,hi=xbt.min(),xbt.max(); supp=(xbc>=lo)&(xbc<=hi)
cr=crows[supp]; xbcs=xbc[supp]
o=np.argsort(xbcs); XS=xbcs[o]; CS=cr[o]                 # 정렬된 지지대조
pos_of={c:i for i,c in enumerate(CS)}
calp=0.2*np.std(xb); K=50
print(f"처치 {len(Tm)} · 지지대조 {len(CS)}",flush=True)
# 이벤트월별 변화 벡터 (전 firm): CHG_e = mean(LE[:,e+7..e+12]) - mean(LE[:,e-12..e-1]), 유효성 카운트 포함
uniq_e=sorted(set(Tm.e))
CHG={}; VALID={}
for e in uniq_e:
    if e-12<0 or e+12>=NM: CHG[e]=None; VALID[e]=None; continue
    pre=LE[:,e-12:e]; post=LE[:,e+7:e+13]
    pc=np.sum(np.isfinite(pre),1); qc=np.sum(np.isfinite(post),1)
    chg=np.nanmean(post,1)-np.nanmean(pre,1)
    val=(pc>=6)&(qc>=3)&np.isfinite(chg)
    CHG[e]=chg; VALID[e]=val
def nn_ctrl(c_row,K):
    # c_row의 xb 위치 기준 최근접 K 대조 (자기 제외)
    i=pos_of.get(c_row)
    if i is None: return []
    lo_i=max(0,i-K-2); hi_i=min(len(CS),i+K+3)
    cand=[j for j in range(lo_i,hi_i) if j!=i and abs(XS[j]-XS[i])<=calp]
    cand.sort(key=lambda j:abs(XS[j]-XS[i]))
    return [CS[j] for j in cand[:K]]
def d_of(row,e,neigh):
    if CHG[e] is None or not VALID[e][row]: return np.nan
    nb=[c for c in neigh if VALID[e][c]]
    if len(nb)<3: return np.nan
    return CHG[e][row]-np.mean(CHG[e][nb])
# 실제 처치 분위 (E 사양 재현: 처치의 50NN은 대조에서)
def nn_treat(xi,K):
    p=np.searchsorted(XS,xi); cand=list(range(max(0,p-K-2),min(len(XS),p+K+2)))
    dd=np.abs(XS[cand]-xi); sel=np.argsort(dd)[:K]
    return [CS[cand[s]] for s in sel if dd[s]<=calp]
d_act=[]
for ii,r in enumerate(Tm.itertuples()):
    if CHG.get(r.e) is None: continue
    v=d_of(r.fi,r.e,nn_treat(xbt[ii],K)) if VALID[r.e][r.fi] else np.nan
    if np.isfinite(v): d_act.append(v)
d_act=np.array(d_act); n_act=len(d_act)
QL=[10,25,50,75,90]
act_q={q:float(np.percentile(d_act,q)) for q in QL}
act_stats=dict(**{f"p{q}":round(act_q[q],4) for q in QL},
               asym_1090=round(act_q[10]+act_q[90],4),asym_2575=round(act_q[25]+act_q[75],4),
               spread_1090=round(act_q[90]-act_q[10],4))
print("실제:",act_stats,"n=",n_act,flush=True)
# pseudo 풀: propensity-odds 가중 대조 추출 × 처치 이벤트월 분포
w=np.exp(XS-XS.max()); w=w/w.sum()
ev_pool=[e for e in Tm.e if CHG.get(e) is not None]
NP=20000
pool=[]
neigh_cache={}
tries=0
while len(pool)<NP and tries<NP*4:
    tries+=1
    ci=RNG.choice(len(CS),p=w); c=CS[ci]; e=ev_pool[RNG.integers(0,len(ev_pool))]
    if c not in neigh_cache: neigh_cache[c]=nn_ctrl(c,K)
    v=d_of(c,e,neigh_cache[c])
    if np.isfinite(v): pool.append(v)
    if len(pool)%5000==0 and len(pool)>0 and tries%1000==0: pass
pool=np.array(pool); print(f"pseudo 풀 {len(pool)} (시도 {tries})",flush=True)
# null 분포: n_act 크기 표본 2000회
R=2000
null={f"p{q}":[] for q in QL}; null["asym_1090"]=[]; null["asym_2575"]=[]; null["spread_1090"]=[]
for _ in range(R):
    s=pool[RNG.integers(0,len(pool),n_act)]
    qs={q:np.percentile(s,q) for q in QL}
    for q in QL: null[f"p{q}"].append(qs[q])
    null["asym_1090"].append(qs[10]+qs[90]); null["asym_2575"].append(qs[25]+qs[75]); null["spread_1090"].append(qs[90]-qs[10])
out={"n_act":n_act,"pool":int(len(pool)),"actual":act_stats,"null":{},"pvals":{}}
for k_,v in null.items():
    v=np.array(v); a=act_stats[k_] if k_ in act_stats else None
    out["null"][k_]=dict(mean=round(float(v.mean()),4),ci=[round(float(np.percentile(v,2.5)),4),round(float(np.percentile(v,97.5)),4)])
    if k_.startswith("p") or k_.startswith("asym"):  # 좌측 초과(음) 검정: P(null <= actual)
        out["pvals"][k_+"_left"]=round(float(np.mean(v<=act_stats[k_])),4)
        out["pvals"][k_+"_right"]=round(float(np.mean(v>=act_stats[k_])),4)
    else:
        out["pvals"][k_+"_ge"]=round(float(np.mean(v>=act_stats[k_])),4)
json.dump(out,open(f"{OUT}/wp9c_permutation.json","w"),ensure_ascii=False,indent=1)
open(f"{OUT}/wp9c.done","w").write("done")
print("\n=== WP9c 완료 ===")
for q in QL: print(f"p{q}: 실제 {act_stats[f'p{q}']:+.4f} · null {out['null'][f'p{q}']['mean']:+.4f} {out['null'][f'p{q}']['ci']} · P(null≤실제)={out['pvals'][f'p{q}_left']}")
print(f"asym1090: 실제 {act_stats['asym_1090']:+.4f} · null {out['null']['asym_1090']['mean']:+.4f} {out['null']['asym_1090']['ci']} · P(null≤실제)={out['pvals']['asym_1090_left']}")
print(f"asym2575: 실제 {act_stats['asym_2575']:+.4f} · null {out['null']['asym_2575']['mean']:+.4f} {out['null']['asym_2575']['ci']} · P(null≤실제)={out['pvals']['asym_2575_left']}")
print(f"spread1090: 실제 {act_stats['spread_1090']:+.4f} · null {out['null']['spread_1090']['mean']:+.4f} {out['null']['spread_1090']['ci']} · P(null≥실제)={out['pvals']['spread_1090_ge']}")
