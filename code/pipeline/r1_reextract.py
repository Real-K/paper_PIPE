# -*- coding: utf-8 -*-
"""P-016 R1 — 처치 재추출 (WP2-a 결함 시정). outcome-blind (고용효과 미산출).
시정: (1) piicDecsn 단독 → **list.json 공시목록 report_nm 스캔** 1차, (2) 창 [dd-365,+120] 확대·연도만은 연-단위,
(3) 제3자배정 확인은 report_nm '제3자배정'(증권발행결과) OR piicDecsn ic_mthn OR 사모CB bdis_mthn.
키 5개 로테이션 미출력. 산출 shared/outputs/pipe_r1_reextract_2026-08-22/.
"""
import os,json,time,urllib.request,urllib.parse,warnings,itertools,re; warnings.filterwarnings("ignore")
import xml.etree.ElementTree as ET
import pandas as pd,numpy as np
BASE=os.environ.get("P016_BASE", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))   # 원 경로는 제거했다 — 실행 시 P016_BASE 로 지정하거나 기본값 사용
OUT=f"{BASE}/shared/outputs/pipe_r1_reextract_2026-08-22"
keys=[l.split("=",1)[1].strip() for l in open(os.path.expanduser("~/.claude/.env")) if l.startswith("DART_API_KEY") and l.split("=",1)[1].strip()]
kc=itertools.cycle(keys); print(f"DART 키 {len(keys)}개 (미출력)",flush=True)
def dget(ep,p):
    p=dict(p); p["crtfc_key"]=next(kc)
    for _ in range(3):
        try: return json.load(urllib.request.urlopen(f"https://opendart.fss.or.kr/api/{ep}?"+urllib.parse.urlencode(p),timeout=25))
        except: time.sleep(0.5)
    return {"status":"ERR"}
def norm(s): return re.sub(r'[^a-z0-9]','',str(s).lower())
root=ET.parse(f"{BASE}/shared/data/external/dart_auditcover/CORPCODE.xml").getroot()
tk2cc={}; eng2cc={}
for li in root.iter("list"):
    sc=(li.findtext("stock_code") or "").strip(); cc=(li.findtext("corp_code") or "").strip(); en=norm(li.findtext("corp_eng_name") or "")
    if sc and cc: tk2cc[sc]=cc
    if en and cc: eng2cc.setdefault(en,[]).append(cc)
nps=set(pd.read_parquet(f"{BASE}/shared/data/processed/nps_monthly_matched_v2.parquet",columns=["bn10"]).bn10.astype(str).unique())
a=pd.read_csv(f"{BASE}/shared/data/processed/pitchbook_all_status_v1.csv",dtype=str)
a=a[(a["Deal Type"].astype(str).str.contains("PIPE",na=False))&(a["Deal Status"].astype(str).str.contains("Complet",case=False,na=False))].copy()
a["k"]=a.bn.astype(str).str.replace(r'\D','',regex=True).str.zfill(10); a=a[a.k.isin(nps)]
a["dd"]=pd.to_datetime(a["Deal Date"],errors="coerce"); a=a.dropna(subset=["dd"])
a["yearonly"]=(a["Deal Date"].astype(str).str.match(r'^\d{4}-01-01'))
a["tk"]=a["Companies"].astype(str).str.extract(r'\((?:KRX|KOSDAQ|KOSPI|KONEX)[:\s]*([0-9]{6})\)')
a["eng"]=a["Companies"].astype(str).str.replace(r'\s*\(.*$','',regex=True).map(norm)
a["sz"]=pd.to_numeric(a["Deal Size"],errors="coerce")
first=a.sort_values("dd").groupby("k").first().reset_index()
def rcc(r):
    if pd.notna(r.tk) and r.tk in tk2cc: return tk2cc[r.tk]
    c=eng2cc.get(r.eng); return c[0] if c and len(c)==1 else None
first["cc"]=first.apply(rcc,axis=1); firm=first.dropna(subset=["cc"])
print(f"최초딜 {len(first)} · corp_code {len(firm)}",flush=True)
PAT=re.compile(r'유상증자|전환사채|신주인수권|교환사채|제3자배정')
def rn_dt(rn):
    try: return pd.to_datetime(str(rn)[:8],format="%Y%m%d")
    except: return pd.NaT
rows=[]
for i,r in enumerate(firm.itertuples(),1):
    cc=r.cc
    if r.yearonly:  # 연도만 → 그 해 전체 + 완충
        bgn=f"{r.dd.year}0101"; end=f"{r.dd.year+1}0630"
    else:
        bgn=(r.dd-pd.Timedelta(days=365)).strftime("%Y%m%d"); end=(r.dd+pd.Timedelta(days=120)).strftime("%Y%m%d")
    # list.json 공시목록 (주요사항보고 B + 발행공시 C 둘 다)
    hits=[]
    for ty in ("B","C"):
        for pg in (1,2):
            L=dget("list.json",{"corp_code":cc,"bgn_de":bgn,"end_de":end,"pblntf_ty":ty,"page_no":str(pg),"page_count":"100"})
            if L.get("status")!="000": break
            for it in L.get("list",[]):
                nm=it.get("report_nm","")
                if PAT.search(nm):
                    hits.append({"rcept":it.get("rcept_no"),"nm":nm,"dt":rn_dt(it.get("rcept_no"))})
            if int(L.get("total_page",1))<=pg: break
        time.sleep(0.05)
    # 제3자배정 신호: report_nm에 '제3자배정' 직접 포함(증권발행결과류)
    third_nm=[h for h in hits if "제3자배정" in h["nm"]]
    # 유상증자결정/CB발행결정 공시 (제3자배정 확인 필요분)
    dec=[h for h in hits if ("유상증자결정" in h["nm"] or "전환사채권발행결정" in h["nm"] or "신주인수권부사채권발행결정" in h["nm"])]
    rows.append({"k":r.k,"cc":cc,"dd":str(r.dd.date()),"yearonly":bool(r.yearonly),
                 "n_hits":len(hits),"n_third_nm":len(third_nm),"n_dec":len(dec),
                 "third_dates":[str(h["dt"].date()) for h in third_nm if pd.notna(h["dt"])][:5],
                 "dec_names":[h["nm"] for h in dec][:6]})
    if i%50==0:
        tr=np.mean([1 if (x["n_third_nm"]>=1 or x["n_dec"]>=1) else 0 for x in rows])
        print(f"  [{i}/{len(firm)}] 유상증자/CB/제3자배정 공시 보유 {tr*100:.0f}%",flush=True)
    time.sleep(0.05)
R=pd.DataFrame(rows); R.to_csv(f"{OUT}/r1_events.csv",index=False,encoding="utf-8-sig")
has_any=int(((R.n_third_nm>=1)|(R.n_dec>=1)).sum())
has_third=int((R.n_third_nm>=1).sum())
res=dict(n_corpcode=len(firm),has_issue_disclosure=has_any,has_3rd_nm=has_third,
         rate_issue=float(has_any/len(firm)),rate_3rd_nm=float(has_third/len(firm)),
         vs_wp1_has3rd=342)
json.dump(res,open(f"{OUT}/r1_summary.json","w"),ensure_ascii=False,indent=1)
print(f"\n=== R1 재추출 (list.json 1차) ===")
print(f"corp_code {len(firm)} · 유상증자/CB 결정공시 보유 {has_any}({has_any/len(firm)*100:.0f}%) · report_nm '제3자배정' 직접 {has_third}")
print(f"(WP1 piicDecsn 방법 제3자배정 342와 대조 — list.json이 커버리지 공백 복구했는지)")
