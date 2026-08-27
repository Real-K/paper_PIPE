# -*- coding: utf-8 -*-
"""WP13e — BHAR 상폐하한·예측 배터리·목적별 subgroup ATT 의 신규-우주 재계산.

배경. 원고 §5.5·부록 C 가 인용하는 세 묶음(`wp9f_bhar_bounds`·`wp9d_car_predict`·목적별 subgroup ATT)이
**생산 스크립트 없는 인라인 산출**이라 C-A 로 우주가 바뀌어도 갱신되지 않는다. 재현 가능한 형태로 다시 만든다.

정의(구 산출과 동일하게 맞춘다).
  BHAR12 = ∏(1+r_i) − ∏(1+r_m), 이벤트 다음 거래일부터 252거래일, 유효일 ≥200. 시장수익률 = 전종목 동일가중 평균.
  **상폐의심** = 현행 주가자료에서 BHAR 를 계산할 수 없는 기업(티커 부재 또는 관측 부족). 결측을 무작위로 보지 않는다.
  **하한(bound)** = 상폐의심에 −100% 를 부여. 상장폐지 시 주주 손실이 전액이라는 가정이므로 **하한**이지 추정치가 아니다.
  꼬리(tail) = 매칭쌍 고용결과 d2 의 하위 4분위. severe = d2 ≤ −0.35(붕괴곡선 임계).

사전 예측. 관측 BHAR 는 상폐의심이 빠져 상방 편향 → 하한에서 rescue 평균이 크게 내려간다. rescue−growth 차이는
관측에서 유의, 하한에서도 부호 유지(구: obs p=0.0072 → bound p=0.0426). 예측 배터리는 전부 비유의(발표수익률은 꼬리를 못 가른다).
기각조건. 하한에서 rescue−growth 부호가 뒤집히면 §5.5 의 목적별 장기수익 서술을 철회한다.
"""
import json,numpy as np,pandas as pd,statsmodels.api as sm,warnings; warnings.filterwarnings("ignore")
from scipy import stats as st
import os
BASE=os.environ.get("P016_BASE", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))   # 원 경로는 제거했다 — 실행 시 P016_BASE 로 지정하거나 기본값 사용
O=f"{BASE}/shared/outputs/pipe_wp13_2026-08-26"
M=pd.read_csv(f"{O}/wp9e_firm_d_v2.csv",dtype=str); M.columns=[c.lstrip("﻿") for c in M.columns]
for c in ("d2","logsize","pregrowth","m1_p1","e0_p1","e0_p5","e0_p20","man"): M[c]=pd.to_numeric(M[c],errors="coerce")
for c in ("survival","growth_p"): M[c]=pd.to_numeric(M[c],errors="coerce").fillna(0).astype(int)
M["evd"]=pd.to_datetime(M.evd,errors="coerce"); M["year"]=M.evd.dt.year
# wp9e 는 종목코드를 실수형("5880.0")으로 저장한다 — 주가 열은 6자리 0채움("005880") 이므로 정규화 필요
def _sc(x):
    try: return str(int(float(x))).zfill(6)
    except (TypeError,ValueError): return None
M["sc"]=M.sc.map(_sc)
def load_sheet(sh):
    d=pd.read_excel(f"{BASE}/PI/drops/kospi, kosdaq 종목 수정주가.xlsx",sheet_name=sh)
    d=d.rename(columns={d.columns[0]:"date"}); d["date"]=pd.to_datetime(d["date"],errors="coerce")
    d=d.dropna(subset=["date"]).set_index("date").sort_index()
    d.columns=[str(c).replace("A","",1) if str(c).startswith("A") else str(c) for c in d.columns]
    return d.apply(pd.to_numeric,errors="coerce")
px=pd.concat([load_sheet("kospi"),load_sheet("kosdaq")],axis=1); px=px.loc[:,~px.columns.duplicated()]
ret=px/px.shift(1)-1.0; mkt=ret.mean(axis=1); dates=ret.index
print(f"주가 {px.shape} · 처치 {len(M)}",flush=True)
def bhar12(sc,evd):
    if not isinstance(sc,str) or sc not in ret.columns or pd.isna(evd): return np.nan
    p0=dates.searchsorted(evd)
    if p0+252>=len(dates) or p0<1: return np.nan
    ri=ret[sc].iloc[p0+1:p0+253].values; rm=mkt.iloc[p0+1:p0+253].values
    ok=np.isfinite(ri)&np.isfinite(rm)
    if ok.sum()<200: return np.nan
    return float(np.prod(1+ri[ok])-np.prod(1+rm[ok]))
M["bhar12"]=[bhar12(r.sc,r.evd) for r in M.itertuples()]
M["delist_susp"]=M.bhar12.isna().astype(int)
q25=M.d2.quantile(.25); M["tl"]=(M.d2<=q25).astype(int); M["severe"]=(M.d2<=-0.35).astype(int)
M["bhar_bound"]=M.bhar12.where(M.delist_susp==0,-1.0)
M.to_csv(f"{O}/wp13e_firm_bhar.csv",index=False,encoding="utf-8-sig")
print(f"BHAR 산출 {int(M.bhar12.notna().sum())}/{len(M)} · 상폐의심 {int(M.delist_susp.sum())} ({M.delist_susp.mean():.1%}) · 꼬리컷 {q25:.4f}",flush=True)
R={}
def mci(x,lab=None):
    x=pd.Series(x).dropna()
    if len(x)<3: return None
    se=x.std(ddof=1)/np.sqrt(len(x))
    o=dict(n=int(len(x)),mean=round(float(x.mean()),4),median=round(float(x.median()),4),
           ci=[round(float(x.mean()-1.96*se),4),round(float(x.mean()+1.96*se),4)])
    if lab: print(f"    {lab:<24} n={o['n']:>3} 평균 {100*o['mean']:+7.2f}% CI[{100*o['ci'][0]:+7.2f},{100*o['ci'][1]:+7.2f}] 중위 {100*o['median']:+7.2f}%",flush=True)
    return o
def welch(a,b):
    a,b=pd.Series(a).dropna(),pd.Series(b).dropna()
    if len(a)<3 or len(b)<3: return None
    t,p=st.ttest_ind(a,b,equal_var=False); return dict(diff=round(float(a.mean()-b.mean()),4),t=round(float(t),2),p=round(float(p),4),n1=int(len(a)),n2=int(len(b)))
print("\n[A] BHAR12 — 관측 vs 상폐하한(−100% 부여)")
for tag,col in (("관측","bhar12"),("하한","bhar_bound")):
    print(f"  {tag}:")
    R[f"{tag}_all"]=mci(M[col],"전체"); R[f"{tag}_rescue"]=mci(M.loc[M.survival==1,col],"rescue")
    R[f"{tag}_growth"]=mci(M.loc[M.growth_p==1,col],"growth"); R[f"{tag}_unclassified"]=mci(M.loc[(M.survival==0)&(M.growth_p==0),col],"미분류")
    w=welch(M.loc[M.survival==1,col],M.loc[M.growth_p==1,col]); R[f"{tag}_rescue_vs_growth"]=w
    if w: print(f"    rescue−growth {100*w['diff']:+.2f}pp Welch t={w['t']} **p={w['p']}** (n {w['n1']}/{w['n2']})",flush=True)
    else: print(f"    rescue−growth: 표본부족(rescue {int(M.loc[M.survival==1,col].notna().sum())}·growth {int(M.loc[M.growth_p==1,col].notna().sum())})",flush=True)
print("\n[B] 상폐의심 분해")
def rate(mask,lab):
    s=M[mask]; o=dict(n=int(len(s)),n_susp=int(s.delist_susp.sum()),rate=round(float(s.delist_susp.mean()),4))
    print(f"    {lab:<20} {o['n_susp']:>3}/{o['n']:<4} = {100*o['rate']:.1f}%",flush=True); return o
R["susp_overall"]=rate(M.k.notna(),"전체")
R["susp_tail"]=rate(M["tl"]==1,"고용 꼬리"); R["susp_rest"]=rate(M["tl"]==0,"나머지")
R["susp_rescue"]=rate(M.survival==1,"rescue"); R["susp_growth"]=rate(M.growth_p==1,"growth")
def fisher(a,b):
    t=[[a["n_susp"],a["n"]-a["n_susp"]],[b["n_susp"],b["n"]-b["n_susp"]]]
    return dict(table=t,fisher_p=round(float(st.fisher_exact(t).pvalue),4))
R["susp_tail_vs_rest"]=fisher(R["susp_tail"],R["susp_rest"]); R["susp_rescue_vs_growth"]=fisher(R["susp_rescue"],R["susp_growth"])
print(f"    꼬리 vs 나머지 Fisher p={R['susp_tail_vs_rest']['fisher_p']} · rescue vs growth Fisher p={R['susp_rescue_vs_growth']['fisher_p']}")
A=M[M.delist_susp==1]
R["absent_composition"]=dict(n=int(len(A)),pct_rescue=round(float(A.survival.mean()),4),pct_growth=round(float(A.growth_p.mean()),4),
                             pct_tail=round(float(A["tl"].mean()),4),median_d2=round(float(A.d2.median()),4),median_d2_present=round(float(M.loc[M.delist_susp==0,"d2"].median()),4))
c=R["absent_composition"]; print(f"    결측기업 구성 n={c['n']}: rescue {100*c['pct_rescue']:.0f}% · growth {100*c['pct_growth']:.0f}% · 꼬리 {100*c['pct_tail']:.0f}% · 고용결과 중위 {c['median_d2']:+.4f}(관측기업 {c['median_d2_present']:+.4f})")
R["obs_bhar_tail_vs_rest"]=dict(tail=mci(M.loc[M["tl"]==1,"bhar12"]),rest=mci(M.loc[M["tl"]==0,"bhar12"]),welch=welch(M.loc[M["tl"]==1,"bhar12"],M.loc[M["tl"]==0,"bhar12"]))
w=R["obs_bhar_tail_vs_rest"]["welch"]; print(f"    관측 BHAR 꼬리 vs 나머지 {100*w['diff']:+.2f}pp p={w['p']} (n {w['n1']}/{w['n2']})")
R["bound_bhar_tail_vs_rest"]=dict(welch=welch(M.loc[M["tl"]==1,"bhar_bound"],M.loc[M["tl"]==0,"bhar_bound"]))
print(f"    하한 BHAR 꼬리 vs 나머지 {100*R['bound_bhar_tail_vs_rest']['welch']['diff']:+.2f}pp p={R['bound_bhar_tail_vs_rest']['welch']['p']}")
print("\n[C] 예측 배터리 — 발표수익률이 고용 꼬리를 가르는가 (wp9d 신우주판)")
P=M.dropna(subset=["d2","m1_p1"]).copy()
X=sm.add_constant(np.column_stack([P.m1_p1,P.logsize,P.pregrowth]))
o1=sm.OLS(np.asarray(P.d2,float),X).fit(cov_type="HC1")
R["pred_ols_car11"]=dict(n=int(len(P)),coef=round(float(o1.params[1]),4),se=round(float(o1.bse[1]),4),t=round(float(o1.tvalues[1]),2),
    p=round(float(o1.pvalues[1]),4),ci=[round(float(o1.params[1]-1.96*o1.bse[1]),4),round(float(o1.params[1]+1.96*o1.bse[1]),4)],r2=round(float(o1.rsquared),3))
e=R["pred_ols_car11"]; print(f"    OLS d2~CAR[−1,+1]+통제  n={e['n']} coef {e['coef']:+.4f} t={e['t']} p={e['p']} CI{e['ci']} R2={e['r2']}")
rho,pr=st.spearmanr(P.d2,P.m1_p1); R["pred_spearman"]=dict(rho=round(float(rho),4),p=round(float(pr),4),n=int(len(P)))
print(f"    Spearman rho={rho:+.4f} p={pr:.4f}")
P["t3"]=pd.qcut(P.m1_p1,3,labels=False)
R["pred_tercile"]={f"T{i+1}":dict(n=int((P.t3==i).sum()),mean_d2=round(float(P.loc[P.t3==i,"d2"].mean()),4),median_d2=round(float(P.loc[P.t3==i,"d2"].median()),4)) for i in range(3)}
print("    CAR 3분위 평균 d2:", {k:v["mean_d2"] for k,v in R["pred_tercile"].items()})
for dep,lab in (("severe","1(d2≤−0.35)"),("tl","1(하위4분위)")):
    o2=sm.OLS(np.asarray(P[dep],float),X).fit(cov_type="HC1")
    R[f"pred_lpm_{dep}"]=dict(n=int(len(P)),coef=round(float(o2.params[1]),4),se=round(float(o2.bse[1]),4),p=round(float(o2.pvalues[1]),4),
        ci=[round(float(o2.params[1]-1.96*o2.bse[1]),4),round(float(o2.params[1]+1.96*o2.bse[1]),4)])
    q=R[f"pred_lpm_{dep}"]; print(f"    LPM {lab:<14} ~CAR  coef {q['coef']:+.4f} p={q['p']} CI{q['ci']}")
for dep,lab in (("severe","severe"),("tl","꼬리")):
    w=welch(P.loc[P[dep]==1,"m1_p1"],P.loc[P[dep]==0,"m1_p1"]); R[f"pred_car_{dep}_vs_rest"]=w
    print(f"    {lab} 기업 CAR vs 나머지: {100*P.loc[P[dep]==1,'m1_p1'].mean():+.2f}% vs {100*P.loc[P[dep]==0,'m1_p1'].mean():+.2f}% Welch p={w['p']} (n {w['n1']}/{w['n2']})")
print("\n[D] 목적별 subgroup ATT (매칭쌍 고용결과 d2)")
RNG=np.random.default_rng(20260827)
def bmean(x,B=4000):
    x=pd.Series(x).dropna().values
    if len(x)<5: return None
    bs=np.array([x[RNG.integers(0,len(x),len(x))].mean() for _ in range(B)])
    return dict(n=int(len(x)),mean=round(float(x.mean()),4),median=round(float(np.median(x)),4),
                ci=[round(float(np.percentile(bs,2.5)),4),round(float(np.percentile(bs,97.5)),4)])
for lab,m in (("rescue",M.survival==1),("growth",M.growth_p==1),("unclassified",(M.survival==0)&(M.growth_p==0))):
    R[f"subgroup_{lab}"]=bmean(M.loc[m,"d2"]); v=R[f"subgroup_{lab}"]
    if v: print(f"    {lab:<13} n={v['n']:>3} ATT {v['mean']:+.4f} CI{v['ci']} 중위 {v['median']:+.4f}")
R["subgroup_rescue_vs_growth"]=welch(M.loc[M.survival==1,"d2"],M.loc[M.growth_p==1,"d2"])
print(f"    rescue−growth {R['subgroup_rescue_vs_growth']['diff']:+.4f} Welch p={R['subgroup_rescue_vs_growth']['p']}")
ob=R["관측_rescue_vs_growth"]; bd=R["하한_rescue_vs_growth"]
verdict=(f"BHAR rescue−growth 관측 {ob['diff']} p={ob['p']} · 상폐하한 {bd['diff']} p={bd['p']} (부호 {'유지' if ob['diff']*bd['diff']>0 else '반전'}). "
         f"상폐의심 {R['susp_overall']['n_susp']}/{R['susp_overall']['n']} — 꼬리 {100*R['susp_tail']['rate']:.1f}% vs 나머지 {100*R['susp_rest']['rate']:.1f}% (Fisher p={R['susp_tail_vs_rest']['fisher_p']}). "
         f"예측 배터리 OLS coef {R['pred_ols_car11']['coef']} p={R['pred_ols_car11']['p']}.")
json.dump({"id":"WP13e","title":"BHAR 상폐하한·예측 배터리·목적별 subgroup ATT","runs":R,"verdict":verdict,
           "provenance":"처치=wp9e_firm_d_v2.csv(신규 우주, 2015–2025·210 고정 경유) · 주가=PI/drops 수정주가 · BHAR=252거래일 동일가중 시장조정, 유효일≥200 · 상폐의심=BHAR 계산불가 · 하한=상폐의심에 −100%",
           "kill":"상폐하한에서 rescue−growth 부호 반전 → §5.5 목적별 장기수익 서술 철회"},
          open(f"{O}/wp13e_bhar_prediction.json","w"),ensure_ascii=False,indent=1)
print("\n"+verdict)
