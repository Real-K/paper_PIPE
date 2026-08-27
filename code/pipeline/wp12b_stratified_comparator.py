# -*- coding: utf-8 -*-
"""WP12b — 층화 비교: 처치를 distress 상태로 나누고, 각 층을 같은 상태의 미수령과 비교.

wp12a 감사가 드러낸 것: 처치 210건 중 재무 distress 55%·고용감소 40% 인데, wp11c 는 비교군에만
distress+고용감소를 요구했다 → 처치의 절반(non-distressed)을 100% distressed 비교군과 비교. 그래서 median
우위가 나온다. 이건 collider 이전의 **정의 비대칭**이다.

올바른 설계: 상태 S ∈ {distress 여부} × {사전 고용감소 여부} 로 **처치·비교군을 같은 기준으로 층화**하고
각 층 안에서 비교한다. 고용감소는 결과 기저창과 겹치지 않는 [−25,−13] 로 잰다.
층 안에서는 'contemporaneous decline' 조건이 처치·비교군 양쪽에 대칭이므로 collider 가 아니다.

사전 예측.
  H1 (상태의존성): distressed 처치층에서 tail 열위가 가장 크고, non-distressed 층에서는 약하거나 없다.
  H2 (median): 층 안에서 median 우위는 wp11c 보다 축소된다(정의 비대칭 제거).
  H3 (통합): 층별 가중평균의 p10 열위는 유지된다 — wp11c 의 tail 결과는 정의 비대칭에도 불구하고 살아남는다.
기각조건. 통합 p10 CI ∋ 0 → 'tail 열위' 철회. 모든 층에서 tail 무차이 → §5.4 재작성.

검정력 장치. (a) 층별 비교군 규모가 크므로 SE 는 처치 n 이 지배 — 층을 2×2 가 아니라 **distress 2층**과
**decl_far 2층**을 각각 따로 봄(교차층은 부록). (b) 재무가중은 층 안에서(공선성 완화). (c) 기업 군집 부트.
(d) 통합 추정치 = 처치 층 크기 가중.
"""
import os,json,warnings; warnings.filterwarnings("ignore")
import numpy as np,pandas as pd
import statsmodels.api as sm
BASE=os.environ.get("P016_BASE", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))   # 원 경로는 제거했다 — 실행 시 P016_BASE 로 지정하거나 기본값 사용
RE=f"{BASE}/shared/outputs/pipe_r1_reextract_2026-08-22"; W11=f"{BASE}/shared/outputs/pipe_wp11_2026-08-23"
OUT=f"{BASE}/shared/outputs/pipe_wp12_2026-08-26"; RNG=np.random.default_rng(20260826); B=2000
CL=pd.read_csv(f"{W11}/controls_clean.csv",dtype={"bn":str}); clean=set(CL[CL.third_hist==False].bn)
FIN=pd.read_csv(f"{W11}/fin_distress_panel.csv",dtype={"bn":str})
fin={(r.bn,int(r.year)):(r.lev,r.roa,r.cash,int(r.impaired),int(r.loss)) for r in FIN.itertuples()}
def fin_asof(bn,yr):
    for y in (yr-1,yr-2):
        v=fin.get((bn,y))
        if v: return v
def is_d(fv): return fv is not None and (fv[4]==1 or (fv[0]==fv[0] and fv[0]>2) or fv[3]==1)
nps=pd.read_parquet(f"{BASE}/shared/data/processed/nps_monthly_matched_v2.parquet",columns=["bn10","data_ym","가입자수"])
nps["ym"]=pd.PeriodIndex(nps["data_ym"],freq="M"); nps["le"]=np.log1p(nps["가입자수"].astype(float))
months=pd.period_range(nps.ym.min(),nps.ym.max(),freq="M"); mi={m:j for j,m in enumerate(months)}; NM=len(months)
piv=nps.pivot_table(index="bn10",columns="ym",values="le",aggfunc="mean").reindex(columns=months)
fx={b:i for i,b in enumerate(piv.index)}; LE=piv.to_numpy(float); del nps,piv
T=pd.read_csv(f"{RE}/treatment_master_v2.csv",dtype=str); T["k"]=T["k"].str.replace(r'\D','',regex=True).str.zfill(10)
T["ev"]=pd.to_datetime(T["event_dt"],errors="coerce").dt.to_period("M"); T=T.dropna(subset=["ev"]).drop_duplicates("k")

def unit(b,e,yr):
    if b not in fx: return None
    row=LE[fx[b]]
    if e-13<0 or e+12>=NM or not(np.isfinite(row[e-1]) and np.isfinite(row[e-13])): return None
    bc=row[e-12:e]
    if np.sum(np.isfinite(bc))<6: return None
    v=row[e+7:e+13]
    if np.sum(np.isfinite(v))<3: return None
    fv=fin_asof(b,yr)
    if fv is None: return None
    far=(e-25>=0 and np.isfinite(row[e-25]))
    return dict(bn=b,e=e,yr=yr,D=float(np.nanmean(v)-np.nanmean(bc)),logsize=float(np.nanmean(bc)),
                pg=float(row[e-1]-row[e-13]),
                decl_far=(int(row[e-13]<row[e-25]) if far else -1),   # −1 = 관측불가
                distress=int(is_d(fv)),lev=fv[0],roa=fv[1],cash=fv[2],imp=fv[3],loss=fv[4])

TR=pd.DataFrame([u for r in T.itertuples() for u in [unit(r.k,mi.get(r.ev,-999),r.ev.year)] if u])
print(f"처치 {len(TR)} · distress {TR.distress.sum()} · decl_far 1/0/NA = {(TR.decl_far==1).sum()}/{(TR.decl_far==0).sum()}/{(TR.decl_far==-1).sum()}",flush=True)
drs=[]
for e in sorted(set(TR.e)):
    yr=months[e].year
    for b in clean:
        u=unit(b,e,yr)
        if u: drs.append(u)
DR=pd.DataFrame(drs).drop_duplicates(["bn","e"])
print(f"청정 미수령 firm-event {len(DR)} (기업 {DR.bn.nunique()}) · distress {DR.distress.mean():.1%} · decl_far=1 {(DR.decl_far==1).mean():.1%}",flush=True)

GRID=np.round(np.arange(-0.60,-0.0999,0.05),2)
def wq(x,w,q):
    o=np.argsort(x); cw=np.cumsum(w[o]); return float(x[o][np.searchsorted(cw,q*cw[-1])])
def stats(da,db,w):
    return dict(mean=float(np.mean(da)-np.average(db,weights=w)),median=float(np.median(da)-wq(db,w,.5)),
                p10=float(np.percentile(da,10)-wq(db,w,.10)),
                curve=[float(np.mean(da<=c)-np.average((db<=c).astype(float),weights=w)) for c in GRID])
def weights(A,Bd,cols):
    X=pd.concat([A[cols],Bd[cols]]).astype(float).copy(); X["yr"]=X["yr"]-2015
    for c in ("lev","roa","cash"):
        if c in X: X[c]=X[c].clip(X[c].quantile(.01),X[c].quantile(.99)).fillna(X[c].median())
    X=X.loc[:,X.std()>1e-9]            # 층 안에서 상수인 열(예: non-distressed 층의 imp·loss) 제거 → 특이행렬 방지
    Xs=((X-X.mean())/X.std()).to_numpy(); y=np.r_[np.ones(len(A)),np.zeros(len(Bd))]
    Xc=sm.add_constant(Xs); converged=True
    try:
        lg=sm.Logit(y,Xc).fit(disp=0,maxiter=300)
        if not lg.mle_retvals.get("converged",True): raise RuntimeError("nonconv")
        ps=np.asarray(lg.predict(Xc))
    except Exception:
        # 극단 불균형(T≪C)에서 MLE 가 발산 → L2 정규화 로짓. 균등가중 fallback 은 쓰지 않는다.
        converged=False
        lg=sm.Logit(y,Xc).fit_regularized(alpha=1.0,L1_wt=0.0,disp=0,maxiter=500); ps=np.asarray(lg.predict(Xc))
    ps=np.clip(ps,1e-6,1-1e-6)
    w=ps[len(A):]/(1-ps[len(A):]); w=np.clip(w,0,np.percentile(w,99)); w=w/w.sum()
    weights.last_converged=converged
    return w,Xs,ps
def smd(xt,xc,w):
    mt,mc=xt.mean(),np.average(xc,weights=w); return float((mt-mc)/np.sqrt((xt.var()+np.average((xc-mc)**2,weights=w))/2+1e-12))
def compare(A,Bd,tag,cols):
    if len(A)<15 or len(Bd)<50: print(f"  {tag:<36} 표본 부족 T={len(A)} C={len(Bd)}"); return None
    w,Xs,ps=weights(A,Bd,cols); da,db=A.D.values,Bd.D.values; obs=stats(da,db,w)
    firms=Bd.bn.values; uf=np.unique(firms); byf={f:np.where(firms==f)[0] for f in uf}
    bs={"mean":[],"median":[],"p10":[]}; bcv=[]
    for _ in range(B):
        ia=RNG.integers(0,len(da),len(da)); ib=np.concatenate([byf[uf[i]] for i in RNG.integers(0,len(uf),len(uf))])
        wb=w[ib]; wb=wb/wb.sum(); s=stats(da[ia],db[ib],wb)
        for k in bs: bs[k].append(s[k])
        bcv.append(s["curve"])
    bcv=np.array(bcv); se=bcv.std(0,ddof=1); se[se==0]=1e-9
    tmax=np.percentile(np.abs((bcv-bcv.mean(0))/se).max(1),95); cd=np.array(obs["curve"])
    r={k:dict(obs=round(obs[k],4),ci=[round(float(np.percentile(bs[k],2.5)),4),round(float(np.percentile(bs[k],97.5)),4)]) for k in bs}
    for k in r: r[k]["sig"]=bool(r[k]["ci"][0]>0 or r[k]["ci"][1]<0)
    lo=[round(float(cd[j]-tmax*se[j]),4) for j in range(len(GRID))]
    hi=[round(float(cd[j]+tmax*se[j]),4) for j in range(len(GRID))]
    r["curve"]=dict(grid=[float(g) for g in GRID],diff=[round(float(x),4) for x in cd],se=[round(float(x),4) for x in se],lo_unif=lo,hi_unif=hi,
                    sig_region=[float(GRID[j]) for j in range(len(GRID)) if lo[j]>0])
    r["cprob_treated"]={str(c):round(float(np.mean(da<=c)),4) for c in (-0.5,-0.35,-0.25)}
    r["cprob_ctrl_w"]={str(c):round(float(np.average((db<=c).astype(float),weights=w)),4) for c in (-0.5,-0.35,-0.25)}
    r["n_treated"]=int(len(A)); r["n_ctrl_events"]=int(len(Bd)); r["n_ctrl_firms"]=int(Bd.bn.nunique())
    r["ess"]=round(float(1/np.sum(w**2)),1); r["ps_converged"]=bool(getattr(weights,"last_converged",True)); r["max_abs_smd"]=round(max(abs(smd(Xs[:len(A),j],Xs[len(A):,j],w)) for j in range(Xs.shape[1])),3)
    r["boot_sd"]={k:round(float(np.std(bs[k])),4) for k in bs}
    print(f"  {tag:<36} T={len(A):>3} C={len(Bd):>5}/{Bd.bn.nunique():>3} ESS={r['ess']:>6.0f}{'' if r['ps_converged'] else '(L2)'} SMD={r['max_abs_smd']:.3f} · "
          f"median {r['median']['obs']:+.4f}{r['median']['ci']}{'✓' if r['median']['sig'] else '✗'} · "
          f"p10 {r['p10']['obs']:+.4f}{r['p10']['ci']}{'✓' if r['p10']['sig'] else '✗'} · curve {len(r['curve']['sig_region'])}/11",flush=True)
    return r

BASE_COLS=["logsize","pg","yr"]; RICH=BASE_COLS+["lev","roa","cash","imp","loss"]
R={}
print("\n[A] 전체 처치 vs 전체 청정 미수령 (distress 조건 없음 — 정의 대칭의 기준점)")
R["A_all_vs_all"]=compare(TR,DR,"전체 vs 전체 · 재무가중",RICH)
print("\n[B] distress 층화 (처치·비교군 같은 기준)")
R["B_distress_1"]=compare(TR[TR.distress==1],DR[DR.distress==1],"distressed 처치 vs distressed 미수령",RICH)
R["B_distress_0"]=compare(TR[TR.distress==0],DR[DR.distress==0],"non-distressed 처치 vs non-distressed",RICH)
print("\n[C] 사전 고용감소 [−25,−13] 층화")
R["C_declfar_1"]=compare(TR[TR.decl_far==1],DR[DR.decl_far==1],"고용감소 처치 vs 고용감소 미수령",RICH)
R["C_declfar_0"]=compare(TR[TR.decl_far==0],DR[DR.decl_far==0],"비감소 처치 vs 비감소 미수령",RICH)
print("\n[D] 교차층 (부록)")
R["D_d1_f1"]=compare(TR[(TR.distress==1)&(TR.decl_far==1)],DR[(DR.distress==1)&(DR.decl_far==1)],"distress∧감소",RICH)
R["D_d1_f0"]=compare(TR[(TR.distress==1)&(TR.decl_far==0)],DR[(DR.distress==1)&(DR.decl_far==0)],"distress∧비감소",RICH)
R["D_d0_f1"]=compare(TR[(TR.distress==0)&(TR.decl_far==1)],DR[(DR.distress==0)&(DR.decl_far==1)],"non-distress∧감소",RICH)
R["D_d0_f0"]=compare(TR[(TR.distress==0)&(TR.decl_far==0)],DR[(DR.distress==0)&(DR.decl_far==0)],"non-distress∧비감소",RICH)

print("\n[E] 층별 가중 통합 (처치 층 크기 가중)")
def pool(keys):
    rs=[R[k] for k in keys if R.get(k)]; n=np.array([r["n_treated"] for r in rs]); w=n/n.sum()
    out={}
    for s in ("mean","median","p10"):
        est=float(np.sum(w*np.array([r[s]["obs"] for r in rs])))
        sd=float(np.sqrt(np.sum((w*np.array([r["boot_sd"][s] for r in rs]))**2)))
        out[s]=dict(obs=round(est,4),ci=[round(est-1.96*sd,4),round(est+1.96*sd,4)],sig=bool(abs(est)>1.96*sd))
    j35=list(GRID).index(-0.35); j25=list(GRID).index(-0.25); j50=list(GRID).index(-0.5)
    for lab,j in (("cprob_-0.5",j50),("cprob_-0.35",j35),("cprob_-0.25",j25)):
        est=float(np.sum(w*np.array([r["curve"]["diff"][j] for r in rs]))); sd=float(np.sqrt(np.sum((w*np.array([r["curve"]["se"][j] for r in rs]))**2)))
        out[lab]=dict(obs=round(est,4),ci=[round(est-1.96*sd,4),round(est+1.96*sd,4)],sig=bool(abs(est)>1.96*sd))
    out["n_treated"]=int(n.sum()); out["note"]="처치 층 크기 가중 · 정규근사 CI(층별 부트 SD 합성)"
    return out
R["E_pool_distress"]=pool(["B_distress_1","B_distress_0"]); R["E_pool_declfar"]=pool(["C_declfar_1","C_declfar_0"])
for k in ("E_pool_distress","E_pool_declfar"):
    p=R[k]; print(f"  {k:<20} median {p['median']['obs']:+.4f}{p['median']['ci']}{'✓' if p['median']['sig'] else '✗'} · p10 {p['p10']['obs']:+.4f}{p['p10']['ci']}{'✓' if p['p10']['sig'] else '✗'} · mean {p['mean']['obs']:+.4f}{p['mean']['ci']}")

print("\n[F] 상태의존성 검정 — 층 간 p10 차이 (distressed − non)")
def strat_diff(k1,k0):
    a,b=R.get(k1),R.get(k0)
    if not(a and b): return None
    d=a["p10"]["obs"]-b["p10"]["obs"]; sd=np.hypot(a["boot_sd"]["p10"],b["boot_sd"]["p10"])
    return dict(diff=round(d,4),ci=[round(d-1.96*sd,4),round(d+1.96*sd,4)],sig=bool(abs(d)>1.96*sd))
R["F_state_dep_distress"]=strat_diff("B_distress_1","B_distress_0"); R["F_state_dep_declfar"]=strat_diff("C_declfar_1","C_declfar_0")
for k in ("F_state_dep_distress","F_state_dep_declfar"):
    if R[k]: print(f"  {k:<24} p10 층간차 {R[k]['diff']:+.4f} {R[k]['ci']} {'✓' if R[k]['sig'] else '✗'}")

print("\n[G] H3 조절효과 — 상호작용 회귀 (LPM · 기업 군집 SE · 연도 FE) : 종속 = 1(D≤c) 또는 D")
P=pd.concat([TR.assign(tr=1),DR.assign(tr=0)],ignore_index=True)
for c_ in ("lev","roa","cash"): P[c_]=P[c_].clip(P[c_].quantile(.01),P[c_].quantile(.99)).fillna(P[c_].median())
P["ncrit"]=P["loss"]+P["imp"]+(P["lev"]>2).astype(int)              # distress 기준 충족 수 0~3
P["zroa"]=-(P["roa"]-P["roa"].mean())/P["roa"].std()                # 연속 부진 지수(ROA 음수화 표준화)
def lpm(y,mod,tag):
    X=pd.DataFrame({"tr":P.tr,"mod":P[mod],"tr_x_mod":P.tr*P[mod],"logsize":P.logsize,"pg":P.pg,"lev":P.lev,"roa":P.roa,"cash":P.cash})
    X=pd.concat([X,pd.get_dummies(P.yr,prefix="y",drop_first=True).astype(float)],axis=1); X=sm.add_constant(X)
    if mod=="distress": X=X.drop(columns=["lev","roa"]) if False else X
    m=sm.OLS(y.astype(float),X).fit(cov_type="cluster",cov_kwds={"groups":pd.factorize(P.bn)[0]})
    o={k:dict(b=round(float(m.params[k]),4),se=round(float(m.bse[k]),4),p=round(float(m.pvalues[k]),4)) for k in ("tr","mod","tr_x_mod")}
    o["n"]=int(m.nobs); o["clusters"]=int(P.bn.nunique())
    print(f"  {tag:<44} tr {o['tr']['b']:+.4f}({o['tr']['se']:.4f}) p={o['tr']['p']:.3f} · tr×mod {o['tr_x_mod']['b']:+.4f}({o['tr_x_mod']['se']:.4f}) p={o['tr_x_mod']['p']:.3f}")
    return o
G={}
for mod in ("distress","ncrit","zroa"):
    for c in (-0.35,-0.25,-0.5):
        G[f"collapse{c}_x_{mod}"]=lpm((P.D<=c).astype(int),mod,f"1(D≤{c}) × {mod}")
    G[f"meanD_x_{mod}"]=lpm(P.D,mod,f"D(mean) × {mod}")
R["G_interaction"]=G
d1=R.get("B_distress_1") or {}; pe=R["E_pool_distress"]
verdict=(f"distress 층화: distressed 처치 vs distressed 미수령 median {d1.get('median',{}).get('obs')} p10 {d1.get('p10',{}).get('obs')}{d1.get('p10',{}).get('ci')}. "
         f"통합 p10 {pe['p10']['obs']}{pe['p10']['ci']}{'✓' if pe['p10']['sig'] else '✗'} · median {pe['median']['obs']}{pe['median']['ci']}{'✓' if pe['median']['sig'] else '✗'}. "
         f"상태의존성(distress) p10 층간차 {R['F_state_dep_distress']['diff'] if R['F_state_dep_distress'] else None}.")
json.dump({"id":"WP12b","title":"층화 비교군","runs":R,"verdict":verdict,
           "provenance":{"treated_master":"treatment_master_v2.csv (mtime 2026-08-23 13:54; wp11c 는 03:41 구버전으로 205건 — 같은 코드가 현행 마스터에서 210건)",
                         "outcome":"own log-employment change: mean(m+7..+12) − mean(m−12..−1)","weights":"propensity odds; logsize·pg·yr + lev·roa·cash·imp·loss (층 내 상수열 제거; MLE 발산 시 L2)",
                         "inference":"처치 iid·비교군 기업군집 부트 B=2000; 곡선 sup-t 균일대","seed":20260826},
           "prediction":"H1 distressed 층에서 tail 열위 최대 · H2 median 우위 축소 · H3 통합 p10 유지",
           "kill":"통합 p10 CI∋0 → tail 열위 철회"},open(f"{OUT}/wp12b.json","w"),ensure_ascii=False,indent=1)
print("\n"+verdict)
