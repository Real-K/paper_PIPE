# -*- coding: utf-8 -*-
"""WP13d — 시장측 인라인 산출 2건의 신규-우주 재계산 + 시장·실물 공통표본 CAR.

배경. 원고 초록·§3·§5.1·커버레터가 인용하는 세 수치가 **생산 스크립트 없는 인라인 산출**(wp8c·wp10g)이라
C-A 로 우주가 바뀌어도 갱신되지 않는다. 여기서 재현 가능한 형태로 다시 만든다.

(1) 목적-CAR 통제회귀 — 원고: "+5.3pp, stake·deal size·firm size·year 통제 후에도 유지".
    주장 그대로의 대조는 **분류표본 내 rescue vs growth** 이므로 growth 를 기준범주로 둔 분류전용 회귀가 정본이고
    (리뷰 C-D 의 'classified-only 회귀' 요구와 동일), 미분류를 기준으로 둔 전체표본 회귀를 함께 보고한다.
    SE 는 HC1 과 **이벤트 연월 군집** 두 가지 — 같은 달에 몰린 딜의 상관을 무시하면 SE 가 과소해진다.
(2) 미분류·혼합 CAR — 원고 §3: "미분류 이벤트의 평균 CAR 는 음수라 프리미엄은 분류딜에 특정적".
(3) 시장·실물 공통표본 CAR — 리뷰 C-D. 고용 1차표본(210)과 CAR 표본의 교집합에서 프리미엄이 재현되는지.
    두 결과가 서로 다른 기업집합에서 나온다는 지적을 차단한다.

사전 예측. (1) 계수는 +0.05 내외로 유지되나 군집 SE 는 HC1 보다 넓다. (2) 미분류 평균은 0 이하.
(3) 공통표본에서 프리미엄 부호 유지, 표본이 작아 CI 는 넓어진다.
기각조건. (1) 분류전용 회귀의 rescue 계수 CI 가 0 포함 → 초록·§5.1 의 "통제 후에도 유지" 문장 철회.
"""
import json,numpy as np,pandas as pd,statsmodels.api as sm,warnings; warnings.filterwarnings("ignore")
import os
BASE=os.environ.get("P016_BASE", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))   # 원 경로는 제거했다 — 실행 시 P016_BASE 로 지정하거나 기본값 사용
RE=f"{BASE}/shared/outputs/pipe_r1_reextract_2026-08-22"; O=f"{BASE}/shared/outputs/pipe_wp13_2026-08-26"
def rd(p,**kw):
    d=pd.read_csv(p,**kw); d.columns=[c.lstrip("﻿") for c in d.columns]; return d
T=rd(f"{RE}/treatment_master_v2.csv",dtype=str); T["k"]=T.k.str.replace(r"\D","",regex=True).str.zfill(10)
T=T[pd.to_numeric(T.event_dt.astype(str).str[:4],errors="coerce").between(2015,2025)]
T["ev"]=pd.to_datetime(T.event_dt,errors="coerce"); T=T.dropna(subset=["ev"]).drop_duplicates("k")
car=rd(f"{O}/wp10b_car_vw.csv",dtype={"k":str}); car["k"]=car.k.str.zfill(10)
stk=rd(f"{O}/wp10a_stake.csv",dtype={"k":str}); stk["k"]=stk.k.str.zfill(10)
pb=rd(f"{BASE}/shared/data/processed/pitchbook_all_status_v1.csv",dtype=str)
pb["k"]=pb["bn"].astype(str).str.replace(r"\D","",regex=True).str.zfill(10)
pbz=pb[["k","Deal Size"]].copy(); pbz["sz"]=pd.to_numeric(pbz["Deal Size"],errors="coerce"); pbz=pbz.groupby("k",as_index=False).sz.max()
nps=pd.read_parquet(f"{BASE}/shared/data/processed/nps_monthly_matched_v2.parquet",columns=["bn10","data_ym","가입자수"])
nps["le"]=np.log1p(nps["가입자수"].astype(float))
fsz=nps.groupby("bn10").le.median().rename("logsize"); del nps
EMP=set(l.strip() for l in open(f"{O}/emp_primary_k.txt") if l.strip())
D=(T[["k","ev"]].merge(car,on="k").merge(stk[["k","stake"]],on="k",how="left").merge(pbz,on="k",how="left")
     .merge(fsz,left_on="k",right_index=True,how="left"))
for c in ("car11","car05","scar11","scar05","stake","sz","logsize"):
    if c in D.columns: D[c]=pd.to_numeric(D[c],errors="coerce")
for c in ("survival","growth","classified"): D[c]=D[c].astype(str).isin(["True","1","1.0"])
D=D.dropna(subset=["car11"]).copy()
D["ym"]=D.ev.dt.to_period("M").astype(str); D["year"]=D.ev.dt.year
D["lsz"]=np.log1p(D.sz.fillna(D.sz.median())); D["stake_f"]=D.stake.fillna(D.stake.median())
D["logsize"]=D.logsize.fillna(D.logsize.median()); D["in_emp"]=D.k.isin(EMP)
print(f"CAR 표본 {len(D)} · 분류 {int(D.classified.sum())}(rescue {int(D.survival.sum())}/growth {int(D.growth.sum())}) · 미분류 {int((~D.classified).sum())} · 고용표본 교집합 {int(D.in_emp.sum())}",flush=True)
R={}
def reg(df,cols,tag,dep="car11"):
    if len(df)<40: print(f"  {tag}: 표본부족 {len(df)}"); return None
    yd=pd.get_dummies(df.year,prefix="y",drop_first=True).astype(float)
    X=sm.add_constant(pd.concat([df[cols].astype(float).reset_index(drop=True),yd.reset_index(drop=True)],axis=1))
    y=np.asarray(df[dep],float)
    h=sm.OLS(y,X).fit(cov_type="HC1")
    c=sm.OLS(y,X).fit(cov_type="cluster",cov_kwds={"groups":pd.factorize(df.ym)[0]})
    o={"n":int(len(df)),"n_month_clusters":int(df.ym.nunique()),"r2":round(float(h.rsquared),3)}
    for v in cols:
        o[v]={"coef":round(float(h.params[v]),4),
              "hc1":{"se":round(float(h.bse[v]),4),"p":round(float(h.pvalues[v]),4),
                     "ci":[round(float(h.params[v]-1.96*h.bse[v]),4),round(float(h.params[v]+1.96*h.bse[v]),4)]},
              "cluster_ym":{"se":round(float(c.bse[v]),4),"p":round(float(c.pvalues[v]),4),
                            "ci":[round(float(c.params[v]-1.96*c.bse[v]),4),round(float(c.params[v]+1.96*c.bse[v]),4)]}}
    print(f"  {tag:<44} n={o['n']:>3} clusters={o['n_month_clusters']:>3} R2={o['r2']:.3f}",flush=True)
    for v in cols:
        e=o[v]; print(f"      {v:<12} {e['coef']:+.4f}  HC1 {e['hc1']['ci']} p={e['hc1']['p']:.4f} · 군집 {e['cluster_ym']['ci']} p={e['cluster_ym']['p']:.4f}",flush=True)
    return o
CTRL=["stake_f","lsz","logsize"]
print("\n[1] 목적-CAR 통제회귀 (종속 car11, 값비중 프록시)")
R["A_classified_only"]=reg(D[D.classified],["survival"]+CTRL,"분류전용 rescue vs growth (정본·C-D)")
R["B_full_sample"]=reg(D,["survival","growth"]+CTRL,"전체 317: rescue·growth vs 미분류")
R["C_classified_car05"]=reg(D[D.classified],["survival"]+CTRL,"분류전용 [0,+5] 창","car05")
print("\n[2] 미분류·혼합 CAR")
def desc(x,lab):
    x=pd.to_numeric(x,errors="coerce").dropna()
    if len(x)<5: return None
    se=x.std(ddof=1)/np.sqrt(len(x)); o=dict(n=int(len(x)),mean=round(float(x.mean()),4),median=round(float(x.median()),4),
        ci=[round(float(x.mean()-1.96*se),4),round(float(x.mean()+1.96*se),4)],t=round(float(x.mean()/se),2),pct_pos=round(float((x>0).mean()),3))
    print(f"  {lab:<30} n={o['n']:>3} mean {100*o['mean']:+.2f}% CI[{100*o['ci'][0]:+.2f},{100*o['ci'][1]:+.2f}] t={o['t']:+.2f} 중위 {100*o['median']:+.2f}% 양비율 {o['pct_pos']:.3f}",flush=True)
    return o
R["D_unclassified"]=desc(D[~D.classified].car11,"미분류·혼합 [−1,+1]")
R["D_unclassified_car05"]=desc(D[~D.classified].car05,"미분류·혼합 [0,+5]")
R["D_classified"]=desc(D[D.classified].car11,"분류 전체 [−1,+1]")
R["D_rescue"]=desc(D[D.survival].car11,"rescue [−1,+1]"); R["D_growth"]=desc(D[D.growth].car11,"growth [−1,+1]")
from scipy import stats as st
a=D[~D.classified].car11.dropna(); b=D[D.classified].car11.dropna()
t_,p_=st.ttest_ind(a,b,equal_var=False); R["E_unclassified_vs_classified"]=dict(diff=round(float(a.mean()-b.mean()),4),welch_t=round(float(t_),2),welch_p=round(float(p_),4))
print(f"  미분류−분류 차이 {100*R['E_unclassified_vs_classified']['diff']:+.2f}pp Welch p={R['E_unclassified_vs_classified']['welch_p']:.4f}")
print("\n[3] 시장·실물 공통표본 (고용 1차표본 210 ∩ CAR) — 리뷰 C-D")
R["F_overlap_all"]=desc(D[D.in_emp].car11,"공통표본 전체")
R["F_overlap_rescue"]=desc(D[D.in_emp&D.survival].car11,"공통표본 rescue")
R["F_overlap_growth"]=desc(D[D.in_emp&D.growth].car11,"공통표본 growth")
ov=D[D.in_emp&D.classified]
if len(ov)>=40: R["F_overlap_reg"]=reg(ov,["survival"]+CTRL,"공통표본 분류전용 회귀")
r,g=D[D.in_emp&D.survival].car11.dropna(),D[D.in_emp&D.growth].car11.dropna()
if len(r)>5 and len(g)>5:
    t2,p2=st.ttest_ind(r,g,equal_var=False); R["F_overlap_welch"]=dict(diff=round(float(r.mean()-g.mean()),4),welch_t=round(float(t2),2),welch_p=round(float(p2),4),n_rescue=int(len(r)),n_growth=int(len(g)))
    print(f"  공통표본 rescue−growth {100*R['F_overlap_welch']['diff']:+.2f}pp Welch p={R['F_overlap_welch']['welch_p']:.4f} (n {len(r)}/{len(g)})")

print("\n[4] 통제 사다리 — rescue 계수가 어느 통제에서 사라지는가 (분류전용 n=221)")
CL=D[D.classified].copy()
LAD=[("(1) rescue 단독",["survival"],False),("(2) + 연도FE",["survival"],True),
     ("(3) + 딜규모·기업규모",["survival","lsz","logsize"],True),("(4) + 지분율(stake)",["survival","lsz","logsize","stake_f"],True)]
def reg2(df,cols,yfe,tag,dep="car11"):
    X=df[cols].astype(float).reset_index(drop=True)
    if yfe:
        yd=pd.get_dummies(df.year,prefix="y",drop_first=True).astype(float).reset_index(drop=True); X=pd.concat([X,yd],axis=1)
    X=sm.add_constant(X); y=np.asarray(df[dep],float)
    h=sm.OLS(y,X).fit(cov_type="HC1"); c=sm.OLS(y,X).fit(cov_type="cluster",cov_kwds={"groups":pd.factorize(df.ym)[0]})
    v="survival"; o=dict(n=int(len(df)),coef=round(float(h.params[v]),4),
        hc1_ci=[round(float(h.params[v]-1.96*h.bse[v]),4),round(float(h.params[v]+1.96*h.bse[v]),4)],hc1_p=round(float(h.pvalues[v]),4),
        cl_ci=[round(float(c.params[v]-1.96*c.bse[v]),4),round(float(c.params[v]+1.96*c.bse[v]),4)],cl_p=round(float(c.pvalues[v]),4),r2=round(float(h.rsquared),3))
    print(f"  {tag:<24} rescue {o['coef']:+.4f}  HC1 {o['hc1_ci']} p={o['hc1_p']:.4f} · 군집 {o['cl_ci']} p={o['cl_p']:.4f}  R2={o['r2']:.3f}",flush=True)
    return o
R["G_ladder"]={t:reg2(CL,c_,y_,t) for t,c_,y_ in LAD}
R["G_ladder_overlap"]={t:reg2(D[D.in_emp&D.classified],c_,y_,"공통 "+t) for t,c_,y_ in LAD} if int((D.in_emp&D.classified).sum())>=60 else None
print("\n[5] 지분율은 목적과 함께 결정되는가 (bad-control 판정 근거)")
sk={}
for lab,m in (("rescue",D.survival),("growth",D.growth),("unclassified",~D.classified)):
    x=D.loc[m,"stake"].dropna()
    sk[lab]=dict(n=int(len(x)),mean=round(float(x.mean()),4),median=round(float(x.median()),4),p25=round(float(x.quantile(.25)),4),p75=round(float(x.quantile(.75)),4))
    print(f"  stake {lab:<13} n={sk[lab]['n']:>3} 평균 {100*sk[lab]['mean']:.2f}% 중위 {100*sk[lab]['median']:.2f}% IQR {100*sk[lab]['p25']:.2f}–{100*sk[lab]['p75']:.2f}%",flush=True)
r_,g_=D.loc[D.survival,"stake"].dropna(),D.loc[D.growth,"stake"].dropna()
t3,p3=st.ttest_ind(r_,g_,equal_var=False); u3,pu=st.mannwhitneyu(r_,g_,alternative="two-sided")
sk["rescue_vs_growth"]=dict(diff=round(float(r_.mean()-g_.mean()),4),welch_p=round(float(p3),4),mwu_p=round(float(pu),4))
print(f"  rescue−growth 지분율 차이 {100*sk['rescue_vs_growth']['diff']:+.2f}pp Welch p={p3:.4f} · MWU p={pu:.4f}")
R["H_stake_by_purpose"]=sk
L=R["G_ladder"]
verdict2=(f"통제 사다리(분류전용): " + " · ".join(f"{k.split(') ')[1]} {v['coef']:+.4f}{v['hc1_ci']}" for k,v in L.items()) +
          f". 지분율 rescue {100*sk['rescue']['median']:.2f}% vs growth {100*sk['growth']['median']:.2f}% (MWU p={sk['rescue_vs_growth']['mwu_p']}).")
R["verdict_ladder"]=verdict2; print("\n"+verdict2)


print("\n[6] 종속변수별 사다리 — 원고가 목적분할의 primary 로 선언한 BMP 표준화(scar11) 및 [0,+5] 창")
for dep,lab in (("scar11","BMP 표준화 [−1,+1]"),("car05","원CAR [0,+5]"),("scar05","BMP 표준화 [0,+5]")):
    if dep not in CL.columns: continue
    CLd=CL.dropna(subset=[dep])
    if len(CLd)<60: continue
    print(f"  -- {lab} (n={len(CLd)})")
    R[f"I_ladder_{dep}"]={t:reg2(CLd,c_,y_,"    "+t,dep) for t,c_,y_ in LAD}

A=R.get("A_classified_only") or {}; s=A.get("survival",{})
verdict=(f"분류전용 rescue 계수 {s.get('coef')} · HC1 CI {s.get('hc1',{}).get('ci')} · 연월군집 CI {s.get('cluster_ym',{}).get('ci')} (n={A.get('n')}). "
         f"미분류 평균 {R['D_unclassified']['mean'] if R.get('D_unclassified') else None}. "
         f"공통표본 rescue−growth {R.get('F_overlap_welch',{}).get('diff')} p={R.get('F_overlap_welch',{}).get('welch_p')}.")
json.dump({"id":"WP13d","title":"목적-CAR 통제회귀·미분류 gapfill·시장실물 공통표본","runs":R,"verdict":verdict,
           "provenance":"CAR=wp10b_car_vw.csv(317, 값비중 프록시) · stake=wp10a_stake.csv · dealsize=PitchBook Deal Size(k별 max) · firm size=NPS log고용 중위 · 표본기간 2015–2025 · 고용 1차표본=emp_primary_k.txt(210)",
           "kill":"분류전용 rescue 계수 CI 가 0 포함 → 초록·§5.1 '통제 후에도 유지' 철회"},
          open(f"{O}/wp13d_market_gapfill.json","w"),ensure_ascii=False,indent=1)
print("\n"+verdict)
