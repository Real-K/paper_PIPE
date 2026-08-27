# -*- coding: utf-8 -*-
"""WP11a — G1 기반 재구축.
(1) 상장 대조 후보의 과거 제3자배정 발행이력 purge (DART piicDecsn 전수: ic_mthn 제3자 이력 → 오염 제거)
(2) distress 공변량 패널 (재무통합 CSV: leverage·ROA·cash·자본잠식(equity<0)) — bn×연도
산출: shared/outputs/pipe_wp11_2026-08-23/{controls_clean.csv, fin_distress_panel.csv, wp11a.json}
"""
import os,json,csv,re,time,urllib.request,urllib.parse,itertools,warnings; warnings.filterwarnings("ignore")
import numpy as np,pandas as pd
import xml.etree.ElementTree as ET
BASE=os.environ.get("P016_BASE", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))   # 원 경로는 제거했다 — 실행 시 P016_BASE 로 지정하거나 기본값 사용
RE=f"{BASE}/shared/outputs/pipe_r1_reextract_2026-08-22"
OUT=f"{BASE}/shared/outputs/pipe_wp11_2026-08-23"; os.makedirs(OUT,exist_ok=True)
keys=[l.split("=",1)[1].strip() for l in open(os.path.expanduser("~/.claude/.env")) if l.startswith("DART_API_KEY") and l.split("=",1)[1].strip()]
kc=itertools.cycle(keys); print(f"키 {len(keys)} (미출력)",flush=True)
def dget(ep,p):
    p=dict(p); p["crtfc_key"]=next(kc)
    for _ in range(3):
        try: return json.load(urllib.request.urlopen(f"https://opendart.fss.or.kr/api/{ep}?"+urllib.parse.urlencode(p),timeout=25))
        except: time.sleep(0.4)
    return {"status":"ERR"}
# bn→ticker (재무CSV) → corp_code (CORPCODE)
bn2tk={}
with open(f"{BASE}/PI/drops/재무데이터_2009_2025_통합.csv",encoding='utf-8') as f:
    rd=csv.reader(f); next(rd)
    for row in rd:
        if len(row)<6: continue
        code=row[0].lstrip('﻿')
        if re.match(r'^A\d{6}$',code):
            bn=re.sub(r'\D','',row[5]).zfill(10)
            if len(bn)==10 and bn!="0000000000": bn2tk.setdefault(bn,set()).add(code[1:])
root=ET.parse(f"{BASE}/shared/data/external/dart_auditcover/CORPCODE.xml").getroot()
tk2cc={}
for li in root.iter("list"):
    sc=(li.findtext("stock_code") or "").strip(); c=(li.findtext("corp_code") or "").strip()
    if sc and c and len(sc)==6: tk2cc[sc]=c
nps_bn=set(pd.read_parquet(f"{BASE}/shared/data/processed/nps_monthly_matched_v2.parquet",columns=["bn10"]).bn10.unique())
pb=pd.read_csv(f"{BASE}/shared/data/processed/pitchbook_all_status_v1.csv",dtype=str)
pbbn=set(pb["bn"].astype(str).str.replace(r'\D','',regex=True).str.zfill(10).dropna())
T=pd.read_csv(f"{RE}/treatment_master_v2.csv",dtype=str); tb=set(T["k"].str.replace(r'\D','',regex=True).str.zfill(10))
cand=[b for b in bn2tk if (b in nps_bn) and (b not in pbbn) and (b not in tb)]
print(f"상장 대조 후보 {len(cand)}",flush=True)
rows=[]
for i,b in enumerate(cand,1):
    cc=None
    for tk in bn2tk[b]:
        if tk in tk2cc: cc=tk2cc[tk]; break
    if cc is None:
        rows.append(dict(bn=b,cc="",third_hist=None)); continue
    R=dget("piicDecsn.json",{"corp_code":cc,"bgn_de":"20100101","end_de":"20261231"})
    th=False
    if R.get("status")=="000":
        th=any("제3자" in str(it.get("ic_mthn","")) for it in R.get("list",[]))
    elif R.get("status") not in ("013",):
        th=None  # 판정불가
    rows.append(dict(bn=b,cc=cc,third_hist=th))
    if i%200==0:
        n3=sum(1 for x in rows if x["third_hist"] is True)
        print(f"  [{i}/{len(cand)}] 제3자이력 {n3}",flush=True)
    time.sleep(0.02)
C=pd.DataFrame(rows); C.to_csv(f"{OUT}/controls_clean.csv",index=False,encoding="utf-8-sig")
n3=int((C.third_hist==True).sum()); nun=int(C.third_hist.isna().sum())
clean=C[(C.third_hist==False)]
print(f"purge: 제3자이력 {n3} 제거 · 판정불가 {nun}(보수적 제거) · 청정 대조 {len(clean)}",flush=True)
# distress 패널 (청정대조+처치)
want=set(clean.bn)|tb
def num(x):
    try: return float(x)
    except: return np.nan
frows=[]
with open(f"{BASE}/PI/drops/재무데이터_2009_2025_통합.csv",encoding='utf-8') as f:
    rd=csv.reader(f); next(rd)
    for row in rd:
        if len(row)<109 or row[4].strip()!="결산": continue
        bn=re.sub(r'\D','',row[5]).zfill(10)
        if bn not in want: continue
        try: yr=int(row[3])
        except: continue
        ta=num(row[8]); tl=num(row[47]); te=num(row[82]); ni=num(row[108]); ch=num(row[12])
        frows.append(dict(bn=bn,year=yr,lev=(tl/te if te and te>0 else np.nan),roa=(ni/ta if ta and ta>0 else np.nan),
                          cash=(ch/ta if ta and ta>0 else np.nan),impaired=1 if (te is not np.nan and te is not None and te<0) else 0,
                          loss=1 if (ni==ni and ni<0) else 0))
F=pd.DataFrame(frows).drop_duplicates(["bn","year"],keep="first")
F.to_csv(f"{OUT}/fin_distress_panel.csv",index=False,encoding="utf-8-sig")
json.dump(dict(candidates=len(cand),third_hist_purged=n3,unresolved_purged=nun,clean_controls=int(len(clean)),
               fin_rows=int(len(F)),fin_firms=int(F.bn.nunique())),open(f"{OUT}/wp11a.json","w"),ensure_ascii=False,indent=1)
open(f"{OUT}/wp11a.done","w").write("done")
print(f"\n=== WP11a 완료 === 청정대조 {len(clean)} · 재무 {F.bn.nunique()}사 {len(F)}행")
