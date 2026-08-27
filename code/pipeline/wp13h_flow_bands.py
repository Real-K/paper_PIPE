# -*- coding: utf-8 -*-
"""WP13h — C-E(조정 마진 차이검정) + C-B(등가밴드 민감도).

C-E. 원고 §5.5 는 "채용 동결이 마진" 이라고 읽히지만, 지금까지 보고된 것은 채용 ATT 와 이탈 ATT **각각의**
신뢰구간뿐이다. 둘 다 0 을 포함하면 "채용이 마진" 이라는 서술은 근거가 없다. 필요한 것은 **차이 β_hire − β_sep 의
검정**이고, 두 통계량이 같은 기업에서 나오므로 **동일 재표본으로 짝지어(joint) 부트스트랩**해야 상관을 반영한다.
함께 (i) 회계 항등식(누적채용 − 누적이탈 ≈ 고용변화)이 자료에서 성립하는지 (ii) 꼬리/비꼬리 분리 를 본다.
기각조건: 차이 CI 가 0 을 포함하면 §5.5 를 "두 마진을 구분할 검정력이 없다" 로 강등(원고가 이미 그 방향).

C-B. 꼬리 등가성은 사전 고정 밴드 ±5pp 로 판정했다. 밴드를 ±3/±5/±7.5pp 로 바꿔도 결론이 유지되는지 본다.
규칙 11 에 따라 판정은 **CI ⊂ 밴드** 로만 하고, knife-edge(여유 <0.1pp)는 배제로 쓰지 않는다.
"""
# -*- coding: utf-8 -*-
"""P-016 WP6 — robustness + 메커니즘. 헤드라인 PSM v2 재현 후:
(A) gross-flow 분해: 신규(채용)/상실(이탈) ATT+12 → 채용동결 vs 이탈증가 채널.
(B) Rosenbaum Γ bounds: +12 pair difference 부호랭크 민감도 → Γ*.
(C) placebo: 주주배정/공모 비처치 유상증자 6사 동일설계 → 위(僞)효과 점추정+CI(rule11).
(D) 표본임계 민감도: >=1/>=1, >=6/>=6.
SESOI 동결 0.0559 재사용. 산출: shared/outputs/pipe_wp13_2026-08-26/wp6_robust.json
"""
import os,json,warnings,math; warnings.filterwarnings("ignore")
import numpy as np,pandas as pd
import statsmodels.api as sm
BASE=os.environ.get("P016_BASE", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))   # 원 경로는 제거했다 — 실행 시 P016_BASE 로 지정하거나 기본값 사용
RE=f"{BASE}/shared/outputs/pipe_r1_reextract_2026-08-22"
OUT=f"{BASE}/shared/outputs/pipe_wp13_2026-08-26"; os.makedirs(OUT,exist_ok=True)
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
T=T[pd.to_numeric(T.event_dt.astype(str).str[:4],errors="coerce").between(2015,2025)]   # 표본기간 2015–2025(원고 명시) — WP13, 2026-08-27
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


import json as _json
print("=== C-E 조정 마진 ===",flush=True)
Tm=build_treated(T,3,3); matches,Xt=psm_match(Tm)
c_le=es_att(Tm,matches,LE,None,None,False)
c_h =es_att(Tm,matches,HIRE,None,None,True)
c_s =es_att(Tm,matches,SEP ,None,None,True)
ok=np.where(np.isfinite(c_h)&np.isfinite(c_s))[0]
print(f"채용·이탈 동시 관측 {len(ok)} / 처치 {len(Tm)}",flush=True)
def pair_boot(a,b,idx,B=4000):
    """같은 재표본으로 두 통계량을 동시에 계산 — 차이의 SE 가 상관을 반영한다."""
    da,db=a[idx],b[idx]; obs=(float(np.mean(da)),float(np.mean(db)),float(np.mean(da-db)))
    bs=np.array([[np.mean(da[j]),np.mean(db[j]),np.mean((da-db)[j])] for j in (RNG.integers(0,len(idx),len(idx)) for _ in range(B))])
    out={}
    for k,lab in enumerate(("hire","sep","diff")):
        lo,hi=np.percentile(bs[:,k],[2.5,97.5])
        out[lab]=dict(obs=round(obs[k],4),ci=[round(float(lo),4),round(float(hi),4)],
                      sd=round(float(bs[:,k].std(ddof=1)),4),sig=bool(lo>0 or hi<0))
    out["corr_hire_sep"]=round(float(np.corrcoef(bs[:,0],bs[:,1])[0,1]),3); out["n"]=int(len(idx))
    return out
R={}
R["E_flow_all"]=pair_boot(c_h,c_s,ok)
r=R["E_flow_all"]
for lab in ("hire","sep","diff"):
    e=r[lab]; print(f"  {lab:<5} {e['obs']:+.4f} {e['ci']} {'유의' if e['sig'] else '비유의'}",flush=True)
print(f"  부트 상관(채용,이탈) {r['corr_hire_sep']:+.3f} · n={r['n']}",flush=True)
# (i) 회계 항등식: (누적채용 − 누적이탈)/base 와 고용 변화율 비교 (처치기업 원자료)
idn=[]
for ii,rr in enumerate(Tm.itertuples()):
    e=rr.e; base=np.nanmean([EMP[rr.fi,e-j] for j in range(1,PRE+1) if 0<=e-j<len(months)])
    post=[e+j for j in range(1,POST+1) if 0<=e+j<len(months)]
    if not np.isfinite(base) or base<=0 or e+POST>=len(months): continue
    lvl=EMP[rr.fi,e+POST]
    if not np.isfinite(lvl): continue
    net=(np.nansum([HIRE[rr.fi,p] for p in post])-np.nansum([SEP[rr.fi,p] for p in post]))/base
    idn.append((net,(lvl-base)/base))
idn=np.array(idn)
R["E_identity"]=dict(n=int(len(idn)),corr=round(float(np.corrcoef(idn[:,0],idn[:,1])[0,1]),4),
                     mean_abs_gap=round(float(np.mean(np.abs(idn[:,0]-idn[:,1]))),4),
                     median_abs_gap=round(float(np.median(np.abs(idn[:,0]-idn[:,1]))),4),
                     note="net flow=(cum hire − cum sep)/base 와 (E_{+12}−base)/base 의 일치도. 사업장 이동·자료 갱신으로 완전일치는 기대하지 않는다.")
q=R["E_identity"]; print(f"  항등식 점검 n={q['n']} 상관 {q['corr']:.4f} · |격차| 평균 {q['mean_abs_gap']:.4f} 중위 {q['median_abs_gap']:.4f}",flush=True)
# (ii) 꼬리/비꼬리 분리
fin=np.where(np.isfinite(c_le))[0]; cut25=np.percentile(c_le[fin],25)
tail_mask=np.zeros(len(c_le),bool); tail_mask[fin]=c_le[fin]<=cut25
for lab,sel in (("tail",np.array([i for i in ok if tail_mask[i]])),("non_tail",np.array([i for i in ok if not tail_mask[i]]))):
    if len(sel)<15: print(f"  {lab}: 표본부족 {len(sel)}"); continue
    R[f"E_flow_{lab}"]=pair_boot(c_h,c_s,sel); e=R[f"E_flow_{lab}"]
    print(f"  {lab:<9} n={e['n']:>3} hire {e['hire']['obs']:+.4f}{e['hire']['ci']} · sep {e['sep']['obs']:+.4f}{e['sep']['ci']} · diff {e['diff']['obs']:+.4f}{e['diff']['ci']} {'유의' if e['diff']['sig'] else '비유의'}",flush=True)

print("\n=== C-B 등가밴드 민감도 (꼬리, 유사시점) ===",flush=True)
fg=_json.load(open(f"{BASE}/shared/outputs/pipe_wp13_2026-08-26/wp11fg.json"))
grid=fg["g_placebo_grid"]; ev_tail=fg["f_honest"]["tail"]["effect"]; ev_ci=fg["f_honest"]["tail"]["grid"][0]["ci"]
BANDS=[0.03,0.05,0.075]; S={}
for bnd in BANDS:
    row={}
    for k,v in grid.items():
        lo,hi=v["tail_ci"]; inside=bool(lo>=-bnd and hi<=bnd)
        margin=round(float(min(bnd-abs(lo),bnd-abs(hi))),4)
        row[k]=dict(tail=v["tail"],ci=[lo,hi],equiv=inside,margin=margin,knife_edge=bool(inside and margin<0.001))
    row["event"]=dict(tail=ev_tail,ci=ev_ci,equiv=bool(ev_ci[0]>=-bnd and ev_ci[1]<=bnd),
                      margin=round(float(min(bnd-abs(ev_ci[0]),bnd-abs(ev_ci[1]))),4))
    S[f"band_{bnd}"]=row
    n_eq=sum(1 for k in grid if row[k]["equiv"]); ke=[k for k in grid if row[k]["knife_edge"]]
    print(f"  ±{bnd*100:.1f}pp: 유사시점 등가 {n_eq}/4 · 이벤트 등가 {row['event']['equiv']} · 최소여유 {min(row[k]['margin'] for k in grid):+.4f}"
          + (f" · knife-edge {ke}" if ke else ""),flush=True)
R["B_band_sensitivity"]=S
verdict=(f"C-E: 채용 {r['hire']['obs']}{r['hire']['ci']} · 이탈 {r['sep']['obs']}{r['sep']['ci']} · "
         f"차이 {r['diff']['obs']}{r['diff']['ci']} → {'구분됨' if r['diff']['sig'] else '두 마진 구분 불가(exploratory 강등)'}. "
         f"C-B: 꼬리 등가성 밴드 ±3/5/7.5pp 에서 유사시점 등가 "
         + "/".join(str(sum(1 for k in grid if S[f'band_{b}'][k]['equiv'])) for b in BANDS) + "/4.")
_json.dump({"id":"WP13h","title":"조정 마진 차이검정(C-E)·등가밴드 민감도(C-B)","runs":R,"verdict":verdict,
  "design":"채용/이탈 ATT 는 wp6 와 동일 구성(누적 flow/사전 고용, k-NN PSM). 차이는 **동일 재표본 짝 부트(B=4000)** 로 상관 반영.",
  "kill":"차이 CI 가 0 포함 → §5.5 를 '두 마진을 구분할 검정력 없음' 으로 강등"},
  open(f"{BASE}/shared/outputs/pipe_wp13_2026-08-26/wp13h_flow_bands.json","w"),ensure_ascii=False,indent=1)
print("\n"+verdict,flush=True)
