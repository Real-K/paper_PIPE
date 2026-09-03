# -*- coding: utf-8 -*-
"""WP15e — same-state 비교 강화 (comment2 §13 + §5 후반).
  (1) entropy balancing: distressed 층에서 처치 모멘트에 정확 균형 —
      평균(logsize·pg·lev·roa·cash·imp·loss) + 연도 더미 + 2차 모멘트(pg·lev·roa·cash 분산).
      목표: max|SMD| 0.123(ROA) → <0.05. 결과: median/p10/cprob(−0.35) 대조 재산출.
  (2) 가중 재추정 부트: wp12b 는 성향가중을 원표본에서 1회 추정 후 복제 내 고정 —
      여기서는 매 복제(처치 iid × 대조 기업군집)마다 로짓을 재적합해 가중 추정 불확실성 반영.
  EB 부트도 복제마다 EB 를 재해석(re-solve). B=500 · seed 20260903.
wp12b head 재사용(TR/DR 동일 구축). 추정기 불변 — 균형과 추론만 강화.
"""
import os, json, time
import numpy as np, pandas as pd
from scipy.optimize import minimize
from scipy.special import logsumexp

HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "wp12b_stratified_comparator.py"), encoding="utf-8").read()
i = src.find("GRID=np.round")
ns = {"__name__": "wp15e_reuse"}
exec(compile(src[:src.rfind("\n", 0, i)], "wp12b(head)", "exec"), ns)
TR, DR, sm = ns["TR"], ns["DR"], ns["sm"]
BASE = ns["BASE"]; OUT = f"{BASE}/shared/outputs/pipe_wp15_2026-09-03"; os.makedirs(OUT, exist_ok=True)
RNG = np.random.default_rng(20260903); B = 500
CUTS = (-0.50, -0.35, -0.25)
COLS = ["logsize", "pg", "lev", "roa", "cash", "imp", "loss"]
VAR2 = ["pg", "lev", "roa", "cash"]

def prep(A, Bd):
    X = pd.concat([A[COLS + ["yr"]], Bd[COLS + ["yr"]]]).astype(float).reset_index(drop=True)
    for c in ("lev", "roa", "cash"):
        X[c] = X[c].clip(X[c].quantile(.01), X[c].quantile(.99)).fillna(X[c].median())
    yrs = sorted(X.yr.unique())[1:]                    # 기준연도 1개 제외
    for y in yrs: X[f"y{int(y)}"] = (X.yr == y).astype(float)
    X = X.drop(columns=["yr"])
    for c in VAR2: X[f"{c}_sq"] = X[c] ** 2
    X = X.loc[:, X.std() > 1e-9]
    Z = ((X - X.mean()) / X.std())
    return X, Z

def eb_solve(Ct):
    """dual: min logsumexp(Ct·λ) — Ct 는 (대조 행 × 제약), 처치 모멘트 중심화 완료."""
    lam0 = np.zeros(Ct.shape[1])
    def f(l): return logsumexp(Ct @ l)
    def g(l):
        u = Ct @ l; w = np.exp(u - logsumexp(u)); return Ct.T @ w
    r = minimize(f, lam0, jac=g, method="BFGS", options=dict(maxiter=500, gtol=1e-8))
    u = Ct @ r.x; w = np.exp(u - logsumexp(u))
    return w, bool(r.success or np.max(np.abs(g(r.x))) < 1e-5)

def fast_logit(X, y, ridge=1e-8, maxit=40):
    """Newton MLE 로짓 (numpy). 발산·분리 시 ridge=1.0 재적합 (wp12b 의 L2 fallback 과 동일 취지).
    statsmodels 대비 수십 배 빠름 — 복제마다 재적합하는 부트에 필요."""
    def newton(lam):
        b = np.zeros(X.shape[1])
        for _ in range(maxit):
            xb = X @ b; mu = 1 / (1 + np.exp(-np.clip(xb, -35, 35)))
            g = X.T @ (y - mu) - lam * b
            Wd = mu * (1 - mu)
            H = (X * Wd[:, None]).T @ X + (lam + 1e-10) * np.eye(X.shape[1])
            step = np.linalg.solve(H, g)
            b = b + step
            if not np.all(np.isfinite(b)) or np.max(np.abs(b)) > 60: return None
            if np.max(np.abs(step)) < 1e-8: return b
        return b if np.max(np.abs(g)) < 1e-3 else None
    b = newton(ridge)
    if b is None:
        b = newton(1.0)
        return 1 / (1 + np.exp(-np.clip(X @ b, -35, 35))), False
    return 1 / (1 + np.exp(-np.clip(X @ b, -35, 35))), True

def wq(x, w, q):
    o = np.argsort(x); cw = np.cumsum(w[o]); return float(x[o][np.searchsorted(cw, q * cw[-1])])
def stats_w(da, db, w):
    o = dict(mean=float(np.mean(da) - np.average(db, weights=w)),
             median=float(np.median(da) - wq(db, w, .5)), p10=float(np.percentile(da, 10) - wq(db, w, .10)))
    for c in CUTS:
        o[f"cprob{abs(int(c*100))}"] = float(np.mean(da <= c) - np.average((db <= c).astype(float), weights=w))
    return o
def smd_vec(Zt, Zc, w):
    out = []
    for j in range(Zt.shape[1]):
        mt, mc = Zt[:, j].mean(), np.average(Zc[:, j], weights=w)
        sd = np.sqrt((Zt[:, j].var() + np.average((Zc[:, j] - mc) ** 2, weights=w)) / 2 + 1e-12)
        out.append((mt - mc) / sd)
    return np.array(out)

def run_stratum(A, Bd, tag, mode):
    """mode='eb' (entropy balancing, 복제마다 re-solve) 또는 'ps' (성향가중, 복제마다 재적합)."""
    A = A.reset_index(drop=True); Bd = Bd.reset_index(drop=True)
    X, Z = prep(A, Bd)
    Zt, Zc = Z.values[:len(A)], Z.values[len(A):]
    names = list(X.columns)
    def weights_of(ia, ib):
        if mode == "eb":
            Ct = Zc[ib] - Zt[ia].mean(0)
            w, ok = eb_solve(Ct); return w, ok
        Xs = np.vstack([Zt[ia], Zc[ib]]); y = np.r_[np.ones(len(ia)), np.zeros(len(ib))]
        Xc_ = np.column_stack([np.ones(len(Xs)), Xs])
        ps, ok = fast_logit(Xc_, y)
        ps = np.clip(ps, 1e-6, 1 - 1e-6); w = ps[len(ia):] / (1 - ps[len(ia):])
        w = np.clip(w, 0, np.percentile(w, 99)); return w / w.sum(), ok
    ia0, ib0 = np.arange(len(A)), np.arange(len(Bd))
    w0, ok0 = weights_of(ia0, ib0)
    da, db = A.D.values, Bd.D.values
    obs = stats_w(da, db, w0)
    sm0 = smd_vec(Zt, Zc, w0)
    firms = Bd.bn.values; uf = np.unique(firms); byf = {f: np.where(firms == f)[0] for f in uf}
    bs = []; t0 = time.time(); nbad = 0
    for rep in range(B):
        ia = RNG.integers(0, len(da), len(da))
        ib = np.concatenate([byf[uf[j]] for j in RNG.integers(0, len(uf), len(uf))])
        try:
            wb, okb = weights_of(ia, ib)
        except Exception:
            nbad += 1; continue
        bs.append(stats_w(da[ia], db[ib], wb))
        if (rep + 1) % 100 == 0: print(f"    [{tag}/{mode}] {rep+1}/{B} ({(time.time()-t0)/60:.1f}분)", flush=True)
    r = {}
    for k in obs:
        v = np.array([x[k] for x in bs]); lo, hi = np.percentile(v, [2.5, 97.5])
        r[k] = dict(obs=round(obs[k], 4), ci=[round(float(lo), 4), round(float(hi), 4)],
                    sig=bool(lo > 0 or hi < 0), sd=round(float(v.std(ddof=1)), 4))
    r["n_treated"] = int(len(A)); r["n_ctrl_events"] = int(len(Bd)); r["n_ctrl_firms"] = int(Bd.bn.nunique())
    r["ess"] = round(float(1 / np.sum(w0 ** 2)), 1); r["solver_ok"] = bool(ok0); r["n_boot_used"] = len(bs); r["n_boot_fail"] = nbad
    r["max_abs_smd"] = round(float(np.max(np.abs(sm0))), 4)
    r["smd_by_constraint"] = {nm: round(float(s), 4) for nm, s in zip(names, sm0)}
    r["treated_level"] = {f"cprob{abs(int(c*100))}": round(float(np.mean(da <= c)), 4) for c in CUTS}
    r["ctrl_level_w"] = {f"cprob{abs(int(c*100))}": round(float(np.average((db <= c).astype(float), weights=w0)), 4) for c in CUTS}
    print(f"  {tag:<14} {mode:<3} T={len(A)} C={len(Bd)} ESS={r['ess']:.0f} maxSMD={r['max_abs_smd']:.4f} · "
          f"median {r['median']['obs']:+.4f}{r['median']['ci']} · p10 {r['p10']['obs']:+.4f}{r['p10']['ci']} · "
          f"cprob35 {r['cprob35']['obs']:+.4f}{r['cprob35']['ci']}", flush=True)
    return r

R = {}
D1t, D1c = TR[TR.distress == 1], DR[DR.distress == 1]
D0t, D0c = TR[TR.distress == 0], DR[DR.distress == 0]
print(f"[층] distressed T={len(D1t)} C={len(D1c)} · non T={len(D0t)} C={len(D0c)}", flush=True)
print("\n[1] entropy balancing (평균+연도+분산 제약 · 복제마다 re-solve)")
R["eb_distress_1"] = run_stratum(D1t, D1c, "distressed", "eb")
R["eb_distress_0"] = run_stratum(D0t, D0c, "non-distressed", "eb")
print("\n[2] 성향가중 — 복제마다 재적합 (wp12b 고정가중과 대비)")
R["ps_reest_distress_1"] = run_stratum(D1t, D1c, "distressed", "ps")
R["ps_reest_distress_0"] = run_stratum(D0t, D0c, "non-distressed", "ps")

def pool(k1, k0):
    rs = [R[k1], R[k0]]; nv = np.array([r["n_treated"] for r in rs]); w = nv / nv.sum()
    out = {}
    for s in ("mean", "median", "p10", "cprob35"):
        est = float(np.sum(w * np.array([r[s]["obs"] for r in rs])))
        sd = float(np.sqrt(np.sum((w * np.array([r[s]["sd"] for r in rs])) ** 2)))
        out[s] = dict(obs=round(est, 4), ci=[round(est - 1.96 * sd, 4), round(est + 1.96 * sd, 4)], sig=bool(abs(est) > 1.96 * sd))
    out["n_treated"] = int(nv.sum()); out["note"] = "처치 층 크기 가중 · 정규근사"
    return out
R["eb_pool"] = pool("eb_distress_1", "eb_distress_0")
R["ps_reest_pool"] = pool("ps_reest_distress_1", "ps_reest_distress_0")
for k in ("eb_pool", "ps_reest_pool"):
    p = R[k]; print(f"  {k:<14} median {p['median']['obs']:+.4f}{p['median']['ci']} · p10 {p['p10']['obs']:+.4f}{p['p10']['ci']} · cprob35 {p['cprob35']['obs']:+.4f}{p['cprob35']['ci']}", flush=True)

# wp12b 원 결과와 대비 (참조 등재)
W12 = json.load(open(f"{BASE}/shared/outputs/pipe_wp12_2026-08-26/wp12b.json"))["runs"]
R["ref_wp12b_distress_1"] = {k: W12["B_distress_1"][k] for k in ("median", "p10", "max_abs_smd", "ess")}
verdict = (f"EB(distressed): maxSMD {R['eb_distress_1']['max_abs_smd']} (wp12b 0.123 → 목표<0.05) · "
           f"median {R['eb_distress_1']['median']['obs']}{R['eb_distress_1']['median']['ci']} · "
           f"p10 {R['eb_distress_1']['p10']['obs']}{R['eb_distress_1']['p10']['ci']} · "
           f"cprob35 {R['eb_distress_1']['cprob35']['obs']}{R['eb_distress_1']['cprob35']['ci']}. "
           f"가중 재추정 부트(distressed) p10 {R['ps_reest_distress_1']['p10']['obs']}{R['ps_reest_distress_1']['p10']['ci']}.")
json.dump({"id": "WP15e", "title": "same-state EB(평균+연도+분산) + 가중 재추정 부트", "seed": 20260903, "B": B,
           "runs": R, "verdict": verdict,
           "design": "wp12b TR/DR 동일 구축. EB 제약: COLS 평균 + 연도더미 + pg·lev·roa·cash 2차모멘트. 부트: 처치 iid × 대조 기업군집, 복제마다 가중 재해석. PS 재적합은 Newton MLE(발산 시 ridge=1.0) — wp12b 추정과 동일 취지, 고속 구현."},
          open(f"{OUT}/wp15e_samestate_eb.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("\n=== WP15e ===\n" + verdict)
