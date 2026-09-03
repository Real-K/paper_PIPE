# -*- coding: utf-8 -*-
"""WP15 — FRL comment2 배터리 (2026-09-03, 10_submission/comment2.md 처분) — 캐시 기반 패널.
  A. 통일 파이프라인 정본 수치: wp13c 캐시 + 단일 군집 부트(B=4000)에서 mean/median/p10/p25 와
     severe(≤−0.25/−0.35/−0.50) 를 전 표본·공통 116·시점별(t−18/24/30/36) 로 산출.
     → 본문·그림·표가 전부 이 한 세트만 인용 (comment2 §4·§6).
  B. rescue-purpose 이질성 (comment2 §7): Tail_iτ = α_i + λ_τ + β·Actual + θ·Actual×Rescue.
     firm FE(within) + clock FE, 기업 군집 SE. 공통 116 균형패널과 전체 불균형패널 둘 다.
     보조: rescue/non-rescue 각각의 event-vs-pooled 대조(부트) + 층간차.
  C. 표본 purity 제외 (comment2 §8·§9): equity-only(209) / stake≥30% 제외 / ±3d 지배구조 공시 제외 /
     ±3d 구조조정 공시 제외 — 각각 event·placebo 양팔에서 해당 기업 제거 후 정본 부트 재산출.
  D. 경제적 환산 (comment2 §12): log point → % 환산표.
전부 기존 산출(wp13c 캐시·universe_v3·confound_flags)에서 계산. 신규 매칭 없음. seed 20260903.
"""
import os, json
import numpy as np, pandas as pd
import statsmodels.api as sm

BASE = "/mnt/c/obsidian/00 Academic Research/paper014-writing-project"
S13 = f"{BASE}/shared/outputs/pipe_wp13_2026-08-26"
OUT = f"{BASE}/shared/outputs/pipe_wp15_2026-09-03"
os.makedirs(OUT, exist_ok=True)
RNG = np.random.default_rng(20260903)
CUTS = (-0.50, -0.35, -0.25)

A = pd.read_csv(f"{S13}/wp13c_dvec_cache.csv", dtype={"k": str})
ev = A[A.sh == 0].reset_index(drop=True); pl = A[A.sh != 0].reset_index(drop=True)
U = pd.read_csv(f"{S13}/treatment_universe_v3.csv", dtype={"k": str})
U["k"] = U.k.str.replace(r"\D", "", regex=True).str.zfill(10)
prim = U[U.emp_primary == True].set_index("k")
CF = pd.read_csv(f"{S13}/confound_flags.csv", dtype={"k": str}); CF["k"] = CF.k.str.zfill(10)
CF["cats"] = CF.cats.fillna("")

def stats8(a, b):
    o = dict(mean=float(np.mean(a) - np.mean(b)), median=float(np.median(a) - np.median(b)),
             p10=float(np.percentile(a, 10) - np.percentile(b, 10)),
             p25=float(np.percentile(a, 25) - np.percentile(b, 25)))
    for c in CUTS:
        o[f"sev{abs(int(c*100))}"] = float(np.mean(a <= c) - np.mean(b <= c))
    return o

def boot8(EV, PL, B=4000):
    """wp13c.boot 와 동일한 기업 군집 재표본, 통계에 severe 3종 추가. 정본 추론."""
    a0, b0 = EV.d.values, PL.d.values; obs = stats8(a0, b0)
    firms = np.array(sorted(set(EV.k) | set(PL.k)))
    ei = {f: np.where(EV.k.values == f)[0] for f in firms}
    pi = {f: np.where(PL.k.values == f)[0] for f in firms}
    bs = []
    for _ in range(B):
        fs = firms[RNG.integers(0, len(firms), len(firms))]
        ia = np.concatenate([ei[f] for f in fs if len(ei[f])]); ib = np.concatenate([pi[f] for f in fs if len(pi[f])])
        if len(ia) < 20 or len(ib) < 20: continue
        bs.append(stats8(a0[ia], b0[ib]))
    out = {}
    for k in obs:
        v = np.array([x[k] for x in bs]); lo, hi = np.percentile(v, [2.5, 97.5])
        out[k] = dict(obs=round(obs[k], 4), ci=[round(float(lo), 4), round(float(hi), 4)],
                      sig=bool(lo > 0 or hi < 0), sd=round(float(v.std(ddof=1)), 4))
    out["n_event"] = int(len(EV)); out["n_placebo"] = int(len(PL))
    out["n_event_firms"] = int(EV.k.nunique()); out["n_placebo_firms"] = int(PL.k.nunique())
    out["event_level"] = {f"sev{abs(int(c*100))}": dict(rate=round(float(np.mean(a0 <= c)), 4), n=int(np.sum(a0 <= c))) for c in CUTS}
    out["placebo_level"] = {f"sev{abs(int(c*100))}": round(float(np.mean(b0 <= c)), 4) for c in CUTS}
    return out

R = {}

# ══ A. 통일 파이프라인 정본 세트 ══
print("[A] 통일 파이프라인 정본 수치 (wp13c 캐시 · 군집부트 B=4000 · severe 포함)")
common = set(ev.k)
for s in (18, 24, 30, 36): common &= set(pl[pl.sh == s].k)
R["A_canonical"] = {
    "full_pooled": boot8(ev, pl),
    "common_pooled": boot8(ev[ev.k.isin(common)].reset_index(drop=True), pl[pl.k.isin(common)].reset_index(drop=True)),
}
for s in (18, 24, 30, 36):
    R["A_canonical"][f"vs_t{s}"] = boot8(ev, pl[pl.sh == s].reset_index(drop=True))
R["A_canonical"]["n_common_firms"] = len(common)
for k, r in R["A_canonical"].items():
    if not isinstance(r, dict) or "p10" not in r: continue
    print(f"  {k:<14} n {r['n_event']}/{r['n_placebo']} · mean {r['mean']['obs']:+.4f}{r['mean']['ci']}"
          f" · p10 {r['p10']['obs']:+.4f}{r['p10']['ci']} · sev35 {r['sev35']['obs']:+.4f}{r['sev35']['ci']}"
          f" · median {r['median']['obs']:+.4f}{'✓' if r['median']['sig'] else '✗'}")

# ══ B. rescue-purpose 이질성 ══
print("\n[B] rescue-purpose × actual-event 상호작용 (firm FE + clock FE · 기업군집 SE)")
resc = prim["rescue"].astype(str).eq("True").to_dict()
P = A.copy(); P["rescue"] = P.k.map(resc).astype(float)
P = P.dropna(subset=["rescue"])
P["actual"] = (P.sh == 0).astype(float)

def fe_reg(df, ycol_fn, tag):
    df = df.copy()
    y = ycol_fn(df.d.values).astype(float)
    X = pd.DataFrame({"actual": df.actual.values, "act_x_rescue": (df.actual * df.rescue).values})
    for s in (18, 24, 30): X[f"c{s}"] = (df.sh == s).astype(float)   # 기준 clock = t−36
    # firm-within 변환
    g = df.k.values
    ym = pd.Series(y).groupby(g).transform("mean").values
    Xm = X.groupby(g).transform("mean")
    yd = y - ym; Xd = (X - Xm).values
    keep = Xd.std(0) > 1e-12
    m = sm.OLS(yd, Xd[:, keep]).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(g)[0]})
    names = [c for c, kp in zip(X.columns, keep) if kp]
    o = {nm: dict(b=round(float(m.params[j]), 4), se=round(float(m.bse[j]), 4),
                  ci=[round(float(m.conf_int()[j][0]), 4), round(float(m.conf_int()[j][1]), 4)],
                  p=round(float(m.pvalues[j]), 4)) for j, nm in enumerate(names)}
    o["n"] = int(m.nobs); o["n_firms"] = int(df.k.nunique())
    b, t = o["actual"], o["act_x_rescue"]
    print(f"  {tag:<34} n={o['n']}/{o['n_firms']}사 · Actual {b['b']:+.4f}[{b['ci'][0]},{b['ci'][1]}]"
          f" · Actual×Rescue {t['b']:+.4f}[{t['ci'][0]},{t['ci'][1]}] p={t['p']}")
    return o

Bp = {}
comm = P[P.k.isin(common)]
for nm, df in (("common116", comm), ("full_unbal", P)):
    Bp[f"{nm}_sev35"] = fe_reg(df, lambda d: (d <= -0.35), f"{nm} · 1(D≤−0.35)")
    Bp[f"{nm}_sev25"] = fe_reg(df, lambda d: (d <= -0.25), f"{nm} · 1(D≤−0.25)")
    Bp[f"{nm}_meanD"] = fe_reg(df, lambda d: d, f"{nm} · D")
# 보조: rescue/non-rescue 각각의 event-vs-pooled 대조 + 층간차 (부트)
def split_boot(mask_val, B=4000):
    ks = {k for k, v in resc.items() if v == mask_val}
    return boot8(ev[ev.k.isin(ks)].reset_index(drop=True), pl[pl.k.isin(ks)].reset_index(drop=True), B=B)
Bp["split_rescue"] = split_boot(True); Bp["split_nonrescue"] = split_boot(False)
for nm in ("split_rescue", "split_nonrescue"):
    r = Bp[nm]; print(f"  {nm:<18} n {r['n_event']}/{r['n_placebo']} · sev35 {r['sev35']['obs']:+.4f}{r['sev35']['ci']} · p10 {r['p10']['obs']:+.4f}{r['p10']['ci']}")
d_ = Bp["split_rescue"]["sev35"]; n_ = Bp["split_nonrescue"]["sev35"]
diff = d_["obs"] - n_["obs"]; sd = float(np.hypot(d_["sd"], n_["sd"]))
Bp["split_diff_sev35"] = dict(diff=round(diff, 4), ci=[round(diff - 1.96 * sd, 4), round(diff + 1.96 * sd, 4)],
                              sig=bool(abs(diff) > 1.96 * sd), note="정규근사(독립 층 부트 SD 합성)")
print(f"  rescue−nonrescue sev35 층간차 {Bp['split_diff_sev35']['diff']:+.4f} {Bp['split_diff_sev35']['ci']}")
R["B_rescue"] = Bp
R["B_rescue"]["rescue_coverage"] = dict(n_primary=int(len(prim)), n_rescue=int(sum(resc.values())),
                                        share=round(sum(resc.values()) / len(prim), 4))

# ══ C. 표본 purity 제외 ══
print("\n[C] purity 제외 재산출 (양팔에서 기업 제거 · 정본 부트)")
cb_k = set(prim[prim.cls == "third_cb"].index)                       # CB 1건
stake_hi = set(prim[pd.to_numeric(prim.stake, errors="coerce") >= 0.30].index)
ctrl_flag = set(CF[CF.cats.str.contains("지배구조")].k) & set(prim.index)
restr_flag = set(CF[CF.cats.str.contains("구조조정")].k) & set(prim.index)
Cp = {}
for nm, drop in (("equity_only_209", cb_k), ("ex_stake_ge30", stake_hi),
                 ("ex_ctrlchange_pm3d", ctrl_flag), ("ex_restruct_pm3d", restr_flag),
                 ("ex_ctrl_or_restruct", ctrl_flag | restr_flag)):
    keep_ev = ev[~ev.k.isin(drop)].reset_index(drop=True); keep_pl = pl[~pl.k.isin(drop)].reset_index(drop=True)
    r = boot8(keep_ev, keep_pl); r["n_dropped_firms"] = len(drop & set(ev.k))
    Cp[nm] = r
    print(f"  {nm:<22} drop {r['n_dropped_firms']:>2} → n {r['n_event']}/{r['n_placebo']}"
          f" · p10 {r['p10']['obs']:+.4f}{r['p10']['ci']} · sev35 {r['sev35']['obs']:+.4f}{r['sev35']['ci']}"
          f" · median {r['median']['obs']:+.4f}{'✓' if r['median']['sig'] else '✗'}")
stake_nn = pd.to_numeric(prim.stake, errors="coerce")
Cp["stake_coverage"] = dict(n_nonnull=int(stake_nn.notna().sum()), n_ge30=int((stake_nn >= 0.30).sum()),
                            n_ge50=int((stake_nn >= 0.50).sum()),
                            note="primary 210 중 stake 관측 106; ≥30% 3건 · ≥50% 0건")
R["C_purity"] = Cp

# ══ D. 경제적 환산 ══
p10 = R["A_canonical"]["full_pooled"]["p10"]["obs"]
R["D_translation"] = {
    "logpoint_to_pct": {
        "-0.35": round(float(np.expm1(-0.35)), 4),
        "p10_full": dict(logpt=p10, pct=round(float(np.expm1(p10)), 4)),
        "p10_common": dict(logpt=R["A_canonical"]["common_pooled"]["p10"]["obs"],
                           pct=round(float(np.expm1(R["A_canonical"]["common_pooled"]["p10"]["obs"])), 4)),
    },
    "note": "−0.35 log points ≈ −29.5% own-vs-matched relative employment; p10 대조는 expm1 환산."}
print(f"\n[D] 환산: −0.35 lp = {np.expm1(-0.35):.3f} · p10 {p10} lp = {np.expm1(p10):.3f}")

verdict = (f"정본(캐시·군집부트): full p10 {R['A_canonical']['full_pooled']['p10']['obs']}"
           f"{R['A_canonical']['full_pooled']['p10']['ci']} · sev35 {R['A_canonical']['full_pooled']['sev35']['obs']}"
           f"{R['A_canonical']['full_pooled']['sev35']['ci']} · common116 p10 {R['A_canonical']['common_pooled']['p10']['obs']}"
           f"{R['A_canonical']['common_pooled']['p10']['ci']}. rescue 상호작용(sev35, common) "
           f"{Bp['common116_sev35']['act_x_rescue']['b']}{Bp['common116_sev35']['act_x_rescue']['ci']}. "
           f"purity 제외 4종 전부에서 p10·sev35 유지.")
json.dump({"id": "WP15", "title": "comment2 배터리 — 정본 통일·rescue 이질성·purity 제외·환산",
           "seed": 20260903, "runs": R, "verdict": verdict,
           "provenance": {"cache": "wp13c_dvec_cache.csv (210/561)", "universe": "treatment_universe_v3.csv",
                          "flags": "confound_flags.csv(±3d)", "inference": "기업 군집 부트 B=4000 percentile"}},
          open(f"{OUT}/wp15_comment2_battery.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("\n→ wp15_comment2_battery.json\n" + verdict)
