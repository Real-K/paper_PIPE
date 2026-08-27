# -*- coding: utf-8 -*-
"""WP13a — 처치우주 v3: 기업(최초 이벤트) 단위 단일 플로우 파일 + 표본 흐름표.
목적(C-A): 205/207/210/212/215 로 갈라진 처치 표본 수를 **하나의 규칙 체계**로 통일하고, 모든 표가 같은 파일을 읽게 한다.
규칙(1차 고용표본 = Tables 3–5 공통): 이벤트월 e 가 패널 내, e−13 ≥ 0, e+12 < NM, 관측 e−1·e−13, 기저(−12..−1) ≥6개월, 결과(+7..+12) ≥3개월.
   보조: complete12 (+1..+12 전부 관측) · equity_only (cls==third_equity) · exit12 (마지막 관측 < e+12).
입력은 wp13 폴더(재실행 산출)에서 읽는다 — 배치 후 재실행하면 CAR·BHAR 플래그가 갱신된다.
"""
import json,numpy as np,pandas as pd
import os
BASE=os.environ.get("P016_BASE", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))   # 원 경로는 제거했다 — 실행 시 P016_BASE 로 지정하거나 기본값 사용
RE=f"{BASE}/shared/outputs/pipe_r1_reextract_2026-08-22"; O=f"{BASE}/shared/outputs/pipe_wp13_2026-08-26"
T=pd.read_csv(f"{RE}/treatment_master_v2.csv",dtype=str); T["k"]=T.k.str.replace(r"\D","",regex=True).str.zfill(10)
T["yr4"]=pd.to_numeric(T.event_dt.astype(str).str[:4],errors="coerce")
T["in_period"]=T.yr4.between(2015,2025)   # 표본기간 2015–2025(원고 명시)
T["ev"]=pd.to_datetime(T.event_dt,errors="coerce"); T["ev_m"]=T.ev.dt.to_period("M")
R=pd.read_csv(f"{RE}/r1_events.csv",dtype=str)[["k","n_dec","n_hits"]]; R["k"]=R.k.str.zfill(10)
nps=pd.read_parquet(f"{BASE}/shared/data/processed/nps_monthly_matched_v2.parquet",columns=["bn10","data_ym","가입자수"])
nps["ym"]=pd.PeriodIndex(nps.data_ym,freq="M"); months=pd.period_range(nps.ym.min(),nps.ym.max(),freq="M"); mi={m:j for j,m in enumerate(months)}; NM=len(months)
piv=nps.pivot_table(index="bn10",columns="ym",values="가입자수",aggfunc="mean").reindex(columns=months); fx={b:i for i,b in enumerate(piv.index)}; LE=piv.to_numpy(float); del nps,piv
def flags(k,evm):
    f=dict(in_nps=k in fx,e=np.nan,in_panel_range=False,window_feasible=False,emp_primary=False,complete12=False,exit12=False,n_pre=np.nan,n_post=np.nan,n_post7_12=np.nan,min3_rule=False)
    if not f["in_nps"] or pd.isna(evm) or evm not in mi: return f
    e=mi[evm]; row=LE[fx[k]]; fin=np.isfinite(row); f.update(e=e,in_panel_range=True)
    f["n_pre"]=int(fin[max(0,e-12):e].sum()); f["n_post"]=int(fin[e+1:min(NM,e+13)].sum()); f["n_post7_12"]=int(fin[e+7:min(NM,e+13)].sum())
    f["min3_rule"]=bool(f["n_pre"]>=3 and f["n_post"]>=3)
    if e-13<0 or e+12>=NM: return f
    f["window_feasible"]=True
    f["emp_primary"]=bool(fin[e-1] and fin[e-13] and fin[e-12:e].sum()>=6 and fin[e+7:e+13].sum()>=3)
    f["complete12"]=bool(fin[e+1:e+13].sum()==12); last=np.where(fin)[0].max(); f["exit12"]=bool(last<e+12)
    return f
F=pd.DataFrame([dict(k=r.k,**flags(r.k,r.ev_m)) for r in T.itertuples()])
U=T.merge(F,on="k").merge(R,on="k",how="left")
U["equity"]=U.cls.eq("third_equity"); U["dated"]=U.ev.notna()
U=U[U.in_period | ~U.dated]   # 기간 밖 사건 제외(날짜 없는 행은 흐름표 상단 계수용으로 유지)
def load(name,keycol="k",**kw):
    try: d=pd.read_csv(f"{O}/{name}",dtype=str,**kw); d.columns=[c.lstrip("﻿") for c in d.columns]; d[keycol]=d[keycol].str.replace(r"\D","",regex=True).str.zfill(10); return d
    except FileNotFoundError: return None
car=load("wp8b_car_firm.csv"); vw=load("wp10b_car_vw.csv"); fd=load("treatment_fdpp.csv"); st=load("wp10a_stake.csv"); fu=load("funding_dates.csv"); bh=load("wp9f_firm_bhar.csv"); cf=load("confound_flags.csv"); al=load("allottee_identity.csv",keycol="bn")
U["car_sample"]=U.k.isin(car.k) if car is not None else False
if vw is not None:
    v=vw.set_index("k"); U["purpose_classified"]=U.k.map(v.classified).isin(["True","1","1.0"]); U["rescue"]=U.k.map(v.survival).isin(["True","1","1.0"]); U["growth"]=U.k.map(v.growth).isin(["True","1","1.0"])
if fd is not None: U["fdpp_found"]=U.k.map(fd.set_index("k").fdpp_found).isin(["True","1","1.0"]); U["dom_purpose"]=U.k.map(fd.set_index("k").dom_purpose)
if st is not None: U["stake"]=pd.to_numeric(U.k.map(st.set_index("k").stake),errors="coerce")
if fu is not None: U["funding_lag_days"]=pd.to_numeric(U.k.map(fu.set_index("k").lag_days),errors="coerce")
if bh is not None: b=bh.set_index("k"); U["bhar_sample"]=U.k.isin(b.index); U["delist_suspect"]=U.k.map(b.delist_susp).isin(["True","1","1.0"]); U["bhar12"]=pd.to_numeric(U.k.map(b.bhar12),errors="coerce")
if cf is not None: U["confounded_broad"]=U.k.map(cf.set_index("k").confounded).isin(["True","1","1.0"])
if al is not None: U["lead_investor_type"]=U.k.map(al.set_index("bn").lead_type)
U["n_dec"]=pd.to_numeric(U.n_dec,errors="coerce")
U.to_csv(f"{O}/treatment_universe_v3.csv",index=False,encoding="utf-8-sig")
E=U[U.emp_primary]
flow=[("Treatment set (first third-party allotment per firm)",len(U),f"{int(U.equity.sum())} paid-in increases · {int((~U.equity).sum())} convertible bonds"),
      ("With identifiable event date in 2015–2025",int(U.dated.sum()),f"r1b {int((U.dated&U.src.eq('r1b')).sum())} · document-parsed r1c {int((U.dated&U.src.eq('r1c')).sum())}; 22 dated events fall outside the stated sample period (18 before 2015, 4 in 2026) and are excluded"),
      ("Event month inside NPS panel (2015-11..2026-05)",int(U.in_panel_range.sum()),f"{int(U.dated.sum()-U.in_panel_range.sum())} precede/follow the panel"),
      ("Window feasible (e−13 ≥ start, e+12 ≤ end)",int(U.window_feasible.sum()),""),
      ("Employment sample, primary rule",len(E),"obs at e−1 & e−13; ≥6 baseline months; ≥3 of months +7..+12"),
      ("— of which paid-in equity only",int(E.equity.sum()),f"{int((~E.equity).sum())} CB"),
      ("— of which complete 12-month follow-up",int(E.complete12.sum()),f"{int((~E.complete12).sum())} with gaps; {int(E.exit12.sum())} exit the panel before month +12"),
      ("— of which document-parsed dates (r1c)",int(E.src.eq('r1c').sum()),""),
      ("Loose rule (≥3 pre & ≥3 post), for reference",int(U.min3_rule.sum()),"legacy Table 1 '215' analogue"),
      ("Announcement CAR sample",int(U.car_sample.sum()),f"overlap with employment sample {int((U.car_sample&U.emp_primary).sum())}"),
      ("Purpose-classified (rescue+growth)",int(U.get('purpose_classified',pd.Series(False,index=U.index)).sum()),f"rescue {int(U.get('rescue',pd.Series(False,index=U.index)).sum())} · growth {int(U.get('growth',pd.Series(False,index=U.index)).sum())}"),
      ("Stake measured",int(U.stake.notna().sum()) if 'stake' in U else 0,""),
      ("Payment date parsed",int(U.funding_lag_days.notna().sum()) if 'funding_lag_days' in U else 0,""),
      ("BHAR sample",int(U.bhar_sample.sum()) if 'bhar_sample' in U else 0,f"delisting-suspect {int(U.delist_suspect.sum()) if 'delist_suspect' in U else 0}"),
      ("Exit the NPS panel within 12 months (all in-range events)",int(U.exit12.sum()),f"{int((U.exit12&U.min3_rule).sum())} pass the loose rule; {int((U.exit12&U.emp_primary).sum())} pass the primary rule")]
json.dump({"id":"WP13a","flow":[dict(step=a,n=b,note=c) for a,b,c in flow],"rule":"emp_primary: e-13>=0 & e+12<NM & obs(e-1,e-13) & pre(-12..-1)>=6 & post(+7..+12)>=3",
           "n_dec_note":"n_dec = r1_events 자본증가 결정공시 건수(모든 방식) — 반복 제3자배정 여부는 미측정(third_dates 비어 있음)"},open(f"{O}/wp13a_universe.json","w"),ensure_ascii=False,indent=1)
for a,b,c in flow: print(f"{b:>5}  {a}  {('· '+c) if c else ''}")
print("n_dec(자본증가 결정공시 수) 1차표본 분포:",E.n_dec.describe()[["50%","75%","max"]].to_dict(), "| ≥2:",int((E.n_dec>=2).sum()))
