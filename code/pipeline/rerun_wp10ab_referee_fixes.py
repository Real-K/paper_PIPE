# WP13 재실행 사본 — 출력 폴더 치환
# -*- coding: utf-8 -*-
"""P-016 WP10ab — 도메인 referee fixes 1·2.
Fix1(A): 배정대상자 사후지분율 = nstk/(nstk+bfic) 분포(357 유상증자) + ssl_at 전매제한 비중 + ≥30%/≥50% 비율(지배권 이전 프록시).
Fix2(B): 목적-CAR을 전체 분류표본(CAR∩fdpp)으로 재실행 + 거래소지수(네이버 KOSPI/KOSDAQ, 가치가중) 프록시 + BMP 표준화 검정.
산출: shared/outputs/pipe_wp13_2026-08-26/wp10ab.json
"""
import os,json,time,urllib.request,urllib.parse,warnings,itertools,re; warnings.filterwarnings("ignore")
import numpy as np,pandas as pd
from scipy import stats
BASE=os.environ.get("P016_BASE", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))   # 원 경로는 제거했다 — 실행 시 P016_BASE 로 지정하거나 기본값 사용
RE=f"{BASE}/shared/outputs/pipe_r1_reextract_2026-08-22"
OUT=f"{BASE}/shared/outputs/pipe_wp13_2026-08-26"; os.makedirs(OUT,exist_ok=True)
keys=[l.split("=",1)[1].strip() for l in open(os.path.expanduser("~/.claude/.env")) if l.startswith("DART_API_KEY") and l.split("=",1)[1].strip()]
kc=itertools.cycle(keys); print(f"DART 키 {len(keys)} (미출력)",flush=True)
def dget(ep,p):
    p=dict(p); p["crtfc_key"]=next(kc)
    for _ in range(3):
        try: return json.load(urllib.request.urlopen(f"https://opendart.fss.or.kr/api/{ep}?"+urllib.parse.urlencode(p),timeout=25))
        except: time.sleep(0.4)
    return {"status":"ERR"}
def num(x):
    try: return float(re.sub(r'[^\d.]','',str(x))) if str(x).strip() not in ('','-') else np.nan
    except: return np.nan
T=pd.read_csv(f"{RE}/treatment_master_v2.csv",dtype=str); T["k"]=T["k"].str.replace(r'\D','',regex=True).str.zfill(10)
T["evd"]=pd.to_datetime(T["event_dt"],errors="coerce"); T=T.dropna(subset=["evd"]).drop_duplicates("k")
T=T[pd.to_numeric(T.event_dt.astype(str).str[:4],errors="coerce").between(2015,2025)]  # WP13: 표본기간 2015–2025 (피어 합의, wp8b 317 우주 정합)
# ===== A. 지분율 =====
rows=[]
for i,r in enumerate(T.itertuples(),1):
    bgn=(r.evd-pd.Timedelta(days=30)).strftime("%Y%m%d"); end=(r.evd+pd.Timedelta(days=30)).strftime("%Y%m%d")
    R=dget("piicDecsn.json",{"corp_code":r.cc,"bgn_de":bgn,"end_de":end})
    st=np.nan; ssl=""; found=False
    for it in R.get("list",[]):
        if "제3자" not in str(it.get("ic_mthn","")): continue
        n_=num(it.get("nstk_ostk_cnt")); b_=num(it.get("bfic_tisstk_ostk"))
        if np.isfinite(n_) and np.isfinite(b_) and (n_+b_)>0:
            st=n_/(n_+b_); ssl=str(it.get("ssl_at","")); found=True; break
    rows.append(dict(k=r.k,cc=r.cc,stake=st,ssl_at=ssl,found=found))
    if i%60==0: print(f"  [A {i}/{len(T)}] stake 확보 {sum(1 for x in rows if np.isfinite(x['stake']))}",flush=True)
    time.sleep(0.03)
A=pd.DataFrame(rows); A.to_csv(f"{OUT}/wp10a_stake.csv",index=False,encoding="utf-8-sig")
sv=A.stake.dropna()
resA=dict(n_stake=int(len(sv)),median=round(float(sv.median()),4),p25=round(float(sv.quantile(.25)),4),p75=round(float(sv.quantile(.75)),4),
          p90=round(float(sv.quantile(.9)),4),ge30=round(float((sv>=.30).mean()),3),ge50=round(float((sv>=.50).mean()),3),
          lockup_Y=round(float((A[A.found].ssl_at=="Y").mean()),3))
print("A 지분율:",resA,flush=True)
# ===== B. 지수 프록시 CAR + 목적 full-sample + BMP =====
def naver_index(sym):
    url=f"https://api.finance.naver.com/siseJson.naver?symbol={sym}&requestType=1&startTime=20140101&endTime=20261231&timeframe=day"
    req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0"})
    txt=urllib.request.urlopen(req,timeout=30).read().decode("utf-8","ignore")
    rows=re.findall(r'\["(\d{8})",\s*([\d.]+)',txt)
    s=pd.Series({pd.to_datetime(d):float(v) for d,v in rows}).sort_index()
    return s
try:
    kospi=naver_index("KOSPI"); kosdaq=naver_index("KOSDAQ")
    idx_ok=len(kospi)>1000 and len(kosdaq)>1000
except Exception as ex:
    idx_ok=False; print("지수 fetch 실패:",ex,flush=True)
print(f"지수: KOSPI {len(kospi) if idx_ok else 0} KOSDAQ {len(kosdaq) if idx_ok else 0}",flush=True)
import xml.etree.ElementTree as ET
root=ET.parse(f"{BASE}/shared/data/external/dart_auditcover/CORPCODE.xml").getroot()
cc2sc={(li.findtext("corp_code") or "").strip():(li.findtext("stock_code") or "").strip() for li in root.iter("list")}
def load_sheet(sh):
    d=pd.read_excel(f"{BASE}/PI/drops/kospi, kosdaq 종목 수정주가.xlsx",sheet_name=sh)
    d=d.rename(columns={d.columns[0]:"date"}); d["date"]=pd.to_datetime(d["date"],errors="coerce"); d=d.dropna(subset=["date"]).set_index("date").sort_index()
    d.columns=[str(c).replace("A","",1) if str(c).startswith("A") else str(c) for c in d.columns]
    return d.apply(pd.to_numeric,errors="coerce")
pk=load_sheet("kospi"); pq=load_sheet("kosdaq")
exch={c:"KOSPI" for c in pk.columns}; exch.update({c:"KOSDAQ" for c in pq.columns if c not in exch})
px=pd.concat([pk,pq],axis=1); px=px.loc[:,~px.columns.duplicated()]
ret=np.log(px/px.shift(1)); dates=ret.index
if idx_ok:
    ik=np.log(kospi/kospi.shift(1)).reindex(dates); iq=np.log(kosdaq/kosdaq.shift(1)).reindex(dates)
T["sc"]=T.cc.map(cc2sc)
fd=pd.read_csv(f"{BASE}/shared/outputs/pipe_wp13_2026-08-26/treatment_fdpp.csv",dtype={"k":str})
fd["k"]=fd["k"].str.replace(r'\D','',regex=True).str.zfill(10)
TT=T.merge(fd[["k","fdpp_found","dom_purpose"]],on="k",how="left")
TT["survival"]=TT.dom_purpose.isin(["운영","채무상환"]); TT["growth_p"]=TT.dom_purpose.isin(["시설","타법인증권","영업양수"])
carr=[]
for r in TT.itertuples():
    sc=r.sc
    if not isinstance(sc,str) or sc not in ret.columns: continue
    e=dates.searchsorted(r.evd)
    if e-120<0 or e+20>=len(dates): continue
    mkt=(ik if exch.get(sc)=="KOSPI" else iq) if idx_ok else ret.mean(axis=1)
    est=slice(e-120,e-20)
    ry=ret[sc].iloc[est].values; rm=mkt.iloc[est].values
    okm=np.isfinite(ry)&np.isfinite(rm)
    if okm.sum()<60: continue
    b=np.polyfit(rm[okm],ry[okm],1); beta,alpha=b[0],b[1]
    resid=ry[okm]-(alpha+beta*rm[okm]); s2=np.var(resid,ddof=2)
    def car(a,z):
        ar=[]
        for j in range(e+a,e+z+1):
            if 0<=j<len(dates) and np.isfinite(ret[sc].iloc[j]) and np.isfinite(mkt.iloc[j]): ar.append(ret[sc].iloc[j]-(alpha+beta*mkt.iloc[j]))
        return (float(np.sum(ar)),len(ar)) if ar else (np.nan,0)
    c11,n11=car(-1,1); c05,n05=car(0,5)
    carr.append(dict(k=r.k,car11=c11,scar11=c11/np.sqrt(n11*s2) if n11>0 and s2>0 else np.nan,
                     car05=c05,scar05=c05/np.sqrt(n05*s2) if n05>0 and s2>0 else np.nan,
                     survival=bool(r.survival),growth=bool(r.growth_p),classified=bool(r.survival or r.growth_p)))
C=pd.DataFrame(carr); C.to_csv(f"{OUT}/wp10b_car_vw.csv",index=False,encoding="utf-8-sig")
def bmp(scars):
    s=np.asarray(scars,float); s=s[np.isfinite(s)]; n=len(s)
    return round(float(s.mean()/(s.std(ddof=1)/np.sqrt(n))),2),n
resB=dict(proxy="exchange index (Naver, value-weighted)" if idx_ok else "EW fallback",n_car=int(len(C)))
resB["all_car11_mean"]=round(float(C.car11.mean()),4); resB["all_bmp_t11"],_=bmp(C.scar11)
cs=C[C.survival]; cg=C[C.growth]
tt11=stats.ttest_ind(cs.car11.dropna(),cg.car11.dropna(),equal_var=False)
resB["purpose_full"]=dict(n_surv=int(len(cs)),n_grow=int(len(cg)),
    surv_car11=round(float(cs.car11.mean()),4),grow_car11=round(float(cg.car11.mean()),4),
    diff=round(float(cs.car11.mean()-cg.car11.mean()),4),welch_p=round(float(tt11.pvalue),4),
    surv_bmp_t=bmp(cs.scar11)[0],grow_bmp_t=bmp(cg.scar11)[0])
tt05=stats.ttest_ind(cs.car05.dropna(),cg.car05.dropna(),equal_var=False)
resB["purpose_full_05"]=dict(surv=round(float(cs.car05.mean()),4),grow=round(float(cg.car05.mean()),4),welch_p=round(float(tt05.pvalue),4))
print("B 목적-CAR(full, 지수프록시):",resB["purpose_full"],flush=True)
json.dump(dict(A_stake=resA,B_car=resB),open(f"{OUT}/wp10ab.json","w"),ensure_ascii=False,indent=1)
open(f"{OUT}/wp10ab.done","w").write("done")
print("\n=== WP10ab 완료 ===")
