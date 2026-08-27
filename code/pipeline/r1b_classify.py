# -*- coding: utf-8 -*-
"""P-016 R1b — R1의 421 결정공시를 ic_mthn으로 제3자배정 분류 + 013-잔여 정량화. outcome-blind.
목적: 교정 처치 N(제3자배정 신주발행) 확정 + piicDecsn 013 공백 잔여 크기 판정(문서파싱 필요 여부).
"""
import os,json,time,urllib.request,urllib.parse,warnings,itertools,re; warnings.filterwarnings("ignore")
import pandas as pd,numpy as np
BASE=os.environ.get("P016_BASE", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))   # 원 경로는 제거했다 — 실행 시 P016_BASE 로 지정하거나 기본값 사용
OUT=f"{BASE}/shared/outputs/pipe_r1_reextract_2026-08-22"
keys=[l.split("=",1)[1].strip() for l in open(os.path.expanduser("~/.claude/.env")) if l.startswith("DART_API_KEY") and l.split("=",1)[1].strip()]
kc=itertools.cycle(keys); print(f"키 {len(keys)} (미출력)",flush=True)
def dget(ep,p):
    p=dict(p); p["crtfc_key"]=next(kc)
    for _ in range(3):
        try: return json.load(urllib.request.urlopen(f"https://opendart.fss.or.kr/api/{ep}?"+urllib.parse.urlencode(p),timeout=25))
        except: time.sleep(0.5)
    return {"status":"ERR"}
R=pd.read_csv(f"{OUT}/r1_events.csv",dtype=str)
R["n_dec"]=pd.to_numeric(R.n_dec,errors="coerce").fillna(0)
have=R[R.n_dec>=1].copy()   # 결정공시 보유 421
print(f"결정공시 보유 {len(have)} 분류",flush=True)
def yr_window(dd_str,yo):
    d=pd.to_datetime(dd_str)
    if str(yo).lower()=="true": return f"{d.year}0101",f"{d.year+1}0630"
    return (d-pd.Timedelta(days=365)).strftime("%Y%m%d"),(d+pd.Timedelta(days=120)).strftime("%Y%m%d")
rows=[]
for i,r in enumerate(have.itertuples(),1):
    bgn,end=yr_window(r.dd,r.yearonly)
    P=dget("piicDecsn.json",{"corp_code":r.cc,"bgn_de":bgn,"end_de":end})
    st=P.get("status")
    third=0; rights=0; public=0; other=0; gap=0; ev=None
    if st=="000":
        for it in P.get("list",[]):
            m=str(it.get("ic_mthn",""))
            if "제3자배정" in m:
                third+=1; d=str(it.get("rcept_no",""))[:8]
                if ev is None or d<ev: ev=d  # 창내 최초 제3자배정 결의
            elif "주주배정" in m: rights+=1
            elif "일반공모" in m or "공모" in m: public+=1
            elif m and m!="-": other+=1
    elif st=="013": gap=1   # 유상증자결정 무자료 — CB만이거나 API 공백
    # CB류도 확인(013이거나 유상증자 제3자 없을 때)
    cb_third=0
    if third==0:
        for ep in ("cvbdIsDecsn.json","bdwtIsDecsn.json"):
            C=dget(ep,{"corp_code":r.cc,"bgn_de":bgn,"end_de":end})
            if C.get("status")=="000":
                for it in C.get("list",[]):
                    blob=" ".join(str(v) for v in it.values())
                    if "제3자배정" in blob or "사모" in str(it.get("bdis_mthn","")): cb_third+=1
    rows.append({"k":r.k,"cc":r.cc,"piic_status":st,"third_equity":third,"rights":rights,"public":public,
                 "other":other,"gap013":gap,"cb_third":cb_third,"event_dt":ev,
                 "is_treat_3rd": (third>=1) or (cb_third>=1)})
    if i%50==0:
        tr=np.mean([x["is_treat_3rd"] for x in rows]); g=np.mean([x["gap013"] for x in rows])
        print(f"  [{i}/{len(have)}] 제3자배정 {tr*100:.0f}% · 013공백 {g*100:.0f}%",flush=True)
    time.sleep(0.1)
D=pd.DataFrame(rows); D.to_csv(f"{OUT}/r1b_classified.csv",index=False,encoding="utf-8-sig")
res=dict(n_decision=len(have),
         treat_3rd=int(D.is_treat_3rd.sum()),
         third_equity=int((D.third_equity>=1).sum()),cb_third=int((D.cb_third>=1).sum()),
         rights_only=int(((D.rights>=1)&(D.third_equity==0)&(D.cb_third==0)).sum()),
         public_only=int(((D.public>=1)&(D.third_equity==0)&(D.cb_third==0)).sum()),
         gap013=int(D.gap013.sum()),
         gap013_no_class=int(((D.gap013==1)&(~D.is_treat_3rd)).sum()),
         has_event_dt=int(D.event_dt.notna().sum()),
         vs_wp1_342=342,vs_wp1_213=213)
json.dump(res,open(f"{OUT}/r1b_summary.json","w"),ensure_ascii=False,indent=1)
print(f"\n=== R1b 분류 (결정공시 {len(have)}) ===")
print(f"제3자배정 처치(유상증자 {res['third_equity']}+CB {res['cb_third']}) = **{res['treat_3rd']}** (WP1 342 대비)")
print(f"주주배정only {res['rights_only']} · 공모only {res['public_only']} · 이벤트일 확보 {res['has_event_dt']}")
print(f"piicDecsn 013공백 {res['gap013']} · 그중 미분류 잔여 {res['gap013_no_class']} (문서파싱 필요분)")
