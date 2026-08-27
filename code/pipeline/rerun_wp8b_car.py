# WP13 재실행 사본 (2026-08-26): 정규화 마스터(382 dated)로 동일 코드 재실행. 원본 wp8b_car.py · 출력 폴더만 pipe_wp13_2026-08-26 으로 치환.
# -*- coding: utf-8 -*-
"""P-016-A (트랙③) — 제3자배정 PIPE 공시 주가 CAR event-study. 시장모형 초과수익.
처치: treatment_master_v2 (cc→CORPCODE stock_code→티커). 이벤트일=event_dt(공시). 로컬 수정주가(kospi/kosdaq).
시장모형 α,β 추정창 [-120,-21] → AR=r-(α+βr_m). CAR 윈도 [-1,1],[0,1],[0,5],[0,20]. 시장프록시=시장별 등가중 평균수익.
산출: shared/outputs/pipe_wp13_2026-08-26/wp8b_car.json
"""
import os,json,warnings,re; warnings.filterwarnings("ignore")
import numpy as np,pandas as pd
import xml.etree.ElementTree as ET
BASE=os.environ.get("P016_BASE", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))   # 원 경로는 제거했다 — 실행 시 P016_BASE 로 지정하거나 기본값 사용
RE=f"{BASE}/shared/outputs/pipe_r1_reextract_2026-08-22"
OUT=f"{BASE}/shared/outputs/pipe_wp13_2026-08-26"; os.makedirs(OUT,exist_ok=True)
RNG=np.random.default_rng(20260823)
# cc → stock_code
root=ET.parse(f"{BASE}/shared/data/external/dart_auditcover/CORPCODE.xml").getroot()
cc2sc={}
for li in root.iter("list"):
    c=(li.findtext("corp_code") or "").strip(); sc=(li.findtext("stock_code") or "").strip()
    if c and sc and sc!=" " and len(sc)==6: cc2sc[c]=sc
T=pd.read_csv(f"{RE}/treatment_master_v2.csv",dtype=str); T["k"]=T["k"].str.replace(r'\D','',regex=True).str.zfill(10)
T=T[pd.to_numeric(T.event_dt.astype(str).str[:4],errors="coerce").between(2015,2025)]   # 표본기간 2015–2025(원고 명시). 날짜 정규화로 유입된 2010–2014·2026 이벤트 제외 — WP13, 2026-08-27
T["ev"]=pd.to_datetime(T["event_dt"],errors="coerce"); T=T.dropna(subset=["ev"]).drop_duplicates("k")
T["sc"]=T.cc.map(cc2sc); T=T.dropna(subset=["sc"])
print(f"처치 티커확보 {len(T)}",flush=True)
# 주가 로드 (wide: 행=날짜, 열=A+티커)
def load_sheet(sh):
    d=pd.read_excel(f"{BASE}/PI/drops/kospi, kosdaq 종목 수정주가.xlsx",sheet_name=sh)
    d=d.rename(columns={d.columns[0]:"date"}); d["date"]=pd.to_datetime(d["date"],errors="coerce"); d=d.dropna(subset=["date"]).set_index("date").sort_index()
    d.columns=[str(c).replace("A","",1) if str(c).startswith("A") else str(c) for c in d.columns]
    return d.apply(pd.to_numeric,errors="coerce")
px=pd.concat([load_sheet("kospi"),load_sheet("kosdaq")],axis=1)
px=px.loc[:,~px.columns.duplicated()]
ret=np.log(px/px.shift(1))
mkt=ret.mean(axis=1)   # 등가중 시장 프록시
dates=ret.index
print(f"주가 {px.shape} · 거래일 {len(dates)}",flush=True)
def nearest_di(ev):
    pos=dates.searchsorted(ev)
    return min(pos,len(dates)-1)
WIN={"m1_p1":(-1,1),"e0_p1":(0,1),"e0_p5":(0,5),"e0_p20":(0,20)}
res_rows=[]
for r in T.itertuples():
    sc=r.sc
    if sc not in ret.columns: continue
    ri=ret[sc]; e=nearest_di(r.ev)
    est=range(e-120,e-20)
    if e-120<0 or e+20>=len(dates): continue
    ry=ri.iloc[list(est)].values; rm=mkt.iloc[list(est)].values
    ok=np.isfinite(ry)&np.isfinite(rm)
    if ok.sum()<60: continue
    b=np.polyfit(rm[ok],ry[ok],1); beta,alpha=b[0],b[1]
    row={"k":r.k,"sc":sc}
    for nm,(a,z) in WIN.items():
        idx=range(e+a,e+z+1); ar=[]
        for j in idx:
            if 0<=j<len(dates) and np.isfinite(ri.iloc[j]) and np.isfinite(mkt.iloc[j]):
                ar.append(ri.iloc[j]-(alpha+beta*mkt.iloc[j]))
        row[nm]=float(np.sum(ar)) if ar else np.nan
    res_rows.append(row)
C=pd.DataFrame(res_rows); C.to_csv(f"{OUT}/wp8b_car_firm.csv",index=False,encoding="utf-8-sig")
print(f"CAR 산출 {len(C)}",flush=True)
def agg(col):
    a=C[col].dropna().values; n=len(a)
    if n<10: return dict(n=n,note="n<10")
    m=float(np.mean(a)); se=float(np.std(a,ddof=1)/np.sqrt(n)); t=m/se if se>0 else None
    bs=np.array([np.mean(a[RNG.integers(0,n,n)]) for _ in range(2000)])
    return dict(n=n,mean_CAR=round(m,4),t=round(t,2) if t else None,ci95=[round(float(np.percentile(bs,2.5)),4),round(float(np.percentile(bs,97.5)),4)],
                median=round(float(np.median(a)),4),pct_pos=round(float(np.mean(a>0)),3))
out={nm:agg(nm) for nm in WIN}
json.dump(dict(id="P016-A-CAR",n_treated_ticker=int(len(T)),n_car=int(len(C)),windows=out,
               market_proxy="equal-weighted cross-sectional mean (kospi+kosdaq)"),
          open(f"{OUT}/wp8b_car.json","w"),ensure_ascii=False,indent=1)
open(f"{OUT}/car.done","w").write("done")
print("=== CAR 완료 ===")
for nm,v in out.items(): print(f"  {nm}: {v}")
