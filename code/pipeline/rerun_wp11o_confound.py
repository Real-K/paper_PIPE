# WP13 재실행 사본 (2026-08-27): 정규화 마스터(382 dated)로 재실행. 원본 wp11o_confound.py · 출력 폴더만 pipe_wp13_2026-08-26 으로 치환.
# -*- coding: utf-8 -*-
"""WP11o — announcement-confound robustness.
각 처치 이벤트일 ±3일(달력) 창의 DART 공시목록을 조회해 배정 결정공시 외의 **중대 공시**를 식별,
오염 이벤트를 제외하고 (a) CAR·목적split (b) 고용 헤드라인을 재추정.
오염 범주: 실적변동·결산, 최대주주변경, 합병/분할/영업·자산양수도, 감사의견·의견거절, 횡령배임,
          관리종목·상장폐지, 자기주식, 무상증자, 타 사채발행, 소송·제재.
산출: shared/outputs/pipe_wp13_2026-08-26/wp11o_confound.json + confound_flags.csv
"""
import os,json,time,re,urllib.request,urllib.parse,itertools,warnings; warnings.filterwarnings("ignore")
import numpy as np,pandas as pd
from scipy import stats
BASE=os.environ.get("P016_BASE", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))   # 원 경로는 제거했다 — 실행 시 P016_BASE 로 지정하거나 기본값 사용
RE=f"{BASE}/shared/outputs/pipe_r1_reextract_2026-08-22"
OUT=f"{BASE}/shared/outputs/pipe_wp13_2026-08-26"
import sys; sys.path.insert(0,f"{BASE}/shared/lib")
from safe_dates import parse_dates
keys=[l.split("=",1)[1].strip() for l in open(os.path.expanduser("~/.claude/.env")) if l.startswith("DART_API_KEY") and l.split("=",1)[1].strip()]
kc=itertools.cycle(keys); print(f"DART 키 {len(keys)} (미출력)",flush=True)
def dget(ep,p):
    p=dict(p); p["crtfc_key"]=next(kc)
    for _ in range(3):
        try: return json.load(urllib.request.urlopen(f"https://opendart.fss.or.kr/api/{ep}?"+urllib.parse.urlencode(p),timeout=25))
        except: time.sleep(0.4)
    return {"status":"ERR"}
# 오염 판정 패턴 (배정 자체 공시는 제외)
SELF=re.compile(r"유상증자결정|전환사채권발행결정|신주인수권부사채권발행결정|교환사채권발행결정|증권발행실적보고서|증권신고서|투자설명서|정정신고")
CONF={
 "실적":re.compile(r"매출액또는손익구조|영업\(잠정\)실적|결산실적|잠정실적"),
 "지배구조":re.compile(r"최대주주변경|경영권|주식양수도|임원ㆍ주요주주|대표이사변경"),
 "구조조정":re.compile(r"합병|분할|영업양수|영업양도|자산양수|자산양도|주식교환|주식이전"),
 "감사":re.compile(r"감사보고서|감사의견|의견거절|한정의견|부적정"),
 "부정행위":re.compile(r"횡령|배임"),
 "상장위험":re.compile(r"관리종목|상장폐지|거래정지|실질심사"),
 "기타자본":re.compile(r"자기주식|무상증자|주식소각|감자"),
 "소송제재":re.compile(r"소송|제재|과징금|고발"),
}
T=pd.read_csv(f"{RE}/treatment_master_v2.csv",dtype=str)
T=T[pd.to_numeric(T.event_dt.astype(str).str[:4],errors="coerce").between(2015,2025)]   # 표본기간 2015–2025(원고 명시). 날짜 정규화로 유입된 2010–2014·2026 이벤트 제외 — WP13, 2026-08-27
T["k"]=T["k"].str.replace(r'\D','',regex=True).str.zfill(10)
T["ev"]=parse_dates(T.event_dt,label="event_dt")
T=T.dropna(subset=["ev"]).drop_duplicates("k")
print(f"이벤트일 보유 {len(T)}",flush=True)
rows=[]
for i,r in enumerate(T.itertuples(),1):
    bgn=(r.ev-pd.Timedelta(days=3)).strftime("%Y%m%d"); end=(r.ev+pd.Timedelta(days=3)).strftime("%Y%m%d")
    names=[]
    for ty in ("A","B","C","D","E","F","I"):
        R=dget("list.json",{"corp_code":r.cc,"bgn_de":bgn,"end_de":end,"pblntf_ty":ty,"page_count":"100"})
        if R.get("status")!="000": continue
        names += [it.get("report_nm","") for it in R.get("list",[])]
    hits={}
    for nm in names:
        if SELF.search(nm): continue
        for lab,pat in CONF.items():
            if pat.search(nm): hits.setdefault(lab,[]).append(nm[:44])
    rows.append(dict(k=r.k,cc=r.cc,ev=str(r.ev.date()),n_filings=len(names),
                     confounded=int(bool(hits)),cats="|".join(sorted(hits)),
                     example=(list(hits.values())[0][0] if hits else "")))
    if i%50==0:
        c=sum(x["confounded"] for x in rows); print(f"  [{i}/{len(T)}] 오염 {c} ({100*c/i:.0f}%)",flush=True)
    time.sleep(0.03)
C=pd.DataFrame(rows); C.to_csv(f"{OUT}/confound_flags.csv",index=False,encoding="utf-8-sig")
import collections
catc=collections.Counter(x for r_ in rows for x in (r_["cats"].split("|") if r_["cats"] else []))
n_conf=int(C.confounded.sum())
print(f"\n=== 오염 {n_conf}/{len(C)} ({100*n_conf/len(C):.1f}%) · 범주 {dict(catc)} ===",flush=True)
clean=set(C[C.confounded==0].k)
# ---------- (a) CAR 재추정 ----------
car=pd.read_csv(f"{OUT}/../pipe_wp13_2026-08-26/wp10b_car_vw.csv",dtype={"k":str})
fd=pd.read_csv(f"{BASE}/shared/outputs/pipe_wp13_2026-08-26/treatment_fdpp.csv",dtype={"k":str})
fd["k"]=fd["k"].str.replace(r'\D','',regex=True).str.zfill(10)
cm=car.merge(fd[["k","dom_purpose"]],on="k",how="left")
cm["surv"]=cm.dom_purpose.isin(["운영","채무상환"]); cm["grow"]=cm.dom_purpose.isin(["시설","타법인증권","영업양수"])
def carstat(df,lab):
    a=pd.to_numeric(df.car11,errors="coerce").dropna()
    t=float(a.mean()/(a.std(ddof=1)/np.sqrt(len(a))))
    s=pd.to_numeric(df[df.surv].car11,errors="coerce").dropna(); g=pd.to_numeric(df[df.grow].car11,errors="coerce").dropna()
    p=float(stats.ttest_ind(s,g,equal_var=False).pvalue) if len(s)>5 and len(g)>5 else None
    out=dict(n=len(a),mean=round(float(a.mean()),4),t=round(t,2),
             surv=dict(n=len(s),mean=round(float(s.mean()),4)),grow=dict(n=len(g),mean=round(float(g.mean()),4)),
             welch_p=round(p,4) if p else None)
    print(f"  {lab}: {out}",flush=True); return out
print("\n=== (a) CAR ===")
res_car=dict(all=carstat(cm,"전체"),clean=carstat(cm[cm.k.isin(clean)],"비오염만"))
json.dump(dict(confound=dict(n=len(C),confounded=n_conf,rate=round(n_conf/len(C),3),categories=dict(catc)),
               car=res_car),open(f"{OUT}/wp11o_confound.json","w"),ensure_ascii=False,indent=1)
open(f"{OUT}/wp11o.done","w").write("done")
print("\n=== WP11o 1차(공시조회+CAR) 완료 ===")
