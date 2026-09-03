# -*- coding: utf-8 -*-
"""WP15d — entity-restructuring 스크린 (comment2 §14, §8 후반).
NPS 고용이 법인(사업자번호) 단위이므로 합병·분할·영업/자산양수도·해산은 근로자가 경제에서
사라지지 않아도 원법인 headcount 를 크게 떨어뜨릴 수 있다(꼬리 측정위험). 기존 ±3일 스크린을
결과창 전체로 확장: 각 1차표본 이벤트의 [공시일−3d, 공시일+13개월] DART 공시목록에서
  reorg    = 합병|분할|영업양수·양도|자산양수·양도|주식교환·이전   (측정위험 핵심)
  dissol   = 해산|청산|폐업                                        (조직 소멸)
  ctrlchg  = 최대주주변경|경영권                                    (control-change, §8)
를 플래그하고, 해당 기업을 event·placebo 양팔에서 제외한 뒤 정본 대조(부트 B=4000)를 재산출.
플래그 CSV(사업자번호 포함)는 로컬 전용 — 공개 저장소 반입 금지.
"""
import os, json, time, re, urllib.request, urllib.parse, itertools, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd

BASE = "/mnt/c/obsidian/00 Academic Research/paper014-writing-project"
S13 = f"{BASE}/shared/outputs/pipe_wp13_2026-08-26"
OUT = f"{BASE}/shared/outputs/pipe_wp15_2026-09-03"; os.makedirs(OUT, exist_ok=True)
RNG = np.random.default_rng(20260903)
keys = [l.split("=", 1)[1].strip() for l in open(os.path.expanduser("~/.claude/.env"))
        if l.startswith("DART_API_KEY") and l.split("=", 1)[1].strip()]
kc = itertools.cycle(keys); print(f"DART 키 {len(keys)} (미출력)", flush=True)

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
       "dissol": re.compile(r"해산|청산|폐업"),
       "ctrlchg": re.compile(r"최대주주변경|경영권")}

U = pd.read_csv(f"{S13}/treatment_universe_v3.csv", dtype=str)
U["k"] = U.k.str.replace(r"\D", "", regex=True).str.zfill(10)
P = U[U.emp_primary == "True"].copy()
P["evd"] = pd.to_datetime(P.event_dt, format="%Y%m%d", errors="coerce")
print(f"1차표본 {len(P)} · corp_code 보유 {P.cc.notna().sum()}", flush=True)

FLAG = f"{OUT}/wp15d_flags.csv"                      # 로컬 전용(사업자번호 포함)
if os.path.exists(FLAG):
    C = pd.read_csv(FLAG, dtype=str); print("플래그 캐시 사용", flush=True)
else:
    rows = []
    for i, r in enumerate(P.itertuples(), 1):
        bgn = (r.evd - pd.Timedelta(days=3)).strftime("%Y%m%d")
        end = (r.evd + pd.Timedelta(days=396)).strftime("%Y%m%d")
        names = []
        for ty in ("A", "B", "C", "D", "E", "F", "I"):
            pg = 1
            while True:
                Rj = dget("list.json", {"corp_code": r.cc, "bgn_de": bgn, "end_de": end,
                                        "pblntf_ty": ty, "page_count": "100", "page_no": str(pg)})
                if Rj.get("status") != "000": break
                names += [it.get("report_nm", "") for it in Rj.get("list", [])]
                if pg >= int(Rj.get("total_page", 1)): break
                pg += 1
        hits = {lab: [] for lab in PAT}
        for nm in names:
            if SELF.search(nm): continue
            for lab, pat in PAT.items():
                if pat.search(nm): hits[lab].append(nm[:44])
        rows.append(dict(k=r.k, cc=r.cc, ev=str(r.evd.date()), n_filings=len(names),
                         reorg=int(bool(hits["reorg"])), dissol=int(bool(hits["dissol"])), ctrlchg=int(bool(hits["ctrlchg"])),
                         reorg_ex=(hits["reorg"][0] if hits["reorg"] else ""),
                         ctrl_ex=(hits["ctrlchg"][0] if hits["ctrlchg"] else "")))
        if i % 30 == 0:
            print(f"  [{i}/{len(P)}] reorg {sum(x['reorg'] for x in rows)} · dissol {sum(x['dissol'] for x in rows)} · ctrl {sum(x['ctrlchg'] for x in rows)}", flush=True)
        time.sleep(0.05)
    C = pd.DataFrame(rows); C.to_csv(FLAG, index=False, encoding="utf-8-sig")
C["k"] = C.k.str.zfill(10)
n = dict(reorg=int(C.reorg.astype(int).sum()), dissol=int(C.dissol.astype(int).sum()), ctrlchg=int(C.ctrlchg.astype(int).sum()))
print(f"결과창(−3d..+13m) 플래그: reorg {n['reorg']} · dissol {n['dissol']} · ctrlchg {n['ctrlchg']} / {len(C)}", flush=True)

# ── 제외 후 정본 대조 재산출 (캐시 기반) ──
A = pd.read_csv(f"{S13}/wp13c_dvec_cache.csv", dtype={"k": str})
ev = A[A.sh == 0].reset_index(drop=True); pl = A[A.sh != 0].reset_index(drop=True)
CUTS = (-0.50, -0.35, -0.25)
def stats8(a, b):
    o = dict(mean=float(np.mean(a) - np.mean(b)), median=float(np.median(a) - np.median(b)),
             p10=float(np.percentile(a, 10) - np.percentile(b, 10)),
             p25=float(np.percentile(a, 25) - np.percentile(b, 25)))
    for c in CUTS: o[f"sev{abs(int(c * 100))}"] = float(np.mean(a <= c) - np.mean(b <= c))
    return o
def boot8(EV, PL, B=4000):
    a0, b0 = EV.d.values, PL.d.values; obs = stats8(a0, b0)
    firms = np.array(sorted(set(EV.k) | set(PL.k)))
    ei = {f: np.where(EV.k.values == f)[0] for f in firms}; pi = {f: np.where(PL.k.values == f)[0] for f in firms}
    bs = []
    for _ in range(B):
        fs = firms[RNG.integers(0, len(firms), len(firms))]
        ia = np.concatenate([ei[f] for f in fs if len(ei[f])]); ib = np.concatenate([pi[f] for f in fs if len(pi[f])])
        if len(ia) < 20 or len(ib) < 20: continue
        bs.append(stats8(a0[ia], b0[ib]))
    out = {}
    for k in obs:
        v = np.array([x[k] for x in bs]); lo, hi = np.percentile(v, [2.5, 97.5])
        out[k] = dict(obs=round(obs[k], 4), ci=[round(float(lo), 4), round(float(hi), 4)], sig=bool(lo > 0 or hi < 0))
    out["n_event"] = int(len(EV)); out["n_placebo"] = int(len(PL))
    return out

R = {"flags": dict(n, n_primary=len(C), window="event−3d .. event+13m", source="DART list.json (wp11o 패턴 확장)")}
sets = {"ex_reorg": set(C[C.reorg.astype(int) == 1].k),
        "ex_reorg_dissol": set(C[(C.reorg.astype(int) == 1) | (C.dissol.astype(int) == 1)].k),
        "ex_reorg_ctrl": set(C[(C.reorg.astype(int) == 1) | (C.ctrlchg.astype(int) == 1)].k),
        "ex_all3": set(C[(C.reorg.astype(int) == 1) | (C.dissol.astype(int) == 1) | (C.ctrlchg.astype(int) == 1)].k)}
for nm, drop in sets.items():
    r = boot8(ev[~ev.k.isin(drop)].reset_index(drop=True), pl[~pl.k.isin(drop)].reset_index(drop=True))
    r["n_dropped"] = len(drop & set(ev.k)); R[nm] = r
    print(f"  {nm:<16} drop {r['n_dropped']:>3} → n {r['n_event']}/{r['n_placebo']}"
          f" · p10 {r['p10']['obs']:+.4f}{r['p10']['ci']} · sev35 {r['sev35']['obs']:+.4f}{r['sev35']['ci']}"
          f" · median {r['median']['obs']:+.4f}", flush=True)

verdict = (f"결과창 reorg {n['reorg']}건 제외 후 p10 {R['ex_reorg']['p10']['obs']}{R['ex_reorg']['p10']['ci']} · "
           f"sev35 {R['ex_reorg']['sev35']['obs']}{R['ex_reorg']['sev35']['ci']}. "
           f"3범주 전체 제외(n_drop {R['ex_all3']['n_dropped']}) 후 p10 {R['ex_all3']['p10']['obs']}{R['ex_all3']['p10']['ci']}.")
json.dump({"id": "WP15d", "title": "entity-restructuring 결과창 스크린 + 제외 재산출", "seed": 20260903,
           "runs": R, "verdict": verdict,
           "note": "wp15d_flags.csv 는 사업자번호 포함 — 로컬 전용, 공개 저장소 반입 금지."},
          open(f"{OUT}/wp15d_restruct.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("\n=== WP15d ===\n" + verdict)
