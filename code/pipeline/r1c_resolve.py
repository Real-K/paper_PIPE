# -*- coding: utf-8 -*-
"""P-016 R1c — 013-잔여 28사 원문 배정방법 파싱 (처치정의 무결성). outcome-blind.
문제: 28사는 list.json에 유상증자/CB 결정공시(활성, 철회아님)가 있으나 구조화 piicDecsn가 status 013(데이터없음)
      → ic_mthn 미확인. false-negative(미분류 제3자배정) 방지 위해 document.xml 원문 증자방식/배정방법 파싱.
분류: 유상증자 '제3자배정증자' → third / '주주배정'·'일반공모' → non. CB '사모'·'제3자' → third.
산출: r1c_resolved.csv + r1c_summary.json. 키 로테이션 미출력.
"""
import os,json,time,io,zipfile,urllib.request,urllib.parse,warnings,itertools,re; warnings.filterwarnings("ignore")
import pandas as pd
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
def ddoc(rcept):
    url=f"https://opendart.fss.or.kr/api/document.xml?"+urllib.parse.urlencode({"crtfc_key":next(kc),"rcept_no":rcept})
    for _ in range(3):
        try:
            raw=urllib.request.urlopen(url,timeout=40).read()
            try:
                z=zipfile.ZipFile(io.BytesIO(raw)); txt=""
                for n in z.namelist():
                    b=z.read(n)
                    for enc in ("utf-8","cp949","euc-kr"):
                        try: txt+=b.decode(enc); break
                        except: pass
                return txt
            except zipfile.BadZipFile:
                return raw.decode("utf-8","ignore")
        except: time.sleep(0.6)
    return ""
def rn_dt(rn):
    try: return pd.to_datetime(str(rn)[:8],format="%Y%m%d")
    except: return pd.NaT

tgt=json.load(open(f"{OUT}/r1c_targets.json",encoding='utf-8'))
ev=pd.read_csv(f"{OUT}/r1_events.csv",dtype=str)
ev.columns=[c.strip().lstrip('﻿') for c in ev.columns]
ccinfo={r.cc:(r.dd,str(r.yearonly).lower()=="true") for r in ev.itertuples()}
PAT_DEC=re.compile(r'유상증자결정|전환사채권발행결정|신주인수권부사채권발행결정|교환사채권발행결정')

def classify_txt(t):
    t=re.sub(r'<[^>]+>',' ',t); t=re.sub(r'\s+','',t)  # 태그·공백 제거
    third_eq = "제3자배정증자" in t
    rights   = ("주주배정증자" in t) or ("주주배정후" in t) or ("주주우선공모" in t)
    public   = "일반공모증자" in t
    samo     = "사모" in t
    third_g  = "제3자배정" in t
    return dict(third_eq=third_eq,rights=rights,public=public,samo=samo,third_g=third_g)

rows=[]
for i,t in enumerate(tgt,1):
    cc=t["cc"]; k=t["k"]; dd,yo=ccinfo.get(cc,(None,False))
    dd=pd.to_datetime(dd) if dd else None
    if yo and dd is not None: bgn=f"{dd.year}0101"; end=f"{dd.year+1}0630"
    elif dd is not None: bgn=(dd-pd.Timedelta(days=365)).strftime("%Y%m%d"); end=(dd+pd.Timedelta(days=120)).strftime("%Y%m%d")
    else: bgn="20100101"; end="20251231"
    # list.json 재호출 → 결정공시 rcept 수집
    hits=[]
    for ty in ("B","C"):
        for pg in (1,2):
            L=dget("list.json",{"corp_code":cc,"bgn_de":bgn,"end_de":end,"pblntf_ty":ty,"page_no":str(pg),"page_count":"100"})
            if L.get("status")!="000": break
            for it in L.get("list",[]):
                nm=it.get("report_nm","")
                if PAT_DEC.search(nm):
                    hits.append({"rcept":it.get("rcept_no"),"nm":nm,"cb":("사채" in nm)})
            if int(L.get("total_page",1))<=pg: break
        time.sleep(0.04)
    # rcept desc: 최신 정정 우선(최종 상태 반영), 최대 3건 파싱
    hits=sorted({h["rcept"]:h for h in hits}.values(),key=lambda h:h["rcept"],reverse=True)
    agg=dict(third_eq=False,rights=False,public=False,samo=False,third_g=False); is_cb_any=any(h["cb"] for h in hits)
    parsed=0
    for h in hits[:3]:
        txt=ddoc(h["rcept"])
        if not txt: continue
        c=classify_txt(txt); parsed+=1
        for key in agg: agg[key]=agg[key] or c[key]
        time.sleep(0.05)
        if agg["third_eq"]: break  # 명확한 제3자배정증자면 조기 확정
    # 판정
    if agg["third_eq"]: verdict="third_equity"
    elif is_cb_any and (agg["samo"] or agg["third_g"]) and not agg["public"]: verdict="third_cb"
    elif agg["rights"] or agg["public"]: verdict="non_third"
    elif agg["third_g"]: verdict="third_generic"      # 제3자배정(증자 접미 없음) — 약신호
    else: verdict="unresolved"
    is_treat = verdict in ("third_equity","third_cb","third_generic")
    # 이벤트일: 결정공시 최소 rcept (원공시)
    dts=[rn_dt(h["rcept"]) for h in hits if pd.notna(rn_dt(h["rcept"]))]
    ev_dt = min(dts).date().isoformat() if dts else ""
    rows.append(dict(k=k,cc=cc,n_dec=len(hits),parsed=parsed,verdict=verdict,is_treat=is_treat,
                     event_dt=ev_dt,is_cb=is_cb_any,**{f"doc_{kk}":vv for kk,vv in agg.items()}))
    if i%7==0:
        nt=sum(1 for r in rows if r["is_treat"])
        print(f"  [{i}/28] 처치확정 {nt} · 미해결 {sum(1 for r in rows if r['verdict']=='unresolved')}",flush=True)

R=pd.DataFrame(rows); R.to_csv(f"{OUT}/r1c_resolved.csv",index=False,encoding="utf-8-sig")
import collections
vc=dict(collections.Counter(r["verdict"] for r in rows))
n_treat=int(sum(1 for r in rows if r["is_treat"]))
n_evt=int(sum(1 for r in rows if r["is_treat"] and r["event_dt"]))
res=dict(n_targets=len(rows),verdict_counts=vc,new_treat=n_treat,new_treat_with_event=n_evt,
         still_unresolved=int(sum(1 for r in rows if r["verdict"]=="unresolved")),
         corrected_treat_total=390+n_treat, corrected_event_total=357+n_evt)
json.dump(res,open(f"{OUT}/r1c_summary.json","w"),ensure_ascii=False,indent=1)
print("\n=== R1c 원문 파싱 (013-잔여 28) ===")
print("verdict:",vc)
print(f"신규 처치확정 {n_treat} (이벤트일 {n_evt}) · 미해결 {res['still_unresolved']}")
print(f"→ 교정 처치총계 390+{n_treat}={res['corrected_treat_total']} · 이벤트확보 357+{n_evt}={res['corrected_event_total']}")
open(f"{OUT}/r1c.done","w").write("done")
