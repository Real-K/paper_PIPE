# -*- coding: utf-8 -*-
"""i01 — severe 꼬리 35건의 플래그 사례 타이밍 감사 (power-rescue 후속 ①, comment2 §14 심화).

왜. wp15d에서 결과창(−3d..+13m) reorg 공시 57건 제외 시 p10이 −0.253→−0.137로 감쇠했고,
ctrlchg 공시는 severe 35건 중 25건(71%)과 공행했다. 감쇠분이 '측정 인공물'(합병·분할·양수도로
근로자가 타법인 등록으로 이동)인지 '실제 수축 후 재조직'인지는 **선후관계**로 분리할 수 있다:
고용 하락이 공시보다 먼저면 인공물 설명이 약해지고, 공시가 먼저면 해당 사례는 인공물 위험이 실재한다.

Panel.
  A. severe(매칭 d≤−0.35) 35건 중 reorg/ctrlchg 플래그 사례의 첫 해당 공시월(DART 재조회, rcept_dt).
  B. 자기(own) 고용 하락월: 기준창 평균 대비 자기 log 고용이 처음 −0.35 이하로 떨어진 월
     (탐색창 e−2..e+12; 미도달이면 no_own_cross — 대조군 상대로만 severe인 사례).
     보조: 최심월(argmin) 기준 분류 병기.
  C. 분류: drop_first(하락월 < 공시월) / same_month / filing_first / no_own_cross. 범주별 계수.

사전 예측 (실행 전 기입).
  reorg 14건: 우세 패턴 미지. drop_first(+no_own_cross 제외 기준) ≥60% → GO(측정 반박 강화,
  D.3 문안에 '하락이 공시에 선행' 문장 추가). filing_first ≥60% → KILL(해당 사례는 인공물 위험 실재 —
  D.3 감쇠 해석을 '측정 기인 가능'으로 강화 수정). 그 외 PARTIAL.
  ctrlchg 25건: drop_first 우세면 '수축 → control 전환' 서사 지지(state-revelation 강화).
  filing_first 우세면 'control 전환 → 수축'(acquisition-effect 우려) — §8 문안 보수화.

산출: out/I01.json (집계·오프셋만, 식별자 없음) · work/i01_case_detail.csv (사업자번호 포함 — 로컬 전용).
seed 불요(결정적). DART 재조회 ~30기업.
"""
import os, sys, json, time, re, urllib.request, urllib.parse, itertools, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.environ.setdefault("HARNESS_OUT", "/mnt/c/obsidian/00 Academic Research/paper014-writing-project/shared/outputs/pipe_wp15_2026-09-03/out")
os.environ.setdefault("PROJECT_BASE", "/mnt/c/obsidian/00 Academic Research/paper014-writing-project")
from emit_contract import emit

src = open(os.path.join(HERE, "wp13c_pooled_placebo.py"), encoding="utf-8").read()
i = src.find("SHIFTS=[18,24,30,36]")
ns = {"__name__": "i01_reuse"}
exec(compile(src[:src.rfind("\n", 0, i)], "wp13c(head)", "exec"), ns)
LE, firm_ix, mi, T = ns["LE"], ns["firm_ix"], ns["mi"], ns["T"]
BASE = ns["BASE"]; S13 = f"{BASE}/shared/outputs/pipe_wp13_2026-08-26"
O15 = f"{BASE}/shared/outputs/pipe_wp15_2026-09-03"
WORK = f"{O15}/work"; os.makedirs(WORK, exist_ok=True)

cache = pd.read_csv(f"{S13}/wp13c_dvec_cache.csv", dtype={"k": str})
sev_k = set(cache[(cache.sh == 0) & (cache.d <= -0.35)].k)
FL = pd.read_csv(f"{O15}/wp15d_flags.csv", dtype=str); FL["k"] = FL.k.str.zfill(10)
for c in ("reorg", "dissol", "ctrlchg"): FL[c] = FL[c].astype(int)
FS = FL[FL.k.isin(sev_k) & ((FL.reorg == 1) | (FL.ctrlchg == 1))].copy()
print(f"severe {len(sev_k)} · 플래그 보유 severe {len(FS)} (reorg {FS.reorg.sum()} · ctrlchg {FS.ctrlchg.sum()})", flush=True)

# ── A. DART 재조회: 범주별 첫 공시일 ──
keys = [l.split("=", 1)[1].strip() for l in open(os.path.expanduser("~/.claude/.env"))
        if l.startswith("DART_API_KEY") and l.split("=", 1)[1].strip()]
kc = itertools.cycle(keys)
def dget(ep, p):
    p = dict(p); p["crtfc_key"] = next(kc)
    for _ in range(3):
        try:
            return json.load(urllib.request.urlopen(f"https://opendart.fss.or.kr/api/{ep}?" + urllib.parse.urlencode(p), timeout=25))
        except Exception:
            time.sleep(0.4)
    return {"status": "ERR"}
SELF = re.compile(r"유상증자결정|전환사채권발행결정|신주인수권부사채권발행결정|교환사채권발행결정|증권발행실적보고서|증권신고서|투자설명서|정정신고")
PAT = {"reorg": re.compile(r"합병|분할|영업양수|영업양도|자산양수|자산양도|주식교환|주식이전"),
       "ctrlchg": re.compile(r"최대주주변경|경영권")}

DCACHE = f"{WORK}/i01_filing_dates.csv"
if os.path.exists(DCACHE):
    FD = pd.read_csv(DCACHE, dtype=str); print("공시일 캐시 사용", flush=True)
else:
    rows = []
    for n_, r in enumerate(FS.itertuples(), 1):
        evd = pd.to_datetime(r.ev)
        bgn = (evd - pd.Timedelta(days=3)).strftime("%Y%m%d"); end = (evd + pd.Timedelta(days=396)).strftime("%Y%m%d")
        first = {}
        for ty in ("A", "B", "C", "D", "E", "F", "I"):
            pg = 1
            while True:
                Rj = dget("list.json", {"corp_code": r.cc, "bgn_de": bgn, "end_de": end,
                                        "pblntf_ty": ty, "page_count": "100", "page_no": str(pg)})
                if Rj.get("status") != "000": break
                for it in Rj.get("list", []):
                    nm = it.get("report_nm", ""); dt = it.get("rcept_dt", "")
                    if SELF.search(nm) or not dt: continue
                    for lab, pat in PAT.items():
                        if pat.search(nm) and (lab not in first or dt < first[lab]): first[lab] = dt
                if pg >= int(Rj.get("total_page", 1)): break
                pg += 1
        rows.append(dict(k=r.k, ev=r.ev, reorg_dt=first.get("reorg", ""), ctrl_dt=first.get("ctrlchg", "")))
        if n_ % 10 == 0: print(f"  [{n_}/{len(FS)}]", flush=True)
        time.sleep(0.05)
    FD = pd.DataFrame(rows); FD.to_csv(DCACHE, index=False, encoding="utf-8-sig")

# ── B. 자기 고용 하락월 ──
evm = {r.k: mi.get(r.ev) for r in T.itertuples()}
def drop_months(k):
    fi = firm_ix.get(k); e = evm.get(k)
    if fi is None or e is None: return None, None
    row = LE[fi]; base = np.nanmean(row[e - 12:e])
    if not np.isfinite(base): return None, None
    gap = row[e - 2:e + 13] - base                    # 오프셋 −2..+12
    cross = None
    for j, g in enumerate(gap):
        if np.isfinite(g) and g <= -0.35: cross = j - 2; break
    fin = np.where(np.isfinite(gap))[0]
    deep = (int(fin[np.argmin(gap[fin])]) - 2) if fin.size else None
    return cross, deep

def month_off(k, dt):
    if not isinstance(dt, str) or len(dt) != 8: return None
    e = evm.get(k)
    fm = pd.Period(f"{dt[:4]}-{dt[4:6]}", freq="M")
    ev_p = [r.ev for r in T.itertuples() if r.k == k][0]
    return (fm - ev_p).n

def classify(drop, fil):
    if fil is None: return None
    if drop is None: return "no_own_cross"
    if drop < fil: return "drop_first"
    if drop == fil: return "same_month"
    return "filing_first"

det = []
for r in FD.itertuples():
    cross, deep = drop_months(r.k)
    ro = month_off(r.k, r.reorg_dt); co = month_off(r.k, r.ctrl_dt)
    det.append(dict(k=r.k, own_cross_m=cross, own_deepest_m=deep, reorg_m=ro, ctrl_m=co,
                    cls_reorg=classify(cross, ro), cls_ctrl=classify(cross, co),
                    cls_reorg_deep=classify(deep, ro), cls_ctrl_deep=classify(deep, co)))
D = pd.DataFrame(det); D.to_csv(f"{WORK}/i01_case_detail.csv", index=False, encoding="utf-8-sig")

def tab(col, universe):
    s = D[D[col].notna()][col]
    out = {c: int((s == c).sum()) for c in ("drop_first", "same_month", "filing_first", "no_own_cross")}
    out["n"] = int(len(s)); out["universe"] = universe
    return out
est = {
    "reorg_primary": tab("cls_reorg", "severe∩reorg (first cross ≤−0.35)"),
    "ctrl_primary": tab("cls_ctrl", "severe∩ctrlchg (first cross ≤−0.35)"),
    "reorg_deepest": tab("cls_reorg_deep", "severe∩reorg (deepest month)"),
    "ctrl_deepest": tab("cls_ctrl_deep", "severe∩ctrlchg (deepest month)"),
    "offsets": {
        "reorg_filing_m": sorted(int(x) for x in D.reorg_m.dropna()),
        "ctrl_filing_m": sorted(int(x) for x in D.ctrl_m.dropna()),
        "own_cross_m": sorted(int(x) for x in D.own_cross_m.dropna()),
    },
}
for k_ in ("reorg_primary", "ctrl_primary"):
    t = est[k_]; nn = max(t["n"] - t["no_own_cross"], 1)
    t["share_drop_first_of_crossed"] = round((t["drop_first"]) / nn, 3)
    t["share_filing_first_of_crossed"] = round((t["filing_first"]) / nn, 3)
print(json.dumps(est, ensure_ascii=False, indent=1), flush=True)

rp = est["reorg_primary"]; cp = est["ctrl_primary"]
sd, sf = rp["share_drop_first_of_crossed"], rp["share_filing_first_of_crossed"]
status = "GO" if sd >= 0.6 else ("KILL" if sf >= 0.6 else "PARTIAL")
verdict = (f"reorg∩severe n={rp['n']}: drop_first {rp['drop_first']} · same {rp['same_month']} · filing_first {rp['filing_first']} · "
           f"no_own_cross {rp['no_own_cross']} (교차사례 중 drop_first {sd:.0%}/filing_first {sf:.0%}). "
           f"ctrl∩severe n={cp['n']}: drop_first {cp['drop_first']} · same {cp['same_month']} · filing_first {cp['filing_first']} · no_cross {cp['no_own_cross']}.")
emit("I-01", "severe 꼬리 플래그 사례 타이밍 감사 (하락월 vs 첫 공시월)", status, est,
     prediction="reorg: drop_first≥60%→GO(측정 반박 강화)/filing_first≥60%→KILL(인공물 위험 실재)/그 외 PARTIAL. ctrl: drop_first 우세면 수축→control 전환 서사 지지.",
     verdict=verdict, kill_met=(status == "KILL"), n=int(len(D)),
     extra={"security": "per-case 상세(work/i01_case_detail.csv)는 사업자번호 포함 — 로컬 전용. JSON은 오프셋·계수만."})
