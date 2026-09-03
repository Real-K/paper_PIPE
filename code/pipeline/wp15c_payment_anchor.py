# -*- coding: utf-8 -*-
"""WP15c — payment-date anchor (comment2 §10).
이벤트 월을 이사회 결의공시월 대신 **납입(payment)월**로 재정의해 정본 대조를 재산출.
"disclosure 를 연구하는 것 아니냐"는 공격을 닫는 검사. 납입일은 1차표본 210 중 123건에서 관측
(funding_dates.csv). 공정 비교를 위해 같은 123 기업에서 (a) 납입월 anchor, (b) 공시월 anchor 를
동일 기계(wp13c build/dvec 재사용)로 나란히 산출한다. 부트 B=4000 · seed 20260903.
"""
import os, json
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "wp13c_pooled_placebo.py"), encoding="utf-8").read()
i = src.find("SHIFTS=[18,24,30,36]")
ns = {"__name__": "wp15c_reuse"}
exec(compile(src[:src.rfind("\n", 0, i)], "wp13c(head)", "exec"), ns)
BASE = ns["BASE"]; S13 = f"{BASE}/shared/outputs/pipe_wp13_2026-08-26"
OUT = f"{BASE}/shared/outputs/pipe_wp15_2026-09-03"; os.makedirs(OUT, exist_ok=True)
pd_ = ns["pd"]; np_ = ns["np"]
RNG = np.random.default_rng(20260903)
CUTS = (-0.50, -0.35, -0.25); SHIFTS = [18, 24, 30, 36]

F = pd.read_csv(f"{S13}/funding_dates.csv", dtype=str)
F["k"] = F.k.str.replace(r"\D", "", regex=True).str.zfill(10)
F = F.dropna(subset=["funding"])
fund_m = {r.k: pd.Period(pd.to_datetime(r.funding), freq="M") for r in F.itertuples()}

T0 = ns["T"].copy()                                   # 공시월 anchor · 1차표본 210
sub = T0[T0.k.isin(fund_m)].copy()
same_month = int(sum(1 for r in sub.itertuples() if fund_m[r.k] == r.ev))
lag = pd.to_numeric(F[F.k.isin(set(sub.k))].lag_days, errors="coerce")
print(f"납입일 보유 {len(sub)}/210 · 공시월=납입월 {same_month} ({same_month/len(sub):.0%}) · lag median {lag.median():.0f}d IQR [{lag.quantile(.25):.0f},{lag.quantile(.75):.0f}]", flush=True)

def run_anchor(Tsub, tag):
    ns["T"] = Tsub                                    # build() 는 ns 전역 T 를 읽는다
    arms = {}
    for s in [0] + SHIFTS:
        Tm = ns["build"](s)
        d = ns["dvec"](Tm)
        arms[s] = pd.DataFrame({"k": Tm.k.values, "d": d}).dropna().reset_index(drop=True)
    print(f"  [{tag}] arm n = " + " · ".join(f"t−{s}:{len(arms[s])}" if s else f"actual:{len(arms[s])}" for s in [0] + SHIFTS), flush=True)
    return arms

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
        if len(ia) < 15 or len(ib) < 15: continue
        bs.append(stats8(a0[ia], b0[ib]))
    out = {}
    for k in obs:
        v = np.array([x[k] for x in bs]); lo, hi = np.percentile(v, [2.5, 97.5])
        out[k] = dict(obs=round(obs[k], 4), ci=[round(float(lo), 4), round(float(hi), 4)],
                      sig=bool(lo > 0 or hi < 0), sd=round(float(v.std(ddof=1)), 4))
    out["n_event"] = int(len(EV)); out["n_placebo"] = int(len(PL))
    return out

R = {"coverage": dict(n_primary=210, n_with_payment=len(sub), same_month=same_month,
                      same_month_share=round(same_month / len(sub), 4),
                      lag_median_days=float(lag.median()), lag_iqr=[float(lag.quantile(.25)), float(lag.quantile(.75))])}

# (b) 공시월 anchor — 동일 123 기업
Ta = sub.copy()
arms_a = run_anchor(Ta, "announcement · 123")
R["announce_123"] = boot8(arms_a[0], pd.concat([arms_a[s] for s in SHIFTS], ignore_index=True))
# (a) 납입월 anchor
Tp = sub.copy(); Tp["ev"] = Tp.k.map(fund_m)
arms_p = run_anchor(Tp, "payment · 123")
R["payment_123"] = boot8(arms_p[0], pd.concat([arms_p[s] for s in SHIFTS], ignore_index=True))

for nm in ("announce_123", "payment_123"):
    r = R[nm]
    print(f"  {nm:<14} n {r['n_event']}/{r['n_placebo']} · mean {r['mean']['obs']:+.4f}{r['mean']['ci']}"
          f" · p10 {r['p10']['obs']:+.4f}{r['p10']['ci']} · sev35 {r['sev35']['obs']:+.4f}{r['sev35']['ci']}"
          f" · median {r['median']['obs']:+.4f}", flush=True)

verdict = (f"납입월 anchor(123): p10 {R['payment_123']['p10']['obs']}{R['payment_123']['p10']['ci']} · "
           f"sev35 {R['payment_123']['sev35']['obs']}{R['payment_123']['sev35']['ci']} — "
           f"같은 123 기업의 공시월 anchor p10 {R['announce_123']['p10']['obs']}{R['announce_123']['p10']['ci']} · "
           f"sev35 {R['announce_123']['sev35']['obs']}{R['announce_123']['sev35']['ci']}. "
           f"공시월=납입월 {R['coverage']['same_month_share']:.0%}.")
json.dump({"id": "WP15c", "title": "payment-date anchor 재산출 (같은 123 기업 나란히)", "seed": 20260903,
           "runs": R, "verdict": verdict,
           "design": "wp13c build/dvec 재사용; anchor 만 교체. placebo 시점도 anchor 기준 t−18/24/30/36."},
          open(f"{OUT}/wp15c_payment.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("\n=== WP15c ===\n" + verdict)
