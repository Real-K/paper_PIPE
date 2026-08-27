# WP13 재실행 사본 (2026-08-27): 정규화 마스터(382 dated)로 재실행. 원본 wp11b_dualclock.py · 출력 폴더만 pipe_wp13_2026-08-26 으로 치환.
# -*- coding: utf-8 -*-
"""WP11b — G3 dual clock. 납입일(문서 파싱) 추출 → 공시-납입 lag → 꼬리 붕괴 onset의 순서 판정
(악화→공시→납입 = selection/distress vs 공시→납입→붕괴 = post-funding adjustment).
산출: shared/outputs/pipe_wp13_2026-08-26/{funding_dates.csv, wp11b.json}
"""
import os,json,re,time,io,zipfile,urllib.request,urllib.parse,itertools,warnings; warnings.filterwarnings("ignore")
import numpy as np,pandas as pd
BASE=os.environ.get("P016_BASE", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))   # 원 경로는 제거했다 — 실행 시 P016_BASE 로 지정하거나 기본값 사용
RE=f"{BASE}/shared/outputs/pipe_r1_reextract_2026-08-22"
OUT=f"{BASE}/shared/outputs/pipe_wp13_2026-08-26"; os.makedirs(OUT,exist_ok=True)
keys=[l.split("=",1)[1].strip() for l in open(os.path.expanduser("~/.claude/.env")) if l.startswith("DART_API_KEY") and l.split("=",1)[1].strip()]
kc=itertools.cycle(keys); print(f"키 {len(keys)} (미출력)",flush=True)
def dget(ep,p):
    p=dict(p); p["crtfc_key"]=next(kc)
    for _ in range(3):
        try: return json.load(urllib.request.urlopen(f"https://opendart.fss.or.kr/api/{ep}?"+urllib.parse.urlencode(p),timeout=25))
        except: time.sleep(0.4)
    return {"status":"ERR"}
def ddoc(rcept):
    for _ in range(3):
        try:
            raw=urllib.request.urlopen("https://opendart.fss.or.kr/api/document.xml?"+urllib.parse.urlencode({"crtfc_key":next(kc),"rcept_no":rcept}),timeout=40).read()
            try:
                z=zipfile.ZipFile(io.BytesIO(raw)); t=""
                for n in z.namelist():
                    b=z.read(n)
                    for enc in ("utf-8","cp949","euc-kr"):
                        try: t+=b.decode(enc); break
                        except: pass
                return t
            except zipfile.BadZipFile: return raw.decode("utf-8","ignore")
        except: time.sleep(0.5)
    return ""
DATE=re.compile(r'(20\d{2})\s*[년.\-/]\s*(\d{1,2})\s*[월.\-/]\s*(\d{1,2})')
def find_pay(txt,ev):
    # '납입일'/'납입기일' 주변 400자에서 이벤트일 이후 최근접 날짜
    best=None
    for m in re.finditer(r'납\s*입\s*(?:기\s*)?일',txt):
        seg=txt[m.end():m.end()+400]
        for dm in DATE.finditer(seg):
            try: d=pd.Timestamp(int(dm.group(1)),int(dm.group(2)),int(dm.group(3)))
            except: continue
            if ev<=d<=ev+pd.Timedelta(days=270):
                if best is None or d<best: best=d
                break
    return best
T=pd.read_csv(f"{RE}/treatment_master_v2.csv",dtype=str); T["k"]=T["k"].str.replace(r'\D','',regex=True).str.zfill(10)
T=T[pd.to_numeric(T.event_dt.astype(str).str[:4],errors="coerce").between(2015,2025)]   # 표본기간 2015–2025(원고 명시). 날짜 정규화로 유입된 2010–2014·2026 이벤트 제외 — WP13, 2026-08-27
T["ev"]=pd.to_datetime(T["event_dt"],errors="coerce"); T=T.dropna(subset=["ev"]).drop_duplicates("k")
rows=[]
for i,r in enumerate(T.itertuples(),1):
    bgn=(r.ev-pd.Timedelta(days=10)).strftime("%Y%m%d"); end=(r.ev+pd.Timedelta(days=10)).strftime("%Y%m%d")
    rc=None
    for ep in ("piicDecsn.json","cvbdIsDecsn.json","bdwtIsDecsn.json"):
        R=dget(ep,{"corp_code":r.cc,"bgn_de":bgn,"end_de":end})
        for it in R.get("list",[]):
            rc=it.get("rcept_no"); break
        if rc: break
    fund=None
    if rc:
        txt=ddoc(rc)
        if txt: fund=find_pay(txt,r.ev)
    rows.append(dict(k=r.k,cc=r.cc,ev=str(r.ev.date()),rcept=rc or "",funding=str(fund.date()) if fund is not None else "",
                     lag_days=(fund-r.ev).days if fund is not None else np.nan))
    if i%50==0:
        nf=sum(1 for x in rows if x["funding"]); print(f"  [{i}/{len(T)}] 납입일 확보 {nf}",flush=True)
    time.sleep(0.03)
F=pd.DataFrame(rows); F.to_csv(f"{OUT}/funding_dates.csv",index=False,encoding="utf-8-sig")
lag=F.lag_days.dropna()
# 꼬리 firm의 순서 판정: 고용 onset(첫 월 le-base ≤ −0.25) vs 납입월
d2=pd.read_csv(f"{BASE}/shared/outputs/pipe_wp13_2026-08-26/wp9e_firm_d_v2.csv",dtype={"k":str})
q25=d2.d2.quantile(.25); tailk=set(d2[d2.d2<=q25].k)
nps=pd.read_parquet(f"{BASE}/shared/data/processed/nps_monthly_matched_v2.parquet",columns=["bn10","data_ym","가입자수"])
nps["ym"]=pd.PeriodIndex(nps["data_ym"],freq="M"); nps["le"]=np.log1p(nps["가입자수"].astype(float))
months=pd.period_range(nps.ym.min(),nps.ym.max(),freq="M"); mi={m:j for j,m in enumerate(months)}
W=nps.pivot_table(index="bn10",columns="ym",values="le",aggfunc="mean").reindex(columns=months)
fx={b:i for i,b in enumerate(W.index)}; LEm=W.to_numpy(float)
order={"deterioration_before_funding":0,"collapse_after_funding":0,"no_onset_or_no_funding":0}
for r in F.itertuples():
    if r.k not in tailk or not r.funding or r.k not in fx: order["no_onset_or_no_funding"]+=1; continue
    e=mi.get(pd.Period(r.ev[:7],'M')); fm=mi.get(pd.Period(r.funding[:7],'M'))
    if e is None or fm is None: order["no_onset_or_no_funding"]+=1; continue
    row=LEm[fx[r.k]]; base=np.nanmean([row[e-j] for j in range(1,13) if e-j>=0])
    onset=None
    for m in range(0,13):
        if e+m<len(months) and np.isfinite(row[e+m]) and (row[e+m]-base)<=-0.25: onset=e+m; break
    if onset is None: order["no_onset_or_no_funding"]+=1
    elif onset<fm: order["deterioration_before_funding"]+=1
    else: order["collapse_after_funding"]+=1
res=dict(n=len(F),funding_found=int((F.funding!="").sum()),
         lag_median=float(lag.median()) if len(lag) else None,lag_p25=float(lag.quantile(.25)) if len(lag) else None,
         lag_p75=float(lag.quantile(.75)) if len(lag) else None,tail_order=order)
json.dump(res,open(f"{OUT}/wp11b.json","w"),ensure_ascii=False,indent=1)
open(f"{OUT}/wp11b.done","w").write("done")
print(f"\n=== WP11b 완료 === 납입일 {res['funding_found']}/{len(F)} · lag median {res['lag_median']}d · 꼬리순서 {order}")
