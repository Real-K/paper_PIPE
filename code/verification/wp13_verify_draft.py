# -*- coding: utf-8 -*-
"""P-016 원고 수치 검증 — 본문·표의 모든 수치가 산출물(JSON)에 존재하는지 기계 대조.

C-A(처치우주 재구축)로 표본이 바뀌면 원고 곳곳의 수치가 조용히 낡는다. 태그에 의존하지 않고
**숫자 자체**를 산출 풀과 대조해 낡은 값을 전수 적발한다. (설계 선례: P-014 `build/verify_draft.py`)

사용: python3 wp13_verify_draft.py [원고경로 ...]
출력: 미매칭 수치 목록(줄번호·문맥) + 요약. 종료코드 1 = 미매칭 존재.
"""
import json,os,re,sys,glob
from decimal import Decimal,ROUND_HALF_UP
BASE="/mnt/c/obsidian/00 Academic Research/paper014-writing-project"
NEW=f"{BASE}/shared/outputs/pipe_wp13_2026-08-26"; W12=f"{BASE}/shared/outputs/pipe_wp12_2026-08-26"
SUB=f"{BASE}/papers/P016_pipe-employment/10_submission/submission_pbfj"
POOL={}
def add(v,src):
    try: x=float(v)
    except (TypeError,ValueError): return
    if not abs(x)<1e12: return
    for f in (1,100,-1,-100):
        y=x*f
        for nd in range(0,7):
            POOL.setdefault(round(y,nd),src)
            try: POOL.setdefault(float(Decimal(repr(y)).quantize(Decimal(1).scaleb(-nd),ROUND_HALF_UP)),src)
            except Exception: pass
def harvest(o,src):
    if isinstance(o,dict):
        for v in o.values(): harvest(v,src)
    elif isinstance(o,(list,tuple)):
        for v in o: harvest(v,src)
    elif isinstance(o,(int,float)) and not isinstance(o,bool): add(o,src)
# 폐기된 구 산출물은 풀에서 제외한다. 남겨두면 **원고의 낡은 수치가 그 파일과 매칭돼 검증을 통과**한다
# (실사례: 상폐의심 꼬리집중 21.2%/9.8% 가 wp13e 로 철회됐는데 구 wp9f_bhar_bounds.json 때문에 통과).
SUPERSEDED={"wp9f_bhar_bounds","wp9b_disappearance","wp9d_car_predict","wp11i_rd_probe",
            "wp11n_allottee_moderator","allottee_summary","wp8c_purpose_moderator","wp10g_gapfill",
            "wp11m_datefix_impact"}   # wp13d/e/f 로 대체됨. wp11c 는 제외하지 않는다 — 부록 D Table D1 Panel B 가 구 비교군을 **의도적으로** 보고하므로(rule 10) 정당한 인용원이다.
_all=sorted(glob.glob(f"{NEW}/*.json"))+sorted(glob.glob(f"{W12}/*.json"))
srcs=[p for p in _all if os.path.basename(p)[:-5] not in SUPERSEDED]
dead_srcs=[p for p in _all if os.path.basename(p)[:-5] in SUPERSEDED]
print(f"폐기 제외 {len(SUPERSEDED)}종 · 디스크에서 발견 {len(dead_srcs)}개:",", ".join(sorted(SUPERSEDED)))
LIVE_RAW=[]; DEAD_RAW={}
def raw(o,sink):
    if isinstance(o,dict):
        for v in o.values(): raw(v,sink)
    elif isinstance(o,(list,tuple)):
        for v in o: raw(v,sink)
    elif isinstance(o,(int,float)) and not isinstance(o,bool): sink.append(float(o))
for p in srcs:
    try:
        d=json.load(open(p,encoding="utf-8")); harvest(d,os.path.basename(p)[:-5]); raw(d,LIVE_RAW)
    except Exception as e: print(f"  (경고) {os.path.basename(p)}: {e}")
for p in dead_srcs:
    try:
        sink=[]; raw(json.load(open(p,encoding="utf-8")),sink); DEAD_RAW[os.path.basename(p)[:-5]]=sink
    except Exception as e: print(f"  (경고, 폐기) {os.path.basename(p)}: {e}")
# 표본 흐름 정수 등 CSV 행수도 정당한 인용원
for p in sorted(glob.glob(f"{NEW}/*.csv")):
    try: add(sum(1 for _ in open(p,encoding="utf-8-sig"))-1,os.path.basename(p)+":rows")
    except Exception: pass
try:
    import pandas as pd
    U=pd.read_csv(f"{NEW}/treatment_universe_v3.csv",dtype=str)
    for c in ("cls","src"):
        for k,v in U[c].value_counts().items(): add(v,f"universe.{c}={k}")
    for c in U.columns:
        vc=U[c].astype(str).str.lower().isin(["true","1","1.0"]).sum()
        if vc: add(int(vc),f"universe.{c}")
    add(len(U),"universe.rows")
except Exception as e: print(f"  (경고) universe: {e}")
print(f"풀 {len(POOL):,}개 값 · 출처 {len(srcs)} JSON")

# --- 철회·폐기 문자열 차단 -------------------------------------------------
# 풀 대조만으로는 못 잡는 것들이 있다. 정수(26·205·117)는 다른 출처와 우연히 매칭되고,
# **철회된 주장**은 폐기 JSON 을 지워도 새 산출에 우연히 같은 값이 있으면 통과한다.
# 그래서 "원고에 남아 있으면 안 되는 문자열" 을 직접 차단한다. (2026-08-27, WP13e/f 결과 반영)

# --- 폐기 산출물에서 차단 수치 자동도출 (P-014 build/verify_draft.py 이식, 2026-08-27) --------
# 손으로 관리하는 RETRACTED 목록은 다음에 또 놓친다. 폐기 JSON 을 풀에서 빼는 것만으로는
# **같은 값이 살아있는 다른 산출물에도 있으면** 여전히 통과하므로, 폐기 JSON 의 값 자체를 막는다.
# 안전장치 두 겹: (a) 살아있는 값과 겹치면 제외 — 우연 일치를 오탐하지 않는다.
# (b) 소수 3자리 이상이거나 4자리 이상 정수인 '특징적인' 값만 — 2·26·205 같은 흔한 수를 막으면
#     검증기가 쓸모없어진다. (c) 살아있는 값이 **반올림해서** 폐기값과 같아지는 경우도 살려둔다.
def build_stale(live_raw, dead_by_src):
    live=set(round(abs(x),6) for x in live_raw)
    def distinctive(x):
        a=abs(x)
        if a!=a or a>1e11: return None
        st=repr(float(x)).rstrip("0").rstrip(".") if "." in repr(float(x)) else repr(float(x))
        frac=len(st.split(".")[1]) if "." in st else 0
        if not (frac>=3 or (frac==0 and a>=1000)): return None
        return round(a,6), frac
    out={}
    for src,vals in dead_by_src.items():
        for x in vals:
            d=distinctive(x)
            if d is None: continue
            v,nd=d
            if v in live: continue
            if any(round(abs(y),nd)==v for y in live_raw): continue   # 반올림 충돌
            out.setdefault(v,src)
    return out
STALE=build_stale(LIVE_RAW,DEAD_RAW)
print(f"폐기 수치 자동도출 {len(STALE)}종 (폐기 JSON {len(DEAD_RAW)}개 · 살아있는 값 {len(set(round(abs(x),6) for x in LIVE_RAW)):,}종과 대조)")

RETRACTED=[
 ("21.2",   "철회: 상폐의심의 고용꼬리 집중 — 신 15.1%(8/53) vs 12.8%(20/156) Fisher p=0.6472 (wp13e)"),
 ("Twenty-six of 205", "구 우주: 신 Twenty-eight of 209 (13.4%) (wp13e)"),
 ("12,480", "구 RD 표본: 신 26,031 firm-years / 2,607 listed (wp13f)"),
 ("n = 117", "구 subgroup: 신 rescue n = 120, ATT −0.0561 [−0.120,+0.004] (wp13e)"),
 ("65.4",   "구 배정대상자 기타 비중: 신 69.3% (wp13f)"),
 ("0.0072", "구 BHAR 관측 p: 신 0.0074 (wp13e)"),
 ("0.0426", "구 BHAR 하한 p: 신 0.043 (wp13e)"),
 ("77% rescue", "구 결측기업 구성: 신 71% rescue · 7% growth · 29% tail (wp13e)"),
]
def check_retracted(paths):
    hits=0
    for t in paths:
        inref=False
        for i,ln in enumerate(open(t,encoding="utf-8"),1):
            if re.match(r"#+\s*References",ln): inref=True
            if inref: continue
            for pat,why in RETRACTED:
                if pat in ln:
                    hits+=1; print(f"  ⛔ {os.path.basename(t)} L{i}  '{pat}'  — {why}")
    return hits

SKIP_CTX=re.compile(r"(Section|Table|Panel|Appendix|Figure|Equation|footnote|Article|Act|20[0-2]\d|19[89]\d)",re.I)
# 4자리 이상을 쉼표 없이 쓴 수(12480)를 종전 정규식이 통째로 놓쳤다 — 그래서 폐기 RD 표본
# 12,480 은 문자열 차단으로만 막히고 있었다. 쉼표군 또는 연속 숫자열을 모두 잡는다.
NUM=re.compile(r"(?<![\w.])[-−+]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?(?![\w])")
def norm(s): return float(s.replace("−","-").replace(",","").replace("+",""))
targets=sys.argv[1:] or [f"{SUB}/PBFJ_manuscript_anonymized.md",f"{SUB}/PBFJ_online_supplement.md",f"{SUB}/PBFJ_cover_letter.md",f"{SUB}/PBFJ_highlights.md"]
tot=bad=stale_tot=0
for t in targets:
    miss=[]; stale_hits=[]
    inref=False
    for i,ln in enumerate(open(t,encoding="utf-8"),1):
        if re.match(r"#+\s*References",ln): inref=True
        if inref or "doi.org" in ln: continue                       # 참고문헌(권·호·페이지·DOI)은 데이터 수치가 아니다
        if ln.lstrip().startswith(("*Notes","*Source","| Source")): continue
        if re.search(r"Article\s+\d|Act\b",ln): continue           # 법조문 번호
        for m in NUM.finditer(ln):
            s=m.group()
            try: v=norm(s)
            except ValueError: continue
            if v!=v or abs(v)>1e11: continue
            if 1980<=v<=2030 and float(v).is_integer(): continue          # 연도
            w=ln[max(0,m.start()-28):m.start()]
            if SKIP_CTX.search(w) and float(v).is_integer() and abs(v)<40: continue  # 절·표 번호
            tot+=1
            av=round(abs(v),6)
            if av in STALE: stale_hits.append((i,s,STALE[av],ln.strip()[:120]))
            if round(v,6) in POOL: continue
            miss.append((i,s,ln.strip()[:150]))
    bad+=len(miss); stale_tot+=len(stale_hits)
    print(f"\n### {os.path.basename(t)} — 미매칭 {len(miss)} · 폐기수치 {len(stale_hits)}")
    for i,s,ctx in miss[:200]: print(f"  L{i:<4} {s:>12}   {ctx}")
    for i,s,src,ctx in stale_hits[:200]: print(f"  🔴 L{i:<4} {s:>12}  폐기 {src} 에서만 나오는 값   {ctx}")
print("\n[철회·폐기 문자열 검사]")
rh=check_retracted(targets)
if not rh: print("  없음")
print(f"\n총 검사 {tot} · 미매칭 {bad} · 철회문자열 {rh} · 폐기수치 {stale_tot}")
print("  주: '127'(NPS 패널 개월수)은 JSON 에 없는 자료 사실이라 항상 미매칭으로 잡힌다 — 마감 기준 미매칭 3.")
sys.exit(1 if (bad>3 or rh or stale_tot) else 0)
