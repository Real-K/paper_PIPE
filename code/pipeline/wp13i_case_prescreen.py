# -*- coding: utf-8 -*-
"""WP13i — 꼬리 사례감사 자동 사전선별 (WP-A 1단계).

목적. 하위 30 사례의 고용 급감이 **실제 수축**인지 **측정 인공물**(분할·합병·영업양도·주식교환·사업장 이관)인지
DART 공시목록으로 1차 선별한다. NPS 는 사업자번호 단위라 법인 분할·영업양도가 있으면 '고용 붕괴' 로 보인다.
수작업 등기 조회는 여기서 걸러지지 않은 건에만 하면 된다.

방법. 각 사례의 이벤트 전후 [−6, +12] 개월 DART 공시목록을 받아 **구조변경 공시**를 탐지한다.
탐지어는 공시 제목 기준이며, 오탐(단순 정정·자회사 건)을 줄이려고 보고서명에 직접 걸린 것만 센다.
결과는 사람이 판정할 수 있도록 **매칭된 공시 제목과 접수일자를 그대로 싣는다**(자동 판정 아님).
"""
import os,json,time,itertools,urllib.request,urllib.parse,warnings; warnings.filterwarnings("ignore")
import pandas as pd
BASE=os.environ.get("P016_BASE", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))   # 원 경로는 제거했다 — 실행 시 P016_BASE 로 지정하거나 기본값 사용
RV=f"{BASE}/papers/P016_pipe-employment/09_review"
keys=[l.split("=",1)[1].strip() for l in open(os.path.expanduser("~/.claude/.env")) if l.startswith("DART_API_KEY") and l.split("=",1)[1].strip()]
assert keys,"DART_API_KEY 없음"
kc=itertools.cycle(keys); print(f"DART 키 {len(keys)}개",flush=True)
def dget(ep,p):
    for _ in range(3):
        try:
            p=dict(p); p["crtfc_key"]=next(kc)
            return json.load(urllib.request.urlopen(f"https://opendart.fss.or.kr/api/{ep}?"+urllib.parse.urlencode(p),timeout=25))
        except Exception: time.sleep(0.5)
    return {}
STRUCT={"분할":"회사분할","합병":"합병","영업양수":"영업양수도","영업양도":"영업양수도","주식교환":"주식교환·이전",
        "주식이전":"주식교환·이전","자산양수":"자산양수도","자산양도":"자산양수도"}
A=pd.read_csv(f"{RV}/WP_A_case_audit_targets.csv",dtype={"k":str,"cc":str,"sc":str})
A["evd"]=pd.to_datetime(A.evd)
rows=[]
for r in A.itertuples():
    bgn=(r.evd-pd.DateOffset(months=6)).strftime("%Y%m%d"); end=(r.evd+pd.DateOffset(months=12)).strftime("%Y%m%d")
    hits=[]
    if isinstance(r.cc,str) and r.cc.strip():
        for ty in ("A","B","C","I"):   # 정기·주요사항·발행·기타
            R=dget("list.json",{"corp_code":r.cc,"bgn_de":bgn,"end_de":end,"pblntf_ty":ty,"page_count":"100"})
            for it in (R.get("list") or []):
                nm=it.get("report_nm","")
                for kw,cat in STRUCT.items():
                    if kw in nm: hits.append((it.get("rcept_dt",""),cat,nm)); break
            time.sleep(0.03)
    hits=sorted(set(hits))
    cats=sorted({c for _,c,_ in hits})
    rows.append(dict(rank=r.rank,k=r.k,cc=r.cc,sc=r.sc,evd=r.evd.date().isoformat(),purpose=r.purpose,
                     d2=r.d2,emp_m1=r.emp_m1,emp_p12=r.emp_p12,delist_susp=r.delist_susp,
                     n_struct_filings=len(hits),struct_categories="; ".join(cats),
                     struct_filings=" | ".join(f"{d} {c}: {n}" for d,c,n in hits[:6]),
                     prescreen="구조변경 공시 있음 — 등기 확인 필요" if hits else "구조변경 공시 없음 — 실제 수축 추정"))
    print(f"  [{r.rank:>2}] {r.sc} {r.evd.date()} {r.purpose:<12} 구조변경 {len(hits)}건 {('· '+', '.join(cats)) if cats else ''}",flush=True)
D=pd.DataFrame(rows); D.to_csv(f"{RV}/WP_A_case_prescreen.csv",index=False,encoding="utf-8-sig")
n_hit=int((D.n_struct_filings>0).sum())
print(f"\n=== 사전선별 완료 === 구조변경 공시 보유 {n_hit}/{len(D)} ({100*n_hit/len(D):.0f}%) — 이 건들만 등기 확인 필요")
print("범주 분포:",D[D.n_struct_filings>0].struct_categories.value_counts().to_dict())
json.dump(dict(id="WP13i",n_cases=len(D),n_with_struct_filing=n_hit,
               note="자동 판정 아님 — 공시 제목 탐지 결과이며, 사람이 원문을 확인해 최종 코딩한다. 탐지어는 회사분할·합병·영업양수도·주식교환/이전·자산양수도.",
               window="event −6 ~ +12 months · pblntf_ty A/B/C/I"),
          open(f"{BASE}/shared/outputs/pipe_wp13_2026-08-26/wp13i_case_prescreen.json","w"),ensure_ascii=False,indent=1)
