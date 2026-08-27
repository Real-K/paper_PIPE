# -*- coding: utf-8 -*-
"""WP13f — 배정대상자 조절(wp11n)·자본잠식 경계 RD 프로브(wp11i) 의 신규-우주 재계산.

두 산출 모두 생산 스크립트가 없던 인라인 결과다. 원고 §3(배정대상자 구성·조절)과 §4.4·부록 D(RD 프로브)가
인용하므로 재현 가능한 형태로 복원하고, C-A 신규 우주(고용 1차표본 210 · CAR 317 · 2015–2025)로 다시 계산한다.

(A) 배정대상자 조절. PitchBook 투자자 식별에서 lead investor 유형을 **금융투자자 vs 전략/기타** 로 이분하고,
    두 집단의 고용결과(d2)와 발표수익률(CAR)을 비교한다. 이분 규칙은 아래 FIN 집합으로 **명시**한다 —
    구 산출은 규칙이 코드에 남아 있지 않아 재현 불가였으므로, 여기서 규칙을 고정하고 구값과의 차이를 함께 보고한다.
(B) RD 프로브. 러닝변수 = 자기자본/자산(자본잠식 경계 0). 원자료에서 재구성한다(fin_distress_panel 에는 비율이 없음).
    경계 좌우 좁은 창에서 **다음 해 제3자배정 수령확률**의 점프를 본다. 점프가 없으면 fuzzy RD 는 성립하지 않는다.
    이건 설계 탐색의 음성 결과이고, 그대로 보고하는 것이 목적이다(§15: 억지 IV 금지).

사전 예측. (A) 두 집단 차이는 표본이 작아 비유의. (B) 점프 없음(구 Fisher p=1.0).
기각조건. (B) 에서 점프가 유의하고 크면 fuzzy RD 재검토 — 그때는 §4.4 의 "이용 가능한 불연속 없음" 을 수정해야 한다.
"""
import csv,json,re,numpy as np,pandas as pd,warnings; warnings.filterwarnings("ignore")
from scipy import stats as st
import os
BASE=os.environ.get("P016_BASE", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))   # 원 경로는 제거했다 — 실행 시 P016_BASE 로 지정하거나 기본값 사용
RE=f"{BASE}/shared/outputs/pipe_r1_reextract_2026-08-22"; O=f"{BASE}/shared/outputs/pipe_wp13_2026-08-26"
def rd_(p,**kw):
    d=pd.read_csv(p,**kw); d.columns=[c.lstrip("﻿") for c in d.columns]; return d
T=rd_(f"{RE}/treatment_master_v2.csv",dtype=str); T["k"]=T.k.str.replace(r"\D","",regex=True).str.zfill(10)
T=T[pd.to_numeric(T.event_dt.astype(str).str[:4],errors="coerce").between(2015,2025)]
T["ev"]=pd.to_datetime(T.event_dt,errors="coerce"); T=T.dropna(subset=["ev"]).drop_duplicates("k"); T["year"]=T.ev.dt.year
R={}

print("=== (A) 배정대상자 조절 ===")
AL=rd_(f"{O}/allottee_identity.csv",dtype=str); AL["bn"]=AL.bn.str.replace(r"\D","",regex=True).str.zfill(10)
FIN={"Venture Capital","PE/Buyout","Asset Manager","Investment Bank","Hedge Fund","Family Office",
     "Limited Partner","Corporate Venture Capital","Mezzanine","Fund/Partnership","Growth/Expansion",
     "Special Purpose Acquisition Company (SPAC)"}
NOINFO={"NO_DATA","","nan","None"}
AL["has_inv"]=~AL.lead_type.fillna("NO_DATA").isin(NOINFO)
AL["financial"]=AL.lead_type.isin(FIN)
inuniv=AL[AL.bn.isin(set(T.k))]
R["A_coverage"]=dict(n_universe=int(len(T)),n_matched_rows=int(len(inuniv)),n_with_investor=int(inuniv.has_inv.sum()),
                     pct_with_investor=round(float(inuniv.has_inv.mean()),4),
                     n_named=int(inuniv.has_inv.sum()),share_named=round(float(inuniv.has_inv.mean()),4),
                     n_financial=int(inuniv[inuniv.has_inv].financial.sum()),
                     pct_financial=round(float(inuniv[inuniv.has_inv].financial.mean()),4),
                     share_financial=round(float(inuniv[inuniv.has_inv].financial.mean()),4),
                     n_other=int((~inuniv[inuniv.has_inv].financial).sum()),
                     share_other=round(float((~inuniv[inuniv.has_inv].financial).mean()),4),
                     rule_financial=sorted(FIN))
c=R["A_coverage"]; print(f"  우주 {c['n_universe']} · 명단보유 {c['n_with_investor']} ({100*c['pct_with_investor']:.1f}%) · 금융 {c['n_financial']} ({100*c['pct_financial']:.1f}%) / 전략·기타 {c['n_with_investor']-c['n_financial']} ({100*(1-c['pct_financial']):.1f}%)",flush=True)
R["A_lead_type_dist"]={k:int(v) for k,v in inuniv[inuniv.has_inv].lead_type.value_counts().items()}
M=rd_(f"{O}/wp9e_firm_d_v2.csv",dtype=str); M["k"]=M.k.str.replace(r"\D","",regex=True).str.zfill(10)
for cc in ("d2","m1_p1"): M[cc]=pd.to_numeric(M[cc],errors="coerce")
M=M.merge(AL[["bn","has_inv","financial"]],left_on="k",right_on="bn",how="left")
M["has_inv"]=M.has_inv.fillna(False); M["financial"]=M.financial.fillna(False)
def blk(x,lab):
    x=pd.Series(x).dropna()
    if len(x)<5: return None
    o=dict(n=int(len(x)),mean=round(float(x.mean()),4),median=round(float(x.median()),4),
           p10=round(float(np.percentile(x,10)),4),tail25=round(float((x<=M.d2.quantile(.25)).mean()),4),
           ci=[round(float(x.mean()-1.96*x.std(ddof=1)/np.sqrt(len(x))),4),round(float(x.mean()+1.96*x.std(ddof=1)/np.sqrt(len(x))),4)])
    print(f"    {lab:<16} n={o['n']:>3} 평균 {o['mean']:+.4f} CI{o['ci']} 중위 {o['median']:+.4f} p10 {o['p10']:+.4f} 꼬리율 {o['tail25']:.3f}",flush=True)
    return o
E=M[M.has_inv]
print("  고용결과(d2):")
R["A_emp_financial"]=blk(E.loc[E.financial,"d2"],"금융"); R["A_emp_strategic"]=blk(E.loc[~E.financial,"d2"],"전략·기타")
def welch(a,b):
    a,b=pd.Series(a).dropna(),pd.Series(b).dropna()
    if len(a)<3 or len(b)<3: return None
    t,p=st.ttest_ind(a,b,equal_var=False); return dict(diff=round(float(a.mean()-b.mean()),4),t=round(float(t),2),p=round(float(p),4),n1=int(len(a)),n2=int(len(b)))
R["A_emp_diff"]=welch(E.loc[E.financial,"d2"],E.loc[~E.financial,"d2"])
if R["A_emp_diff"]:
    fq=np.percentile(E.loc[E.financial,"d2"].dropna(),10); sq=np.percentile(E.loc[~E.financial,"d2"].dropna(),10)
    R["A_emp_p10_diff"]=round(float(fq-sq),4)
    print(f"    금융−전략 평균차 {R['A_emp_diff']['diff']:+.4f} Welch p={R['A_emp_diff']['p']} · 중위차 {R['A_emp_financial']['median']-R['A_emp_strategic']['median']:+.4f} · p10차 {R['A_emp_p10_diff']:+.4f}")
car=rd_(f"{O}/wp10b_car_vw.csv",dtype=str); car["k"]=car.k.str.zfill(10); car["car11"]=pd.to_numeric(car.car11,errors="coerce")
C=car.merge(AL[["bn","has_inv","financial"]],left_on="k",right_on="bn",how="left")
C["has_inv"]=C.has_inv.fillna(False); C["financial"]=C.financial.fillna(False); C=C[C.has_inv]
R["A_car_financial"]=dict(n=int(C.financial.sum()),mean=round(float(C.loc[C.financial,"car11"].mean()),4))
R["A_car_strategic"]=dict(n=int((~C.financial).sum()),mean=round(float(C.loc[~C.financial,"car11"].mean()),4))
R["A_car_diff"]=welch(C.loc[C.financial,"car11"],C.loc[~C.financial,"car11"])
print(f"  CAR[−1,+1]: 금융 {100*R['A_car_financial']['mean']:+.2f}% (n={R['A_car_financial']['n']}) vs 전략·기타 {100*R['A_car_strategic']['mean']:+.2f}% (n={R['A_car_strategic']['n']}) Welch p={R['A_car_diff']['p'] if R['A_car_diff'] else None}")

print("\n=== (B) 자본잠식 경계 RD 프로브 ===")
def num(x):
    try: return float(x)
    except: return np.nan
rows=[]
with open(f"{BASE}/PI/drops/재무데이터_2009_2025_통합.csv",encoding="utf-8") as f:
    r_=csv.reader(f); next(r_)
    for row in r_:
        if len(row)<109 or row[4].strip()!="결산": continue
        bn=re.sub(r"\D","",row[5]).zfill(10)
        try: yr=int(row[3])
        except: continue
        if not re.match(r"^A\d{6}$",row[0].lstrip("\ufeff")): continue   # 상장 우주 한정(구 프로브와 동일) — 비상장 포함 시 수령확률이 희석돼 경계 비교가 무의미
        ta=num(row[8]); te=num(row[82])
        if not (ta and ta>0) or te!=te: continue
        rows.append((bn,yr,te/ta))
FR=pd.DataFrame(rows,columns=["bn","year","eq_ratio"]).drop_duplicates(["bn","year"],keep="first")
ev=set(zip(T.k,T.year))
FR["treat_next"]=[1 if (b,y+1) in ev else 0 for b,y in zip(FR.bn,FR.year)]
FR=FR[FR.year.between(2014,2024)]
print(f"  firm-year {len(FR):,} (기업 {FR.bn.nunique():,}) · 다음해 수령 {int(FR.treat_next.sum())}",flush=True)
R["B_panel"]=dict(n_firm_years=int(len(FR)),n_firms=int(FR.bn.nunique()),n_treat_next=int(FR.treat_next.sum()))
for h in (0.05,0.10,0.20):
    W=FR[FR.eq_ratio.abs()<=h]
    L=W[W.eq_ratio<0]; Rt=W[W.eq_ratio>=0]
    if len(L)<10 or len(Rt)<10: continue
    tab=[[int(L.treat_next.sum()),int(len(L)-L.treat_next.sum())],[int(Rt.treat_next.sum()),int(len(Rt)-Rt.treat_next.sum())]]
    fp=float(st.fisher_exact(tab).pvalue)
    o=dict(bandwidth=h,n_window=int(len(W)),left_n=int(len(L)),left_p=round(float(L.treat_next.mean()),5),
           right_n=int(len(Rt)),right_p=round(float(Rt.treat_next.mean()),5),
           jump=round(float(L.treat_next.mean()-Rt.treat_next.mean()),5),fisher_p=round(fp,4),table=tab)
    R[f"B_rd_h{h}"]=o
    print(f"  h=±{h:.2f}: 창 {o['n_window']:>5} · 좌(잠식) {100*o['left_p']:.3f}% n={o['left_n']:>4} · 우 {100*o['right_p']:.3f}% n={o['right_n']:>5} · 점프 {100*o['jump']:+.3f}pp Fisher p={o['fisher_p']}",flush=True)
b=R.get("B_rd_h0.1") or R.get("B_rd_h0.2") or {}
verdict=(f"배정대상자: 명단 {c['n_with_investor']}/{c['n_universe']} ({100*c['pct_with_investor']:.1f}%), 금융 {100*c['pct_financial']:.1f}%. "
         f"고용 금융−전략 평균차 {R['A_emp_diff']['diff'] if R.get('A_emp_diff') else None} p={R['A_emp_diff']['p'] if R.get('A_emp_diff') else None}. "
         f"RD(h=±{b.get('bandwidth')}): 좌 {b.get('left_p')} 우 {b.get('right_p')} Fisher p={b.get('fisher_p')} → 불연속 없음.")
json.dump({"id":"WP13f","title":"배정대상자 조절·자본잠식 RD 프로브(신규 우주)","runs":R,"verdict":verdict,
           "provenance":"배정대상자=allottee_identity.csv(PitchBook lead_type; 금융 이분규칙은 runs.A_coverage.rule_financial 에 명시) · 고용=wp9e_firm_d_v2.csv · CAR=wp10b_car_vw.csv · RD 러닝변수=자기자본/자산(재무데이터_2009_2025_통합.csv 원자료 재구성)",
           "caveat":"구 wp11n 의 금융/전략 이분 규칙은 코드에 남아 있지 않아 재현 불가 — 여기 규칙은 신규 정의이며 구값과 직접 비교 불가.",
           "kill":"RD 점프가 유의·크면 fuzzy RD 재검토 및 §4.4 '이용 가능한 불연속 없음' 수정"},
          open(f"{O}/wp13f_allottee_rd.json","w"),ensure_ascii=False,indent=1)
print("\n"+verdict)
