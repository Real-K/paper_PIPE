# -*- coding: utf-8 -*-
"""WP12a — C-C 비교군 재설계 (리뷰1 §5.11 · Major Comment 2).

wp11c 의 세 결함을 고친다. 실행 전 예측·기각조건을 적어 둔다.

결함 1 (collider). eligibility 의 고용감소 조건 row[e-1] < row[e-13] 이 결과 D 의 기준선 bt=mean(row[e-12:e])
  과 창이 겹친다. 처치에는 없고 비교군에만 있는 비대칭 조건 → 비교군 D 를 기계적으로 위로 편향
  (하락 직후 기저에서 재는 셈). → 고용감소 조건을 **[−24,−13] 창**으로 옮기고 처치·비교군에 **대칭** 적용.
결함 2 (재무 미가중). 패널에 lev·roa·cash·impaired·loss 가 있는데 logsize·pg·year 만 가중. → 전부 투입.
결함 3 (반복 firm-event 독립 부트). 13,095 건이 765 기업 → **기업 군집 부트**.

사전 예측. 결함 1 교정은 비교군 D 를 **낮춘다**(하락 직후 기저 제거) → 처치 median 우위 축소,
p10 열위 축소 가능. 결함 2 는 비교군을 더 '처치 같은' 재무상태로 맞춰 양쪽 차이를 줄일 수 있다.
결함 3 은 CI 를 넓힌다. 세 방향 모두 **현 결과에 불리**하게 작용할 수 있다.

기각조건. 재설계 후 p10 차이 CI 가 0 을 포함하면 'tail 열위' 주장 철회. median 차이가 0 을 포함하면
'median 우위' 철회. 둘 다 철회되면 §5.4 는 'distressed 비수령과 구별되지 않음' 으로 다시 쓴다.

패널 A  wp11c 원설계 재현 (기준)
패널 B  결함별 단계 교정 — 1 만 · 1+2 · 1+2+3 (어느 결함이 결과를 움직이는지 분해)
패널 C  최종 설계 진단 — balance(SMD) · overlap · ESS · trimming 민감도
패널 D  최종 설계 결과 — mean · median · p10 · collapse curve(uniform) · 기업군집 부트
"""
import os,json,warnings; warnings.filterwarnings("ignore")
import numpy as np,pandas as pd
import statsmodels.api as sm
BASE=os.environ.get("P016_BASE", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))   # 원 경로는 제거했다 — 실행 시 P016_BASE 로 지정하거나 기본값 사용
RE=f"{BASE}/shared/outputs/pipe_r1_reextract_2026-08-22"
W11=f"{BASE}/shared/outputs/pipe_wp11_2026-08-23"
OUT=f"{BASE}/shared/outputs/pipe_wp12_2026-08-26"
RNG=np.random.default_rng(20260826)
B_CI=2000
CL=pd.read_csv(f"{W11}/controls_clean.csv",dtype={"bn":str}); clean=set(CL[CL.third_hist==False].bn)
FIN=pd.read_csv(f"{W11}/fin_distress_panel.csv",dtype={"bn":str})
fin={(r.bn,int(r.year)):(r.lev,r.roa,r.cash,int(r.impaired),int(r.loss)) for r in FIN.itertuples()}
def fin_asof(bn,yr):
    for y in (yr-1,yr-2):
        v=fin.get((bn,y))
        if v: return v
    return None
def is_distress(fv): return fv is not None and (fv[4]==1 or (fv[0]==fv[0] and fv[0]>2) or fv[3]==1)
nps=pd.read_parquet(f"{BASE}/shared/data/processed/nps_monthly_matched_v2.parquet",columns=["bn10","data_ym","가입자수"])
nps["ym"]=pd.PeriodIndex(nps["data_ym"],freq="M"); nps["le"]=np.log1p(nps["가입자수"].astype(float))
months=pd.period_range(nps.ym.min(),nps.ym.max(),freq="M"); mi={m:j for j,m in enumerate(months)}; NM=len(months)
piv=nps.pivot_table(index="bn10",columns="ym",values="le",aggfunc="mean").reindex(columns=months)
idx=list(piv.index); fx={b:i for i,b in enumerate(idx)}; LE=piv.to_numpy(float); del nps,piv
T=pd.read_csv(f"{RE}/treatment_master_v2.csv",dtype=str); T["k"]=T["k"].str.replace(r'\D','',regex=True).str.zfill(10)
T["ev"]=pd.to_datetime(T["event_dt"],errors="coerce").dt.to_period("M"); T=T.dropna(subset=["ev"]).drop_duplicates("k")

def ownD(b,e):
    """결과 D · 기준 logsize · 사전성장 pg(−13→−1, 원설계) · 원격 사전성장 pg_far(−25→−13)."""
    if b not in fx: return None
    row=LE[fx[b]]
    if e-25<0 or e+12>=NM: return None
    if not(np.isfinite(row[e-1]) and np.isfinite(row[e-13]) and np.isfinite(row[e-25])): return None
    bc=row[e-12:e]
    if np.sum(np.isfinite(bc))<6: return None
    bt=np.nanmean(bc); v=row[e+7:e+13]
    if np.sum(np.isfinite(v))<3: return None
    return dict(D=float(np.nanmean(v)-bt),logsize=float(bt),pg=float(row[e-1]-row[e-13]),
                pg_far=float(row[e-13]-row[e-25]),decl_near=bool(row[e-1]<row[e-13]),decl_far=bool(row[e-13]<row[e-25]))

def build(decl_window,symmetric):
    """decl_window: 'near'(원설계 [−13,−1]) | 'far'([−25,−13]) | None. symmetric: 처치에도 같은 조건 적용."""
    trt=[]
    for r in T.itertuples():
        o=ownD(r.k,mi.get(r.ev,-999))
        if o is None: continue
        fv=fin_asof(r.k,r.ev.year)
        if symmetric and decl_window and not o[f"decl_{decl_window}"]: continue
        if symmetric and not is_distress(fv): continue
        trt.append(dict(bn=r.k,e=mi[r.ev],yr=r.ev.year,**o,
                        lev=(fv[0] if fv else np.nan),roa=(fv[1] if fv else np.nan),cash=(fv[2] if fv else np.nan),
                        imp=(fv[3] if fv else 0),loss=(fv[4] if fv else 0),distress=int(is_distress(fv))))
    TR=pd.DataFrame(trt)
    drs=[]
    for e in sorted(set(TR.e)):
        yr=months[e].year
        for b in clean:
            if b not in fx: continue
            fv=fin_asof(b,yr)
            if not is_distress(fv): continue
            o=ownD(b,e)
            if o is None: continue
            if decl_window and not o[f"decl_{decl_window}"]: continue
            drs.append(dict(bn=b,e=e,yr=yr,**o,lev=fv[0],roa=fv[1],cash=fv[2],imp=fv[3],loss=fv[4]))
    DR=pd.DataFrame(drs).drop_duplicates(["bn","e"])
    return TR,DR

def weights(TR,DR,rich):
    cols=["logsize","pg_far" if rich else "pg","yr"]
    if rich: cols+=["lev","roa","cash","imp","loss"]
    A=TR[cols].copy(); Bd=DR[cols].copy()
    X=pd.concat([A,Bd]).astype(float); X["yr"]=X["yr"]-2015
    for c in ("lev","roa","cash"):
        if c in X: X[c]=X[c].clip(X[c].quantile(.01),X[c].quantile(.99)).fillna(X[c].median())
    Xs=(X-X.mean())/X.std().replace(0,1); Xs=Xs.to_numpy()
    y=np.r_[np.ones(len(TR)),np.zeros(len(DR))]
    lg=sm.Logit(y,sm.add_constant(Xs)).fit(disp=0,maxiter=200); ps=np.asarray(lg.predict(sm.add_constant(Xs)))
    w=ps[len(TR):]/(1-ps[len(TR):]); cap=np.percentile(w,99); w=np.clip(w,0,cap)
    return w/w.sum(), ps, Xs, cols

def smd(x_t,x_c,w):
    mt,mc=np.mean(x_t),np.average(x_c,weights=w)
    vt,vc=np.var(x_t),np.average((x_c-mc)**2,weights=w)
    return float((mt-mc)/np.sqrt((vt+vc)/2+1e-12))

GRID=np.round(np.arange(-0.60,-0.0999,0.05),2)
def cprob(d,w,c): return float(np.average((d<=c).astype(float),weights=w))
def stats(da,db,w):
    return dict(mean=float(np.mean(da)-np.average(db,weights=w)),
                median=float(np.median(da)-wq(db,w,.5)),
                p10=float(np.percentile(da,10)-wq(db,w,.10)),
                curve=[cprob(da,None,c)-cprob(db,w,c) for c in GRID])
def wq(x,w,q):
    o=np.argsort(x); cw=np.cumsum(w[o]); return float(x[o][np.searchsorted(cw,q*cw[-1])])

def infer(TR,DR,w,cluster,B=B_CI):
    da=TR.D.values; db=DR.D.values; obs=stats(da,db,w)
    firms=DR.bn.values; uf=np.unique(firms); byf={f:np.where(firms==f)[0] for f in uf}
    bs={"mean":[],"median":[],"p10":[]}; bcv=[]
    for _ in range(B):
        ia=RNG.integers(0,len(da),len(da))
        if cluster:
            ib=np.concatenate([byf[uf[i]] for i in RNG.integers(0,len(uf),len(uf))])
        else:
            ib=RNG.integers(0,len(db),len(db))
        wb=w[ib]; wb=wb/wb.sum()
        s=stats(da[ia],db[ib],wb)
        for k in bs: bs[k].append(s[k])
        bcv.append(s["curve"])
    bcv=np.array(bcv); se=bcv.std(0,ddof=1); se[se==0]=1e-9
    tmax=np.percentile(np.abs((bcv-bcv.mean(0))/se).max(1),95)
    cd=np.array(obs["curve"])
    out={k:dict(obs=round(obs[k],4),ci=[round(float(np.percentile(bs[k],2.5)),4),round(float(np.percentile(bs[k],97.5)),4)]) for k in bs}
    for k in out: out[k]["sig"]=bool(out[k]["ci"][0]>0 or out[k]["ci"][1]<0)
    out["curve"]={"grid":[float(c) for c in GRID],"diff":[round(float(x),4) for x in cd],
                  "lo_unif":[round(float(cd[j]-tmax*se[j]),4) for j in range(len(GRID))],
                  "hi_unif":[round(float(cd[j]+tmax*se[j]),4) for j in range(len(GRID))]}
    out["curve"]["sig_region"]=[float(GRID[j]) for j in range(len(GRID)) if out["curve"]["lo_unif"][j]>0]
    return out

def run(tag,decl,sym,rich,cluster):
    TR,DR=build(decl,sym)
    w,ps,Xs,cols=weights(TR,DR,rich)
    r=infer(TR,DR,w,cluster)
    ess=float(1.0/np.sum(w**2))
    bal={c:round(smd(Xs[:len(TR),j],Xs[len(TR):,j],w),3) for j,c in enumerate(cols)}
    pre={c:round(smd(Xs[:len(TR),j],Xs[len(TR):,j],np.ones(len(DR))/len(DR)),3) for j,c in enumerate(cols)}
    ov=dict(treated_ps=[round(float(np.percentile(ps[:len(TR)],q)),3) for q in (5,50,95)],
            ctrl_ps=[round(float(np.percentile(ps[len(TR):],q)),3) for q in (5,50,95)],
            treated_outside_support=int(np.sum(ps[:len(TR)]>ps[len(TR):].max())))
    res=dict(tag=tag,decl_window=decl,symmetric=sym,rich_weights=rich,firm_cluster=cluster,
             n_treated=int(len(TR)),n_ctrl_events=int(len(DR)),n_ctrl_firms=int(DR.bn.nunique()),
             ess=round(ess,1),max_abs_smd_post=round(max(abs(v) for v in bal.values()),3),
             smd_pre=pre,smd_post=bal,overlap=ov,**r)
    print(f"  {tag:<34} T={len(TR):>3} C={len(DR):>5}/{DR.bn.nunique():>3} ESS={ess:>6.1f} |SMD|max={res['max_abs_smd_post']:.3f} · "
          f"mean {r['mean']['obs']:+.4f}{r['mean']['ci']} · median {r['median']['obs']:+.4f}{r['median']['ci']}{'✓' if r['median']['sig'] else '✗'} · "
          f"p10 {r['p10']['obs']:+.4f}{r['p10']['ci']}{'✓' if r['p10']['sig'] else '✗'} · curve sig {len(r['curve']['sig_region'])}/{len(GRID)}",flush=True)
    return res

print("=== WP12a 비교군 재설계 ===",flush=True)
R={}
print("\n[A] 원설계 재현"); R["A_wp11c_replica"]=run("A wp11c 재현 (near·비대칭·빈약·독립)","near",False,False,False)
print("\n[B] 결함별 단계 교정")
R["B1_collider_fixed"]=run("B1 고용감소창→far, 대칭","far",True,False,False)
R["B2_plus_rich"]=run("B2 +재무가중","far",True,True,False)
R["B3_plus_cluster"]=run("B3 +기업군집 부트 (최종)","far",True,True,True)
print("\n[B'] 분리 진단 — 결함 하나씩")
R["Bx_rich_only"]=run("near·비대칭·재무가중·독립","near",False,True,False)
R["Bx_cluster_only"]=run("near·비대칭·빈약·군집","near",False,False,True)
R["Bx_nodecl"]=run("고용감소 조건 제거·대칭 distress·재무·군집",None,True,True,True)
F=R["B3_plus_cluster"]
verdict=(f"원설계 median {R['A_wp11c_replica']['median']['obs']:+.4f} / p10 {R['A_wp11c_replica']['p10']['obs']:+.4f} → "
         f"최종(collider 교정+재무가중+기업군집) median {F['median']['obs']:+.4f}{F['median']['ci']}"
         f"{'✓' if F['median']['sig'] else '✗'} / p10 {F['p10']['obs']:+.4f}{F['p10']['ci']}{'✓' if F['p10']['sig'] else '✗'} · "
         f"curve 유의 {len(F['curve']['sig_region'])}/{len(GRID)} · ESS {F['ess']} · |SMD|max {F['max_abs_smd_post']}.")
json.dump({"id":"WP12a","title":"C-C 비교군 재설계","runs":R,"verdict":verdict,
           "prediction":"세 교정 모두 현 결과에 불리 방향 가능",
           "kill":"p10 CI∋0 → tail 열위 철회 · median CI∋0 → median 우위 철회"},
          open(f"{OUT}/wp12a.json","w"),ensure_ascii=False,indent=1)
print("\n"+verdict); print(f"→ {OUT}/wp12a.json")
