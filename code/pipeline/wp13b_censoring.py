# -*- coding: utf-8 -*-
"""WP13b — 우측절단(리뷰1 핵심문제5) 정면 대응.
(a) 완전관측 표본: 1차표본 210 중 +1..+12 전부 관측 208 — own-Δ 분포 통계 재계산(표본 재구성 없이 부분집합).
(b) 조기이탈 경계: 창 가능(e−13/e+12) 이벤트 중 1차규칙 탈락 조기이탈 9건을 전부 붕괴(D≤−0.60)로 코딩한
    worst-case 꼬리 상한 — 1차 추정이 꼬리 주장에 보수적임을 수치로 보임.
(c) pseudo-date 창은 정의상 완전(처치 도달 생존) → 절단은 event 쪽 꼬리만 깎는 방향 = 보수성 방향 서술 근거.
"""
import json,numpy as np,pandas as pd
import os
BASE=os.environ.get("P016_BASE", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))   # 원 경로는 제거했다 — 실행 시 P016_BASE 로 지정하거나 기본값 사용; O=f"{BASE}/shared/outputs/pipe_wp13_2026-08-26"
T=pd.read_csv(f"{BASE}/shared/outputs/pipe_r1_reextract_2026-08-22/treatment_master_v2.csv",dtype=str); T["k"]=T.k.str.replace(r"\D","",regex=True).str.zfill(10)
T["ev"]=pd.to_datetime(T.event_dt,errors="coerce").dt.to_period("M"); T=T.dropna(subset=["ev"]).drop_duplicates("k")
PRIM={l.strip() for l in open(f"{O}/emp_primary_k.txt") if l.strip()}
nps=pd.read_parquet(f"{BASE}/shared/data/processed/nps_monthly_matched_v2.parquet",columns=["bn10","data_ym","가입자수"])
nps["ym"]=pd.PeriodIndex(nps.data_ym,freq="M"); months=pd.period_range(nps.ym.min(),nps.ym.max(),freq="M"); mi={m:j for j,m in enumerate(months)}; NM=len(months)
piv=nps.pivot_table(index="bn10",columns="ym",values="가입자수",aggfunc="mean").reindex(columns=months); fx={b:i for i,b in enumerate(piv.index)}
LEr=piv.to_numpy(float); LE=np.log1p(LEr)
rows=[]
for r in T.itertuples():
    e=mi.get(r.ev)
    if e is None or r.k not in fx or e-13<0 or e+12>=NM: continue
    row=LE[fx[r.k]]; fin=np.isfinite(row)
    D=float(np.nanmean(row[e+7:e+13])-np.nanmean(row[e-12:e])) if (fin[e-12:e].sum()>=6 and fin[e+7:e+13].sum()>=3) else np.nan
    last=int(np.where(fin)[0].max()) if fin.any() else -1
    rows.append(dict(k=r.k,e=e,prim=r.k in PRIM,D=D,complete12=bool(fin[e+1:e+13].sum()==12),exit12=bool(last<e+12),post7_12=int(fin[e+7:e+13].sum())))
A=pd.DataFrame(rows); P=A[A.prim]
def stats(d):
    d=d[np.isfinite(d)]
    return dict(n=len(d),mean=round(float(d.mean()),4),median=round(float(np.median(d)),4),p10=round(float(np.percentile(d,10)),4),
                c35=round(float(np.mean(d<=-0.35)),4),c60=round(float(np.mean(d<=-0.60)),4))
full=stats(P.D.values); comp=stats(P[P.complete12].D.values)
# 부트스트랩: 완전관측 vs 전체 차이 CI (동일표본 재표집)
RNG=np.random.default_rng(20260827); B=4000
dif={k:[] for k in ("median","p10","c35")}
d_all=P.D.values[np.isfinite(P.D.values)]; d_cmp=P[P.complete12].D.values
for _ in range(B):
    ia=RNG.integers(0,len(d_all),len(d_all)); ic=RNG.integers(0,len(d_cmp),len(d_cmp))
    dif["median"].append(np.median(d_cmp[ic])-np.median(d_all[ia])); dif["p10"].append(np.percentile(d_cmp[ic],10)-np.percentile(d_all[ia],10))
    dif["c35"].append(np.mean(d_cmp[ic]<=-0.35)-np.mean(d_all[ia]<=-0.35))
dci={k:[round(float(np.percentile(v,2.5)),4),round(float(np.percentile(v,97.5)),4)] for k,v in dif.items()}
# 이탈 경계: 창가능·1차탈락·조기이탈 → D:=-0.75 (모든 격자 임계 이하) worst case
EX=A[(~A.prim)&(A.exit12)]
d_wc=np.r_[d_all,np.full(len(EX),-0.75)]
wc=stats(d_wc)
res=dict(id="WP13b",n_primary=int(P.shape[0]),n_complete12=int(P.complete12.sum()),n_excluded_early_exit=int(EX.shape[0]),
         full=full,complete12=comp,diff_complete_minus_full_ci=dci,worst_case_exits_as_collapse=wc,
         note="pseudo-date 창은 처치 도달 생존으로 정의상 완전 → 절단은 event 꼬리만 축소(보수적). worst-case 는 탈락 조기이탈 전건을 D=-0.75 로 코딩.")
json.dump(res,open(f"{O}/wp13b_censoring.json","w"),ensure_ascii=False,indent=1)
print("1차",full,"\n완전12",comp,"\n차이CI",dci,"\n이탈",len(EX),"건 worst-case",wc)
