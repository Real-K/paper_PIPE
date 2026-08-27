# -*- coding: utf-8 -*-
"""P-016 트랙① — 조달목적(fdpp) 추출 (딜특성 moderator 후보; 평균회귀 무관).
treated 415(treatment_master_v2)의 piicDecsn(유상증자)·cvbdIsDecsn(CB) fdpp_* 필드 → 조달목적 금액.
분류: 지배목적=argmax(시설/영업양수/운영/채무상환/타법인증권/기타). 채무상환·운영 vs 시설·투자 대비.
산출: shared/outputs/pipe_wp8_2026-08-23/treatment_fdpp.csv
"""
import os,json,time,urllib.request,urllib.parse,warnings,itertools,re; warnings.filterwarnings("ignore")
import pandas as pd
BASE=os.environ.get("P016_BASE", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))   # 원 경로는 제거했다 — 실행 시 P016_BASE 로 지정하거나 기본값 사용
RE=f"{BASE}/shared/outputs/pipe_r1_reextract_2026-08-22"
OUT=f"{BASE}/shared/outputs/pipe_wp8_2026-08-23"; os.makedirs(OUT,exist_ok=True)
keys=[l.split("=",1)[1].strip() for l in open(os.path.expanduser("~/.claude/.env")) if l.startswith("DART_API_KEY") and l.split("=",1)[1].strip()]
kc=itertools.cycle(keys); print(f"DART 키 {len(keys)}개 (미출력)",flush=True)
def dget(ep,p):
    p=dict(p); p["crtfc_key"]=next(kc)
    for _ in range(3):
        try: return json.load(urllib.request.urlopen(f"https://opendart.fss.or.kr/api/{ep}?"+urllib.parse.urlencode(p),timeout=25))
        except: time.sleep(0.4)
    return {"status":"ERR"}
def num(x):
    try: return float(re.sub(r'[^\d.-]','',str(x))) if str(x).strip() not in ('','-') else 0.0
    except: return 0.0
FDPP=[("시설","fdpp_fclt"),("영업양수","fdpp_bsninh"),("운영","fdpp_op"),("채무상환","fdpp_dtrp"),("타법인증권","fdpp_ocsa"),("기타","fdpp_etc")]
T=pd.read_csv(f"{RE}/treatment_master_v2.csv",dtype=str); T["k"]=T["k"].str.replace(r'\D','',regex=True).str.zfill(10)
T["ev"]=pd.to_datetime(T["event_dt"],errors="coerce"); T=T.dropna(subset=["ev"]).drop_duplicates("k")
def evd(rc):
    try: return pd.to_datetime(str(rc)[:8],format="%Y%m%d")
    except: return pd.NaT
rows=[]
for i,r in enumerate(T.itertuples(),1):
    cc=r.cc; ev=r.ev; bgn=(ev-pd.Timedelta(days=30)).strftime("%Y%m%d"); end=(ev+pd.Timedelta(days=30)).strftime("%Y%m%d")
    best=None; bestgap=1e9
    for ep in ("piicDecsn.json","cvbdIsDecsn.json","bdwtIsDecsn.json"):
        R=dget(ep,{"corp_code":cc,"bgn_de":bgn,"end_de":end})
        if R.get("status")!="000": continue
        for it in R.get("list",[]):
            g=abs((evd(it.get("rcept_no"))-ev).days) if pd.notna(evd(it.get("rcept_no"))) else 999
            # fdpp 필드가 있는 레코드 우선
            has=any(f in it for _,f in FDPP)
            if has and g<bestgap: bestgap=g; best=(ep,it)
    if best is None:
        rows.append(dict(k=r.k,cc=cc,fdpp_found=False,dom_purpose="",**{p:0.0 for p,_ in FDPP}));
    else:
        ep,it=best; amts={p:num(it.get(f,0)) for p,f in FDPP}; tot=sum(amts.values())
        dom=max(amts,key=amts.get) if tot>0 else ""
        rows.append(dict(k=r.k,cc=cc,fdpp_found=True,src=ep,dom_purpose=dom,total=tot,**amts))
    if i%60==0:
        f=sum(1 for x in rows if x["fdpp_found"]); print(f"  [{i}/{len(T)}] fdpp 확보 {f}",flush=True)
    time.sleep(0.03)
D=pd.DataFrame(rows); D.to_csv(f"{OUT}/treatment_fdpp.csv",index=False,encoding="utf-8-sig")
import collections
found=int(D.fdpp_found.sum()); dist=dict(collections.Counter(D[D.fdpp_found].dom_purpose))
# 이분: 채무상환·운영(자금난) vs 시설·영업양수·타법인(투자/확장)
D["distress_purpose"]=D.dom_purpose.isin(["채무상환","운영"])
summ=dict(n=len(D),fdpp_found=found,dom_dist=dist,
          n_distress=int((D.fdpp_found&D.distress_purpose).sum()),
          n_invest=int((D.fdpp_found&~D.distress_purpose&(D.dom_purpose!="")).sum()))
json.dump(summ,open(f"{OUT}/treatment_fdpp_summary.json","w"),ensure_ascii=False,indent=1)
D.to_csv(f"{OUT}/treatment_fdpp.csv",index=False,encoding="utf-8-sig")
open(f"{OUT}/fdpp.done","w").write("done")
print(f"\n=== fdpp 완료 ===\nfdpp 확보 {found}/{len(D)} · 목적분포 {dist}\n채무상환·운영(자금난) {summ['n_distress']} vs 투자/확장 {summ['n_invest']}")
