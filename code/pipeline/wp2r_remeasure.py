# -*- coding: utf-8 -*-
"""P-016 WP2-재측정 (R1 교정 처치 415/382 입력). outcome-blind: 커버리지·balance·placebo·usable-ES 만.
치료효과(rel@k, treated-control 고용차) 미산출 — WP3 동결 전 금지.
입력: treatment_master_v2.csv (415, event 382) · nps_monthly_matched_v2.parquet · pitchbook_all_status_v1.csv
산출: shared/outputs/pipe_wp2_2026-08-22/wp2r_panel.json
"""
import json,warnings,collections,math; warnings.filterwarnings("ignore")
import pandas as pd,numpy as np
import os
BASE=os.environ.get("P016_BASE", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))   # 원 경로는 제거했다 — 실행 시 P016_BASE 로 지정하거나 기본값 사용
RE=f"{BASE}/shared/outputs/pipe_r1_reextract_2026-08-22"
OUT=f"{BASE}/shared/outputs/pipe_wp2_2026-08-22"

T=pd.read_csv(f"{RE}/treatment_master_v2.csv",dtype=str)
T["k"]=T["k"].str.replace(r'\D','',regex=True).str.zfill(10)
T["ev"]=pd.to_datetime(T["event_dt"],errors="coerce").dt.to_period("M")
Tev=T.dropna(subset=["ev"]).drop_duplicates("k")
print(f"처치 마스터 {len(T)} · 이벤트일 보유 {len(Tev)}",flush=True)

nps=pd.read_parquet(f"{BASE}/shared/data/processed/nps_monthly_matched_v2.parquet",
                    columns=["bn10","data_ym","가입자수","업종","시도"])
nps["ym"]=pd.PeriodIndex(nps["data_ym"],freq="M")
nps_firms=set(nps.bn10.unique())
mn,mx=nps.ym.min(),nps.ym.max()
print(f"NPS {nps.bn10.nunique()}사 {mn}~{mx}",flush=True)

# 처치-패널 교집합
Tin=Tev[Tev.k.isin(nps_firms)].copy()
n_in=len(Tin)
# 이벤트 캘린더 feasibility
Tin["ev_before_start"]=Tin.ev<mn
Tin["ev_after_nopost"]=Tin.ev> (mx-12)
cal=dict(in_nps=n_in,
         ev_before_data_start=int(Tin.ev_before_start.sum()),
         ev_after_no_full_post=int(Tin.ev_after_nopost.sum()),
         ev_in_full_window=int(((~Tin.ev_before_start)&(~Tin.ev_after_nopost)).sum()))

# firm별 관측 월 집합
g=nps.groupby("bn10")["ym"].apply(lambda s:set(s))
def prepost(k,ev,preN,postN):
    obs=g.get(k,set())
    pre=sum(1 for m in range(1,preN+1) if (ev-m) in obs)
    post=sum(1 for m in range(1,postN+1) if (ev+m) in obs)
    return pre,post
def count_usable(preN,postN,need_pre,need_post):
    c=0
    for r in Tin.itertuples():
        pre,post=prepost(r.k,r.ev,preN,postN)
        if pre>=need_pre and post>=need_post: c+=1
    return c
usable=dict(
    ge1pre_ge1post_win13_12=count_usable(13,12,1,1),
    ge3pre_ge3post=count_usable(13,12,3,3),
    ge6pre_ge6post=count_usable(13,12,6,6),
    full_pre13_post12=count_usable(13,12,13,12),
    note="corrected 382 입력. WP1 보고 usable N=213(폐기)·구 wp2b 브래킷 244와 대조.")
print("usable:",usable,flush=True)

# covariate coverage (event월 baseline 가입자수·업종2·시도, pre-growth)
npsi=nps.set_index(["bn10","ym"]).sort_index()
def cov_at(k,ev):
    obs=g.get(k,set())
    # baseline: event월 또는 최근접 ±2월
    for d in (0,-1,1,-2,2):
        if (ev+d) in obs:
            try: row=npsi.loc[(k,ev+d)];
            except: continue
            row=row.iloc[0] if isinstance(row,pd.DataFrame) else row
            return row
    return None
size=[];ind=[];reg=[];pg=[]
for r in Tin.itertuples():
    row=cov_at(r.k,r.ev); obs=g.get(r.k,set())
    if row is not None:
        size.append(float(row["가입자수"])); ind.append(str(row["업종"])[:2]); reg.append(str(row["시도"]))
    pre2=sum(1 for m in range(1,13) if (r.ev-m) in obs)
    pg.append(1 if pre2>=2 else 0)
cover=dict(n_in_nps=n_in,
           baseline_size=round(100*len(size)/n_in,1),
           industry2=round(100*len(ind)/n_in,1),
           region=round(100*len(reg)/n_in,1),
           pregrowth_ge2pre=round(100*sum(pg)/n_in,1))
print("coverage:",cover,flush=True)

# balance: treated baseline log가입자수 vs control pool (never-pipe firm median)
pb=pd.read_csv(f"{BASE}/shared/data/processed/pitchbook_all_status_v1.csv",dtype=str)
pbbn=set(pb["bn"].astype(str).str.replace(r'\D','',regex=True).str.zfill(10).dropna())
ctrl_firms=nps_firms - pbbn
cmed=nps[nps.bn10.isin(ctrl_firms)].groupby("bn10")["가입자수"].median()
c_log=np.log1p(cmed.values); c_log=c_log[np.isfinite(c_log)]
t_log=np.log1p(np.array(size)); t_log=t_log[np.isfinite(t_log)]
pooled=math.sqrt((t_log.var(ddof=1)+c_log.var(ddof=1))/2)
smd=float((t_log.mean()-c_log.mean())/pooled) if pooled>0 else None
# common support: treated 업종2/시도가 control에 존재?
c_ind=set(nps[nps.bn10.isin(ctrl_firms)]["업종"].astype(str).str[:2].unique())
c_reg=set(nps[nps.bn10.isin(ctrl_firms)]["시도"].astype(str).unique())
ind_nosupport=sorted(set(ind)-c_ind); reg_nosupport=sorted(set(reg)-c_reg)
balance=dict(control_pool_never_pipe=len(ctrl_firms),
             treated_baseline_logsize_mean=round(float(t_log.mean()),4),treated_n=len(t_log),
             control_logsize_mean=round(float(c_log.mean()),4),control_n=int(len(c_log)),
             smd_baseline_logsize=round(smd,4) if smd else None,
             industry2_treated_without_control_support=ind_nosupport,
             region_treated_without_control_support=reg_nosupport)
print("balance:",balance,flush=True)

# placebo universe (주주배정·공모·non_third) — r1b + r1c 비처치
import csv
b=list(csv.DictReader(open(f"{RE}/r1b_classified.csv",encoding='utf-8')))
mb={c.strip().lstrip('﻿'):c for c in b[0].keys()}
def tf(x): return str(x).strip().lower() in ("1","true")
rights=sum(1 for r in b if tf(r.get(mb.get("rights",""),"")) and not tf(r.get(mb["is_treat_3rd"],"")))
public=sum(1 for r in b if tf(r.get(mb.get("public",""),"")) and not tf(r.get(mb["is_treat_3rd"],"")))
c=list(csv.DictReader(open(f"{RE}/r1c_resolved.csv",encoding='utf-8')))
mc={cc.strip().lstrip('﻿'):cc for cc in c[0].keys()}
nonthird_r1c=sum(1 for r in c if r.get(mc.get("verdict",""),"")=="non_third")
placebo=dict(rights_only=rights,public_only=public,nonthird_r1c=nonthird_r1c,total=rights+public+nonthird_r1c,
             note="placebo(비처치 유상증자/CB) 우주 — 여전히 소규모. rule 11: placebo는 점추정+CI 함께 보고.")
print("placebo:",placebo,flush=True)

res=dict(id="P016-WP2R", date="2026-08-22", outcome_blind_attestation="치료효과 미산출: 커버리지·balance·placebo·usable-ES 만.",
         treatment_input="treatment_master_v2.csv (415, event 382)",
         calendar_feasibility=cal, usable_es_subset=usable, treated_covariate_coverage=cover,
         balance_input=balance, placebo_universe=placebo)
json.dump(res,open(f"{OUT}/wp2r_panel.json","w"),ensure_ascii=False,indent=1)
print("\n=== WP2 재측정 완료 ===")
print(f"처치-패널 교집합 {n_in} · full-window {cal['ev_in_full_window']} · usable(≥1/≥1) {usable['ge1pre_ge1post_win13_12']} · SMD {balance['smd_baseline_logsize']}")
open(f"{OUT}/wp2r.done","w").write("done")
