# WP13 재실행 사본 (2026-08-26): 정규화 마스터(382 dated)로 동일 코드 재실행. 원본 wp10c_listed_pool.py · 출력 폴더만 pipe_wp13_2026-08-26 으로 치환.
# -*- coding: utf-8 -*-
"""P-016 WP10c — 식별 referee fix 1: 상장-전용 대조풀 재구축 + 헤드라인·SESOI·permutation 재실행.
대조 = NPS ∩ 상장(재무통합CSV 코드=A+티커 보유 bn) − 처치 − PitchBook-touched.
(비스폰서 제3자배정 잔존 가능 → 오염방향=귀무 쪽(보수적), 명시. 완전 purge는 후속 DART 전수 필요.)
재산출: SESOI(상장대조 사전 12m logΔ SD×0.2) · avg(+1..+12)/base12 ATT · 사전추세 등가 · 좌측꼬리 permutation.
산출: shared/outputs/pipe_wp13_2026-08-26/wp10c_listed.json
"""
import os,json,csv,re,warnings; warnings.filterwarnings("ignore")
import numpy as np,pandas as pd
import statsmodels.api as sm
BASE=os.environ.get("P016_BASE", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))   # 원 경로는 제거했다 — 실행 시 P016_BASE 로 지정하거나 기본값 사용
RE=f"{BASE}/shared/outputs/pipe_r1_reextract_2026-08-22"
OUT=f"{BASE}/shared/outputs/pipe_wp13_2026-08-26"
RNG=np.random.default_rng(20260823)
# --- 상장 bn 우주 (재무통합 CSV 스트리밍: 코드 A+6자리 & 사업자번호) ---
listed=set()
with open(f"{BASE}/PI/drops/재무데이터_2009_2025_통합.csv",encoding='utf-8') as f:
    rd=csv.reader(f); next(rd)
    for row in rd:
        if len(row)<6: continue
        code=row[0].lstrip('﻿')
        if re.match(r'^A\d{6}$',code):
            bn=re.sub(r'\D','',row[5]).zfill(10)
            if len(bn)==10 and bn!="0000000000": listed.add(bn)
print(f"상장 bn 우주 {len(listed)}",flush=True)
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
_cl=set(pd.read_csv(f"{BASE}/shared/outputs/pipe_wp13_2026-08-26/controls_clean.csv",dtype=str).query("third_hist=='False'").bn.str.replace(r"\D","",regex=True).str.zfill(10))  # WP13: clean pool 통일(C-A5)
ctrl_bn=[b for b in idx if (b in listed) and (b not in pbbn) and (b not in tb)]
ctrl_bn=[b for b in ctrl_bn if b in _cl]
print(f"상장-전용 대조풀 {len(ctrl_bn)} (구 51,568 대비)",flush=True)
crows=np.array([firm_ix[b] for b in ctrl_bn])
def cap(s): return 1.0 if str(s) in ("11","41","28") else 0.0
def man(i):
    try: return 1.0 if 10<=int(i)<=34 else 0.0
    except: return 0.0
def g12(r): d=r[12:]-r[:-12]; return d[np.isfinite(d)]
# --- SESOI 재보정 (상장대조 사전 12m logΔ SD) ---
alld=[g12(LE[r]) for r in crows]; allc=np.concatenate([a for a in alld if a.size]) if alld else np.array([0.])
sd12=float(np.std(allc,ddof=1)); SESOI=round(0.2*sd12,4)
print(f"SESOI(상장대조) = 0.2×{sd12:.4f} = {SESOI} (구 0.0559)",flush=True)
# --- 처치 usable + 매칭 (k50) ---
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
cpg=np.array([np.nanmean(g12(LE[r])) if g12(LE[r]).size else np.nan for r in crows]); cls=firm_med[crows]
okc=np.isfinite(cls)&np.isfinite(cpg); crows=crows[okc]; cls=cls[okc]; cpg=cpg[okc]
ccap=np.array([cap(firm_sido.get(idx[r],"0")) for r in crows]); cman=np.array([man(firm_ind.get(idx[r],"99")) for r in crows])
Xt=np.column_stack([Tm.logsize,Tm.logsize**2,Tm.pregrowth,Tm.cap,Tm.man]); Xc=np.column_stack([cls,cls**2,cpg,ccap,cman])
X=np.vstack([Xt,Xc]); y=np.r_[np.ones(len(Xt)),np.zeros(len(Xc))]; Xs=(X-X.mean(0))/X.std(0)
psm=sm.Logit(y,sm.add_constant(Xs)).fit(disp=0); xb=np.asarray(psm.predict(sm.add_constant(Xs),linear=True)); xbt=xb[:len(Xt)]; xbc=xb[len(Xt):]
lo,hi=xbt.min(),xbt.max(); supp=(xbc>=lo)&(xbc<=hi); CSr=crows[supp]; xbcs=xbc[supp]; calp=0.2*np.std(xb); K=50
o=np.argsort(xbcs); XS=xbcs[o]; CS=CSr[o]
print(f"처치 {len(Tm)} · 공통지지 상장대조 {len(CS)}",flush=True)
def knn_t(xi):
    p=np.searchsorted(XS,xi); cand=list(range(max(0,p-K-2),min(len(XS),p+K+2))); dd=np.abs(XS[cand]-xi); sel=np.argsort(dd)[:K]
    return [CS[cand[s]] for s in sel if dd[s]<=calp]
matches=[knn_t(x) for x in xbt]
# balance
def smd(a,b): return (np.nanmean(a,0)-np.nanmean(b,0))/np.sqrt((np.nanvar(a,0,ddof=1)+np.nanvar(b,0,ddof=1))/2)
cmap={r:j for j,r in enumerate(crows)}
mc=[c for m in matches for c in m]; Xmc=np.array([Xc[cmap[c]] for c in mc]) if mc else Xc[:1]
mx=float(np.abs(smd(Xmc,Xt)).max())
# --- event-study τ_k + avg estimand ---
KS=list(range(-12,13)); kidx={k:j for j,k in enumerate(KS)}
Cmat=np.full((len(Tm),len(KS)),np.nan); Davg=np.full(len(Tm),np.nan); D712=np.full(len(Tm),np.nan)
for ii,r in enumerate(Tm.itertuples()):
    m=matches[ii]
    if not m: continue
    e=r.e
    if e-12<0: continue
    bc=list(range(e-12,e)); bt_=np.nanmean(LE[r.fi,bc])
    if np.sum(np.isfinite(LE[r.fi,bc]))<6 or not np.isfinite(bt_): continue
    cb={c:np.nanmean(LE[c,bc]) for c in m}
    for k in KS:
        t=e+k
        if not(0<=t<NM) or not np.isfinite(LE[r.fi,t]): continue
        dc=[LE[c,t]-cb[c] for c in m if np.isfinite(cb[c]) and np.isfinite(LE[c,t])]
        if len(dc)<3: continue
        Cmat[ii,kidx[k]]=(LE[r.fi,t]-bt_)-np.mean(dc)
    pj=[kidx[k] for k in range(1,13)]; v=Cmat[ii,pj]
    if np.sum(np.isfinite(v))>=3: Davg[ii]=np.nanmean(v)
    pj2=[kidx[k] for k in range(7,13)]; v2=Cmat[ii,pj2]
    if np.sum(np.isfinite(v2))>=3: D712[ii]=np.nanmean(v2)
def bci(vec,fn=np.nanmean,B=2000):
    v=vec[np.isfinite(vec)]; n=len(v)
    bs=np.array([fn(v[RNG.integers(0,n,n)]) for _ in range(B)])
    return round(float(fn(v)),4),[round(float(np.percentile(bs,2.5)),4),round(float(np.percentile(bs,97.5)),4)],n
p_avg,ci_avg,n_avg=bci(Davg); p712,ci712,n712=bci(D712)
# 사전추세 등가 (재보정 SESOI)
valid=np.array([i for i in range(len(Tm)) if np.isfinite(Davg[i])])
def tau_of(rows): return np.array([np.nanmean(Cmat[rows,j]) for j in range(len(KS))])
tau=tau_of(valid); B_=300; boot=np.array([tau_of(valid[RNG.integers(0,len(valid),len(valid))]) for _ in range(B_)])
loci=np.nanpercentile(boot,2.5,0); hici=np.nanpercentile(boot,97.5,0)
npass=sum(1 for k in range(-12,0) if (loci[kidx[k]]>=-SESOI and hici[kidx[k]]<=SESOI))
print(f"ATT avg1-12={p_avg}{ci_avg} n={n_avg} · avg7-12={p712}{ci712} · balance {mx:.3f} · 사전추세 {npass}/12 (SESOI {SESOI})",flush=True)
# --- permutation (상장 pseudo-처치) ---
uniq_e=sorted(set(Tm.e)); CHG={}; VAL={}
for e in uniq_e:
    if e-12<0 or e+12>=NM: CHG[e]=None; continue
    pre=LE[:,e-12:e]; post=LE[:,e+7:e+13]
    pc=np.sum(np.isfinite(pre),1); qc=np.sum(np.isfinite(post),1)
    CHG[e]=np.nanmean(post,1)-np.nanmean(pre,1); VAL[e]=(pc>=6)&(qc>=3)&np.isfinite(CHG[e])
pos_of={c:i for i,c in enumerate(CS)}
def nn_c(c,K):
    i=pos_of.get(c)
    if i is None: return []
    cand=[j for j in range(max(0,i-K-2),min(len(CS),i+K+3)) if j!=i and abs(XS[j]-XS[i])<=calp]
    cand.sort(key=lambda j:abs(XS[j]-XS[i])); return [CS[j] for j in cand[:K]]
w=np.exp(XS-XS.max()); w=w/w.sum(); evp=[e for e in Tm.e if CHG.get(e) is not None]
# 실제 d (avg7-12) 분위
d_act=D712[np.isfinite(D712)]; n_act=len(d_act)
QL=[10,25,50,75,90]; actq={q:float(np.percentile(d_act,q)) for q in QL}
pool=[]; cache={}; tries=0
while len(pool)<15000 and tries<60000:
    tries+=1
    ci_=RNG.choice(len(CS),p=w); c=CS[ci_]; e=evp[RNG.integers(0,len(evp))]
    if CHG[e] is None or not VAL[e][c]: continue
    if c not in cache: cache[c]=nn_c(c,K)
    nb=[x for x in cache[c] if VAL[e][x]]
    if len(nb)<3: continue
    pool.append(CHG[e][c]-np.mean(CHG[e][nb]))
pool=np.array(pool); print(f"pseudo 풀 {len(pool)}",flush=True)
R_=2000; nullq={q:[] for q in QL}
for _ in range(R_):
    s=pool[RNG.integers(0,len(pool),n_act)]
    for q in QL: nullq[q].append(np.percentile(s,q))
perm={}
for q in QL:
    v=np.array(nullq[q]); perm[f"p{q}"]=dict(actual=round(actq[q],4),null_mean=round(float(v.mean()),4),
        null_ci=[round(float(np.percentile(v,2.5)),4),round(float(np.percentile(v,97.5)),4)],
        P_null_le_actual=round(float(np.mean(v<=actq[q])),4))
res=dict(id="P016-WP10c",listed_universe=len(listed),listed_ctrl_pool=int(len(ctrl_bn)),common_support=int(len(CS)),
         SESOI_listed=SESOI,sd12_listed=round(sd12,4),
         ATT_avg1_12=dict(point=p_avg,ci=ci_avg,n=n_avg),ATT_avg7_12=dict(point=p712,ci=ci712,n=n712),
         balance_max_abs_smd=round(mx,4),pretrend_pass=f"{npass}/12",permutation=perm,
         caveat="비스폰서 제3자배정 잔존 가능(오염방향=귀무쪽, 보수적). 완전 purge는 DART 전수 후속.")
json.dump(res,open(f"{OUT}/wp10c_listed.json","w"),ensure_ascii=False,indent=1)
open(f"{OUT}/wp10c.done","w").write("done")
print("\n=== WP10c 완료 ===")
for q in QL: print(f"p{q}: 실제 {perm[f'p{q}']['actual']:+.4f} null {perm[f'p{q}']['null_mean']:+.4f} {perm[f'p{q}']['null_ci']} P={perm[f'p{q}']['P_null_le_actual']}")
