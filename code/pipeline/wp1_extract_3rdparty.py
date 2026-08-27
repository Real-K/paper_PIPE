# -*- coding: utf-8 -*-
"""P-016 WP1 — 전체표본 제3자배정 공시 전수 추출 + 딜-공시 특정률 게이트(≥80%).
처치정의: 상장 PIPE 최초딜 ↔ 제3자배정 유상증자/CB 공시(rcept_no=이벤트일).
키 5개 로테이션, 미출력. 읽기전용(원자료 무수정), 산출 → shared/outputs/pipe_wp1_2026-08-22/.
"""
import os,json,time,urllib.request,urllib.parse,warnings,itertools; warnings.filterwarnings("ignore")
import xml.etree.ElementTree as ET
import pandas as pd,numpy as np
BASE=os.environ.get("P016_BASE", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))   # 원 경로는 제거했다 — 실행 시 P016_BASE 로 지정하거나 기본값 사용
OUT=f"{BASE}/shared/outputs/pipe_wp1_2026-08-22"
keys=[l.split("=",1)[1].strip() for l in open(os.path.expanduser("~/.claude/.env"))
      if l.startswith("DART_API_KEY") and "=" in l and l.split("=",1)[1].strip()]
assert len(keys)>=1, "DART 키 없음"
print(f"DART 키 {len(keys)}개 로테이션(미출력)",flush=True)
kc=itertools.cycle(keys)
def dget(ep,p):
    p=dict(p); p["crtfc_key"]=next(kc)
    for _ in range(3):
        try: return json.load(urllib.request.urlopen(f"https://opendart.fss.or.kr/api/{ep}?"+urllib.parse.urlencode(p),timeout=25))
        except Exception: time.sleep(0.5)
    return {"status":"ERR"}
# corp_code 매핑: ticker + eng name
root=ET.parse(f"{BASE}/shared/data/external/dart_auditcover/CORPCODE.xml").getroot()
tk2cc={}; eng2cc={}
import re
def norm(s): return re.sub(r'[^a-z0-9]','',str(s).lower())
for li in root.iter("list"):
    sc=(li.findtext("stock_code") or "").strip(); cc=(li.findtext("corp_code") or "").strip()
    en=norm(li.findtext("corp_eng_name") or "")
    if sc and cc: tk2cc[sc]=cc
    if en and cc: eng2cc.setdefault(en,[]).append(cc)
# PIPE∩Completed∩NPS 최초딜
nps=set(pd.read_parquet(f"{BASE}/shared/data/processed/nps_monthly_matched_v2.parquet",columns=["bn10"]).bn10.astype(str).unique())
a=pd.read_csv(f"{BASE}/shared/data/processed/pitchbook_all_status_v1.csv",dtype=str)
a=a[(a["Deal Type"].astype(str).str.contains("PIPE",na=False)) & (a["Deal Status"].astype(str).str.contains("Complet",case=False,na=False))].copy()
a["k"]=a.bn.astype(str).str.replace(r'\D','',regex=True).str.zfill(10); a=a[a.k.isin(nps)]
a["dd"]=pd.to_datetime(a["Deal Date"],errors="coerce"); a=a.dropna(subset=["dd"])
a["tk"]=a["Companies"].astype(str).str.extract(r'\((?:KRX|KOSDAQ|KOSPI|KONEX)[:\s]*([0-9]{6})\)')
a["eng"]=a["Companies"].astype(str).str.replace(r'\s*\(.*$','',regex=True).map(norm)
a["sz"]=pd.to_numeric(a["Deal Size"],errors="coerce")   # 백만 USD
first=a.sort_values("dd").groupby("k").first().reset_index()
def resolve_cc(r):
    if pd.notna(r.tk) and r.tk in tk2cc: return tk2cc[r.tk]
    c=eng2cc.get(r.eng)
    return c[0] if c and len(c)==1 else None
first["cc"]=first.apply(resolve_cc,axis=1)
firm=first.dropna(subset=["cc"])
print(f"PIPE∩Completed∩NPS 최초딜: {len(first)} · corp_code 확보 {len(firm)} ({len(firm)/len(first)*100:.0f}%)",flush=True)
def rn_dt(rn):
    try: return pd.to_datetime(str(rn)[:8],format="%Y%m%d")
    except: return pd.NaT
rows=[]
for i,r in enumerate(firm.itertuples(),1):
    cc=r.cc; bgn=(r.dd-pd.Timedelta(days=200)).strftime("%Y%m%d"); end=(r.dd+pd.Timedelta(days=60)).strftime("%Y%m%d")
    cands=[]  # 제3자배정 공시 후보
    for ep,amt_field in (("piicDecsn.json",None),("cvbdIsDecsn.json","bd_ist_tram"),
                         ("bdwtIsDecsn.json","bd_ist_tram"),("exbdIsDecsn.json","bd_ist_tram")):
        d=dget(ep,{"corp_code":cc,"bgn_de":bgn,"end_de":end})
        if d.get("status")=="000":
            for it in d.get("list",[]):
                blob=" ".join(str(v) for v in it.values())
                if "제3자배정" in blob:
                    dt=rn_dt(it.get("rcept_no"))
                    # 조달금액(원): 유상증자는 fdpp 합, CB류는 발행총액
                    amt=None
                    if ep=="piicDecsn.json":
                        s=0
                        for f in ("fdpp_fclt","fdpp_bsninh","fdpp_op","fdpp_dtrp","fdpp_ocsa","fdpp_etc"):
                            v=str(it.get(f,"")).replace(",","").strip()
                            if v not in("","-"):
                                try: s+=float(v)
                                except: pass
                        amt=s if s>0 else None
                    else:
                        v=str(it.get("bd_ist_tram","")).replace(",","").strip()
                        if v not in("","-"):
                            try: amt=float(v)
                            except: pass
                    cands.append({"rcept":it.get("rcept_no"),"dt":dt,"ep":ep.split("Decsn")[0],"amt_won":amt})
    # 특정: 후보 유일 or 조달금액 매칭(Deal Size*1190*1e6 ± 25%) or 딜일 최근접
    pb_won=(r.sz*1190*1e6) if pd.notna(r.sz) else None
    n=len(cands)
    spec=None; how=None
    if n==1: spec=cands[0]; how="unique"
    elif n>1:
        if pb_won:
            m=[c for c in cands if c["amt_won"] and abs(c["amt_won"]-pb_won)/pb_won<0.25]
            if len(m)==1: spec=m[0]; how="amount"
        if spec is None:
            g=[(abs((c["dt"]-r.dd).days),c) for c in cands if pd.notna(c["dt"])]
            if g: spec=min(g,key=lambda x:x[0])[1]; how="nearest"
    rows.append({"k":r.k,"cc":cc,"dd":str(r.dd.date()),"n_cands":n,
                 "specified":spec is not None,"how":how,
                 "event_rcept":spec["rcept"] if spec else None,
                 "event_dt":str(spec["dt"].date()) if spec and pd.notna(spec["dt"]) else None,
                 "ep":spec["ep"] if spec else None})
    if i%50==0:
        sr=np.mean([x["specified"] for x in rows]); print(f"  [{i}/{len(firm)}] 특정률 {sr*100:.0f}%",flush=True)
    time.sleep(0.15)
R=pd.DataFrame(rows); R.to_csv(f"{OUT}/wp1_treatment_events.csv",index=False,encoding="utf-8-sig")
R["strict"]=R.specified & R.how.isin(["unique","amount"])
res=dict(n_firstdeals=int(len(first)),n_corpcode=int(len(firm)),
         n_strict=int(R["strict"].sum()),
         spec_rate_strict_of_corpcode=float(R["strict"].mean()),
         spec_rate_strict_of_all=float(R["strict"].sum()/len(first)),
         n_specified=int(R.specified.sum()),
         spec_rate_of_corpcode=float(R.specified.mean()),
         spec_rate_of_all=float(R.specified.sum()/len(first)),
         has_3rd=int((R.n_cands>=1).sum()),
         how=R[R.specified].how.value_counts().to_dict(),
         med_cands=float(R.n_cands.median()),
         gate_80_strict_corpcode=bool(R["strict"].mean()>=0.80),
         gate_80_lenient_corpcode=bool(R.specified.mean()>=0.80),
         gate_80_strict_all=bool(R["strict"].sum()/len(first)>=0.80))
json.dump(res,open(f"{OUT}/wp1_summary.json","w"),ensure_ascii=False,indent=1)
print(f"\n=== WP1 게이트 ===")
print(f"최초딜 {res['n_firstdeals']} · corp_code {res['n_corpcode']} · 제3자배정 보유 {res['has_3rd']}")
print(f"특정 {res['n_specified']} · 특정률(corp_code분모) {res['spec_rate_of_corpcode']*100:.1f}% · (전체분모) {res['spec_rate_of_all']*100:.1f}%")
print(f"특정방법: {res['how']}")
print(f"엄격특정(유일+금액) {res['n_strict']} · 엄격특정률(corp_code) {res['spec_rate_strict_of_corpcode']*100:.1f}%")
print(f"게이트 ≥80% 엄격(corp_code): {'PASS' if res['gate_80_strict_corpcode'] else 'FAIL'} · 관대: {'PASS' if res['gate_80_lenient_corpcode'] else 'FAIL'} · 엄격(전체분모): {'PASS' if res['gate_80_strict_all'] else 'FAIL'}")
