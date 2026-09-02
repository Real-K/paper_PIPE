# -*- coding: utf-8 -*-
"""WP14a — 하위창 꼬리 동학 (comment #1: 'financing window' 시간해상도).
outcome 창을 +1..+6 과 +7..+12 로 나눠, 각 창에서 event vs pooled pseudo 의
p10 대조와 severe(≤−0.35) 초과를 재추정한다. 기존 wp13c 파이프라인(매칭·기준창 동일) 재사용.
기준창은 항상 −12..−1. 새 데이터 없음. seed 20260902(신규 스트림)."""
import os, json
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "wp13c_pooled_placebo.py"), encoding="utf-8").read()
i = src.find("SHIFTS=[18,24,30,36]")
ns = {"__name__": "wp14a_reuse"}
exec(compile(src[:src.rfind("\n", 0, i)], "wp13c(head)", "exec"), ns)
np_, pd_ = ns["np"], ns["pd"]
build, T, Xc, crows, LE, mi, sm = ns["build"], ns["T"], ns["Xc"], ns["crows"], ns["LE"], ns["mi"], ns["sm"]
OUT14 = ns["BASE"] + "/shared/outputs/pipe_wp14_2026-09-02"
RNG = np.random.default_rng(20260902)

def dvec_win(Tm, a, b):
    """wp13c.dvec 와 동일하되 outcome 창을 e+a..e+b 로 (기준창 −12..−1 불변)."""
    Xt = np.column_stack([Tm.logsize, Tm.logsize**2, Tm.pregrowth, Tm.cap, Tm.man])
    X = np.vstack([Xt, Xc]); y = np.r_[np.ones(len(Xt)), np.zeros(len(Xc))]
    Xs = (X - X.mean(0)) / X.std(0)
    lgt = sm.Logit(y, sm.add_constant(Xs)).fit(disp=0)
    xb = np.asarray(lgt.predict(sm.add_constant(Xs), linear=True))
    xbt = xb[:len(Xt)]; xbc = xb[len(Xt):]
    lo, hi = xbt.min(), xbt.max(); supp = (xbc >= lo) & (xbc <= hi)
    CSr = crows[supp]; xbcs = xbc[supp]; calp = 0.2 * np.std(xb); K = 50
    o = np.argsort(xbcs); XS = xbcs[o]; CS = CSr[o]
    out = np.full(len(Tm), np.nan)
    for ii, r in enumerate(Tm.itertuples()):
        p = np.searchsorted(XS, xbt[ii]); cand = list(range(max(0, p - K - 2), min(len(XS), p + K + 2)))
        dd = np.abs(XS[cand] - xbt[ii]); sel = np.argsort(dd)[:K]
        m = [CS[cand[s]] for s in sel if dd[s] <= calp]
        if not m: continue
        e = r.e; bc = list(range(e - 12, e)); bt_ = np.nanmean(LE[r.fi, bc])
        if np.sum(np.isfinite(LE[r.fi, bc])) < 6 or not np.isfinite(bt_): continue
        pj = list(range(e + a, e + b + 1)); v = LE[r.fi, pj]
        if np.sum(np.isfinite(v)) < 3: continue
        dc = [np.nanmean(LE[c, pj]) - np.nanmean(LE[c, bc]) for c in m
              if np.isfinite(np.nanmean(LE[c, bc])) and np.sum(np.isfinite(LE[c, pj])) >= 3]
        if len(dc) < 3: continue
        out[ii] = (np.nanmean(v) - bt_) - np.mean(dc)
    return out

def stats2(a, b):
    return dict(p10=float(np.percentile(a, 10) - np.percentile(b, 10)),
                median=float(np.median(a) - np.median(b)),
                sev=float(np.mean(a <= -0.35) - np.mean(b <= -0.35)))

def boot2(EV, PL, B=4000):
    obs = stats2(EV.d.values, PL.d.values)
    firms = np.array(sorted(set(EV.k) | set(PL.k)))
    ei = {f: np.where(EV.k.values == f)[0] for f in firms}; pi = {f: np.where(PL.k.values == f)[0] for f in firms}
    bs = []
    for _ in range(B):
        fs = firms[RNG.integers(0, len(firms), len(firms))]
        ia = np.concatenate([ei[f] for f in fs if len(ei[f])]); ib = np.concatenate([pi[f] for f in fs if len(pi[f])])
        if len(ia) < 20 or len(ib) < 20: continue
        bs.append(stats2(EV.d.values[ia], PL.d.values[ib]))
    out = {}
    for k in obs:
        v = np.array([x[k] for x in bs]); lo, hi = np.percentile(v, [2.5, 97.5])
        out[k] = dict(obs=round(obs[k], 4), ci=[round(float(lo), 4), round(float(hi), 4)], sig=bool(lo > 0 or hi < 0))
    out["n_event"], out["n_placebo"] = int(len(EV)), int(len(PL))
    return out

R = {}
for (a, b), lab in (((1, 6), "m+1..+6"), ((7, 12), "m+7..+12")):
    ev_t = build(0); dv = dvec_win(ev_t, a, b)
    EV = pd.DataFrame({"k": ev_t.k.values, "d": dv}).dropna()
    pls = []
    for s in (18, 24, 30, 36):
        Ts = build(s); Ds = dvec_win(Ts, a, b)
        pls.append(pd.DataFrame({"k": Ts.k.values, "d": Ds, "sh": s}).dropna(subset=["d"]))
    PL = pd.concat(pls, ignore_index=True)
    r = boot2(EV.reset_index(drop=True), PL.reset_index(drop=True))
    r["event_p10"] = round(float(np.percentile(EV.d.values, 10)), 4)
    r["event_sev"] = round(float(np.mean(EV.d.values <= -0.35)), 4)
    R[lab] = r
    print(f"[A] {lab}: n {r['n_event']}/{r['n_placebo']} · p10 diff {r['p10']['obs']:+.4f} {r['p10']['ci']} · "
          f"sev excess {r['sev']['obs']:+.4f} {r['sev']['ci']} · median {r['median']['obs']:+.4f}", flush=True)
json.dump(R, open(f"{OUT14}/wp14a_subwindow.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("→ wp14a_subwindow.json")
