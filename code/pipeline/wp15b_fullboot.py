# -*- coding: utf-8 -*-
"""WP15b — full-design bootstrap (comment2 §5): 매 복제마다
  (i) 수령기업을 기업 단위로 재표본, (ii) 비교기업 풀을 기업 단위로 **별도** 재표본,
  (iii) 성향점수 로짓·공통지지·캘리퍼·K=50 매칭을 **재추정/재실행**,
  (iv) actual/pseudo d 벡터와 mean/median/p10/p25/severe(−0.25/−0.35/−0.50)·11-cutoff 곡선을 재계산.
기존 군집부트(wp13c)가 반영 못 하던 매칭 불확실성·대조 재사용·가중(성향) 추정 불확실성을
하나의 재표본 체계에 넣는다. wp13c 기계(head 재사용) 그대로 — 추정기는 불변, 추론만 확장.
검증: 재구현 dvec_fast(원표본) ≡ wp13c 캐시 (전 이벤트 일치 확인 후 진행).
B=1000 · seed 20260903.
"""
import os, json, time
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "wp13c_pooled_placebo.py"), encoding="utf-8").read()
i = src.find("SHIFTS=[18,24,30,36]")
ns = {"__name__": "wp15b_reuse"}
exec(compile(src[:src.rfind("\n", 0, i)], "wp13c(head)", "exec"), ns)
build, T, Xc, crows, LE, sm = ns["build"], ns["T"], ns["Xc"], ns["crows"], ns["LE"], ns["sm"]
BASE = ns["BASE"]; S13 = f"{BASE}/shared/outputs/pipe_wp13_2026-08-26"
OUT = f"{BASE}/shared/outputs/pipe_wp15_2026-09-03"; os.makedirs(OUT, exist_ok=True)
RNG = np.random.default_rng(20260903)
B = 1000; K = 50; CUTS = (-0.50, -0.35, -0.25)
GRID = [round(-0.60 + 0.05 * j, 2) for j in range(11)]

SHIFTS = [0, 18, 24, 30, 36]
ARM = {s: build(s).reset_index(drop=True) for s in SHIFTS}
print("arm sizes:", {s: len(a) for s, a in ARM.items()}, flush=True)

# ── 사전계산 1: 처치 own delta (복제 불변) ──
for s, Tm in ARM.items():
    own = np.full(len(Tm), np.nan)
    for ii, r in enumerate(Tm.itertuples()):
        e = r.e; bc = LE[r.fi, e - 12:e]
        if np.sum(np.isfinite(bc)) < 6: continue
        bt_ = np.nanmean(bc)
        if not np.isfinite(bt_): continue
        v = LE[r.fi, e + 7:e + 13]
        if np.sum(np.isfinite(v)) < 3: continue
        own[ii] = np.nanmean(v) - bt_
    Tm["own"] = own

# ── 사전계산 2: 대조 풀의 e별 delta (복제 불변) ──
NC = len(crows)
all_e = sorted({int(e) for Tm in ARM.values() for e in Tm.e})
DC = {}
LEc = LE[crows]                                   # (NC, NM)
for e in all_e:
    bcm = LEc[:, e - 12:e]; pjm = LEc[:, e + 7:e + 13]
    base = np.nanmean(bcm, axis=1)
    okp_ = np.sum(np.isfinite(pjm), axis=1) >= 3
    val = np.where(np.isfinite(base) & okp_, np.nanmean(pjm, axis=1) - base, np.nan)
    DC[e] = val
print(f"대조 풀 {NC} · 사전계산 e {len(all_e)}", flush=True)

def dvec_fast(Tm, cidx):
    """wp13c.dvec 재구현: cidx = 대조 풀 행 인덱스(부트에서는 중복 허용)."""
    Xt = np.column_stack([Tm.logsize, Tm.logsize ** 2, Tm.pregrowth, Tm.cap, Tm.man])
    Xcb = Xc[cidx]
    X = np.vstack([Xt, Xcb]); y = np.r_[np.ones(len(Xt)), np.zeros(len(Xcb))]
    Xs = (X - X.mean(0)) / X.std(0)
    lgt = sm.Logit(y, sm.add_constant(Xs)).fit(disp=0)
    xb = np.asarray(lgt.predict(sm.add_constant(Xs), linear=True))
    xbt = xb[:len(Xt)]; xbc = xb[len(Xt):]
    lo, hi = xbt.min(), xbt.max(); supp = (xbc >= lo) & (xbc <= hi)
    pool_rows = cidx[supp]; xbcs = xbc[supp]; calp = 0.2 * np.std(xb)
    o = np.argsort(xbcs); XS = xbcs[o]; CS = pool_rows[o]
    out = np.full(len(Tm), np.nan)
    ownv = Tm.own.values; ev_ = Tm.e.values.astype(int)
    for ii in range(len(Tm)):
        if not np.isfinite(ownv[ii]): continue
        p = np.searchsorted(XS, xbt[ii]); c0, c1 = max(0, p - K - 2), min(len(XS), p + K + 2)
        dd = np.abs(XS[c0:c1] - xbt[ii]); sel = np.argsort(dd)[:K]
        m = CS[c0:c1][sel][dd[sel] <= calp]
        if m.size == 0: continue
        dc = DC[ev_[ii]][m]; dc = dc[np.isfinite(dc)]
        if dc.size < 3: continue
        out[ii] = ownv[ii] - dc.mean()
    return out

def stats8(a, b):
    o = dict(mean=float(np.mean(a) - np.mean(b)), median=float(np.median(a) - np.median(b)),
             p10=float(np.percentile(a, 10) - np.percentile(b, 10)),
             p25=float(np.percentile(a, 25) - np.percentile(b, 25)))
    for c in CUTS: o[f"sev{abs(int(c * 100))}"] = float(np.mean(a <= c) - np.mean(b <= c))
    return o

# ── 검증: 원표본 재구현 ≡ wp13c 캐시 ──
cache = pd.read_csv(f"{S13}/wp13c_dvec_cache.csv", dtype={"k": str})
full_idx = np.arange(NC)
obs_d = {}
for s in SHIFTS:
    d = dvec_fast(ARM[s], full_idx)
    df = pd.DataFrame({"k": ARM[s].k.values, "d2": d}).dropna()
    ref = cache[cache.sh == s][["k", "d"]]
    mg = ref.merge(df, on="k", how="outer")
    assert len(mg) == len(ref) == len(df), f"sh={s} 표본 불일치 {len(ref)} vs {len(df)}"
    mad = float(np.max(np.abs(mg.d - mg.d2)))
    assert mad < 1e-10, f"sh={s} d 불일치 max {mad}"
    obs_d[s] = df
print("검증 통과: dvec_fast(원표본) ≡ wp13c 캐시 (5팔 전부, max|Δ|<1e-10)", flush=True)

a0 = obs_d[0].d2.values; b0 = np.concatenate([obs_d[s].d2.values for s in (18, 24, 30, 36)])
obs = stats8(a0, b0); obs_curve = [float(np.mean(a0 <= c) - np.mean(b0 <= c)) for c in GRID]

# ── full-design bootstrap ──
tf = T.k.values                                    # 처치 기업 210 (고정 1차표본)
arm_by_firm = {s: {k: np.where(ARM[s].k.values == k)[0] for k in set(ARM[s].k)} for s in SHIFTS}
t0 = time.time(); bs = []; bcurve = []; nfail = 0
for rep in range(B):
    fs = tf[RNG.integers(0, len(tf), len(tf))]
    cs = RNG.integers(0, NC, NC)
    dd = {}
    ok = True
    for s in SHIFTS:
        rows = np.concatenate([arm_by_firm[s][k] for k in fs if k in arm_by_firm[s]]) if any(k in arm_by_firm[s] for k in fs) else np.array([], int)
        if len(rows) < 20: ok = False; break
        d = dvec_fast(ARM[s].iloc[rows].reset_index(drop=True), cs)
        d = d[np.isfinite(d)]
        if len(d) < 20: ok = False; break
        dd[s] = d
    if not ok: nfail += 1; continue
    a = dd[0]; b = np.concatenate([dd[s] for s in (18, 24, 30, 36)])
    bs.append(stats8(a, b))
    bcurve.append([float(np.mean(a <= c) - np.mean(b <= c)) for c in GRID])
    if (rep + 1) % 100 == 0:
        el = time.time() - t0
        print(f"  [{rep+1}/{B}] {el/60:.1f}분 경과 (평균 {el/(rep+1):.2f}s/rep)", flush=True)

R = {"obs": {k: round(v, 4) for k, v in obs.items()}, "B": B, "n_used": len(bs), "n_fail": nfail}
for k in obs:
    v = np.array([x[k] for x in bs]); lo, hi = np.percentile(v, [2.5, 97.5])
    R[k] = dict(obs=round(obs[k], 4), ci=[round(float(lo), 4), round(float(hi), 4)],
                sig=bool(lo > 0 or hi < 0), sd=round(float(v.std(ddof=1)), 4))
bcv = np.array(bcurve); se = bcv.std(0, ddof=1); se[se == 0] = 1e-9
tmax = float(np.percentile(np.abs((bcv - bcv.mean(0)) / se).max(1), 95))
cd = np.array(obs_curve)
R["curve"] = dict(grid=GRID, diff=[round(float(x), 4) for x in cd],
                  lo_ptw=[round(float(np.percentile(bcv[:, j], 2.5)), 4) for j in range(len(GRID))],
                  hi_ptw=[round(float(np.percentile(bcv[:, j], 97.5)), 4) for j in range(len(GRID))],
                  lo_unif=[round(float(cd[j] - tmax * se[j]), 4) for j in range(len(GRID))],
                  hi_unif=[round(float(cd[j] + tmax * se[j]), 4) for j in range(len(GRID))],
                  tmax=round(tmax, 3),
                  n_pos_lower_unif=int(np.sum(cd - tmax * se > 0)))
# wp13c 정본(캐시·군집부트) 대비 비교표
comp = json.load(open(f"{OUT}/wp15_comment2_battery.json"))["runs"]["A_canonical"]["full_pooled"]
R["vs_cache_cluster"] = {k: dict(fullboot_ci=R[k]["ci"], cache_cluster_ci=comp[k]["ci"]) for k in ("mean", "median", "p10", "p25", "sev35")}
verdict = (f"full-design 부트(B={len(bs)}): p10 {R['p10']['obs']}{R['p10']['ci']}"
           f"{'유의' if R['p10']['sig'] else '비유의'} · sev35 {R['sev35']['obs']}{R['sev35']['ci']}"
           f"{'유의' if R['sev35']['sig'] else '비유의'} · median {R['median']['obs']}{R['median']['ci']}. "
           f"곡선 균일하한>0 {R['curve']['n_pos_lower_unif']}/11. "
           f"(캐시 군집부트 대비 CI 변화는 vs_cache_cluster 참조)")
json.dump({"id": "WP15b", "title": "full-design bootstrap — 양측 기업 재표본 + 매칭·성향 재추정",
           "seed": 20260903, "B": B, "runs": R, "verdict": verdict,
           "design": "매 복제: 처치 210 기업 재표본 × 대조 풀 기업 재표본 → 팔별 로짓 재적합·공통지지·캘리퍼(0.2σ)·K50 재매칭 → d 재계산 → 통계. 추정기는 wp13c 와 동일, 추론만 확장.",
           "note": "검증: 재구현이 원표본에서 wp13c 캐시와 전 이벤트 일치(max|Δ|<1e-10)."},
          open(f"{OUT}/wp15b_fullboot.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("\n=== WP15b ===\n" + verdict)
