# -*- coding: utf-8 -*-
"""WP14 — FRL comment 배터리 (2026-09-02, 10_submission/comment.md 처분).
  A. 하위창 꼬리 동학: outcome 창을 +1..+6 / +7..+12 로 나눠 event-vs-pooled p10·severe 초과를 재추정
     ("financing window" 시간해상도 보강 — 새 데이터 없이 기존 월별 NPS).
  B. threshold grid 벤치마크 확장: 기존 t−36 단독 → pooled·t−18 에서도 sup-t 균일밴드 + max-t.
  C. leave-one-out / 하위 관측 영향도: 하위 1..15개 제거 시 p10·severe·event−pseudo 변화.
  D. 표본선택: window-feasible 260 중 primary 210 vs 제외 50 — 연도·stake·목적·재무상태 비교.
전부 기존 산출(캐시·우주 파일)에서 계산; 신규 매칭 없음(A 제외 — A 는 wp13c 파이프라인 재사용).
"""
import os, json, re
import numpy as np, pandas as pd
from scipy import stats as sps

BASE = os.environ.get("P016_BASE", "/path/to/project-root")
S13 = f"{BASE}/shared/outputs/pipe_wp13_2026-08-26"
OUT14 = f"{BASE}/shared/outputs/pipe_wp14_2026-09-02"
os.makedirs(OUT14, exist_ok=True)
RNG = np.random.default_rng(20260902)
HERE = os.path.dirname(os.path.abspath(__file__))
GRID = [round(-0.60 + 0.05 * i, 2) for i in range(11)]

def stats4(a, b):
    return dict(mean=float(np.mean(a) - np.mean(b)), median=float(np.median(a) - np.median(b)),
                p10=float(np.percentile(a, 10) - np.percentile(b, 10)),
                p25=float(np.percentile(a, 25) - np.percentile(b, 25)))

def boot_cluster(EV, PL, B=4000, extra=None):
    a0, b0 = EV.d.values, PL.d.values; obs = stats4(a0, b0)
    if extra: obs.update(extra(a0, b0))
    firms = np.array(sorted(set(EV.k) | set(PL.k)))
    ei = {f: EV.index[EV.k == f].to_numpy() for f in firms}; pi = {f: PL.index[PL.k == f].to_numpy() for f in firms}
    bs = []
    for _ in range(B):
        fs = firms[RNG.integers(0, len(firms), len(firms))]
        ia = np.concatenate([ei[f] for f in fs if len(ei[f])]); ib = np.concatenate([pi[f] for f in fs if len(pi[f])])
        if len(ia) < 20 or len(ib) < 20: continue
        s = stats4(a0[EV.index.get_indexer(ia)], b0[PL.index.get_indexer(ib)])
        if extra: s.update(extra(a0[EV.index.get_indexer(ia)], b0[PL.index.get_indexer(ib)]))
        bs.append(s)
    out = {}
    for k in bs[0]:
        v = np.array([x[k] for x in bs]); lo, hi = np.percentile(v, [2.5, 97.5])
        out[k] = dict(obs=round(obs[k], 4), ci=[round(float(lo), 4), round(float(hi), 4)],
                      sig=bool(lo > 0 or hi < 0), sd=round(float(v.std(ddof=1)), 4))
    out["n_event"] = int(len(EV)); out["n_placebo"] = int(len(PL))
    return out

R = {}

# ══ B·C: 캐시 기반 ══
A = pd.read_csv(f"{S13}/wp13c_dvec_cache.csv", dtype={"k": str})
ev = A[A.sh == 0].reset_index(drop=True); pl = A[A.sh != 0].reset_index(drop=True)
print(f"[캐시] event {len(ev)} · pooled placebo {len(pl)}")

def curve_band(EV, PL, tag, B=4000):
    a0, b0 = EV.d.values, PL.d.values
    cd = np.array([np.mean(a0 <= c) - np.mean(b0 <= c) for c in GRID])
    t0 = stats4(a0, b0)
    firms = np.array(sorted(set(EV.k) | set(PL.k)))
    ei = {f: np.where(EV.k.values == f)[0] for f in firms}; pi = {f: np.where(PL.k.values == f)[0] for f in firms}
    bcv, bst = [], []
    for _ in range(B):
        fs = firms[RNG.integers(0, len(firms), len(firms))]
        ia = np.concatenate([ei[f] for f in fs if len(ei[f])]); ib = np.concatenate([pi[f] for f in fs if len(pi[f])])
        if len(ia) < 20 or len(ib) < 20: continue
        aa, bb = a0[ia], b0[ib]
        bcv.append([np.mean(aa <= c) - np.mean(bb <= c) for c in GRID])
        bst.append(stats4(aa, bb))
    bcv = np.array(bcv); se = bcv.std(0, ddof=1); se[se == 0] = 1e-9
    tmax = float(np.percentile(np.abs((bcv - bcv.mean(0)) / se).max(1), 95))
    lo = cd - tmax * se; hi = cd + tmax * se
    # max-t: 4개 요약통계 결합 조정 p
    keys = ["mean", "p10", "p25", "median"]
    M = np.array([[x[k] for k in keys] for x in bst]); sse = M.std(0, ddof=1); sse[sse == 0] = 1e-9
    tobs = np.array([t0[k] for k in keys]) / sse
    tnull = np.abs((M - M.mean(0)) / sse).max(1)
    adjp = {k: round(float((np.sum(tnull >= abs(tobs[j])) + 1) / (len(tnull) + 1)), 4) for j, k in enumerate(keys)}
    r = dict(grid=GRID, diff=[round(float(x), 4) for x in cd],
             lo_unif=[round(float(x), 4) for x in lo], hi_unif=[round(float(x), 4) for x in hi],
             all_positive=bool((cd > 0).all()), band_above_zero=bool((lo > 0).all()),
             n_pos_lower=int((lo > 0).sum()), tmax=round(tmax, 3), maxt_adj_p=adjp,
             at_035=dict(diff=round(float(cd[GRID.index(-0.35)]), 4),
                         band=[round(float(lo[GRID.index(-0.35)]), 4), round(float(hi[GRID.index(-0.35)]), 4)]),
             n_event=len(EV), n_bench=len(PL))
    print(f"  [B] {tag:<18} 11/11 양수 {r['all_positive']} · 균일하한>0 {r['n_pos_lower']}/11 · c=−0.35 {r['at_035']['diff']:+.3f} {r['at_035']['band']} · max-t p10 p {adjp['p10']}")
    return r

R["B_grid"] = {"vs_pooled": curve_band(ev, pl, "vs pooled(561)"),
               "vs_t18": curve_band(ev, pl[pl.sh == 18].reset_index(drop=True), "vs t−18"),
               "vs_t24": curve_band(ev, pl[pl.sh == 24].reset_index(drop=True), "vs t−24"),
               "vs_t36_replic": curve_band(ev, pl[pl.sh == 36].reset_index(drop=True), "vs t−36(재현)")}

# ── C: LOO / 하위 관측 영향도 ──
d0 = np.sort(ev.d.values); n = len(d0)
sev0 = float(np.mean(ev.d.values <= -0.35)); p100 = float(np.percentile(ev.d.values, 10))
pooled0 = stats4(ev.d.values, pl.d.values)
loo = []
for m in range(1, 16):
    dm = d0[m:]                       # 하위 m개 제거
    loo.append(dict(m=m, p10=round(float(np.percentile(dm, 10)), 4),
                    sev=round(float(np.mean(dm <= -0.35)), 4),
                    p10_diff=round(float(np.percentile(dm, 10) - np.percentile(pl.d.values, 10)), 4),
                    sev_excess=round(float(np.mean(dm <= -0.35) - np.mean(pl.d.values <= -0.35)), 4)))
single = []
for j in range(15):                   # 하위 15개 각각 단독 제거
    dm = np.delete(d0, j)
    single.append(round(float(np.percentile(dm, 10) - np.percentile(pl.d.values, 10)), 4))
R["C_influence"] = dict(
    n=n, n_severe_035=int(np.sum(ev.d.values <= -0.35)), severe_rate=round(sev0, 4),
    p10_event=round(p100, 4), p10_diff_full=round(pooled0["p10"], 4),
    drop_bottom_cum=loo, drop_single_bottom15_p10diff=single,
    note="하위 m개 누적 제거(최악 관측 우선). 단독 제거 15개는 p10 event−pooled 차이.")
print(f"  [C] severe(≤−0.35) {R['C_influence']['n_severe_035']}/{n} · p10 diff 전체 {pooled0['p10']:+.4f} · "
      f"하위5 제거 {loo[4]['p10_diff']:+.4f} · 하위10 제거 {loo[9]['p10_diff']:+.4f} · 하위15 제거 {loo[14]['p10_diff']:+.4f}")

# ── D: 표본선택 (feasible 260 vs primary 210) ──
U = pd.read_csv(f"{S13}/treatment_universe_v3.csv", dtype={"k": str})
U["k"] = U.k.str.replace(r"\D", "", regex=True).str.zfill(10)
W_ = U[U.window_feasible == True].copy(); inc = W_[W_.emp_primary == True]; exc = W_[W_.emp_primary != True]
fin = pd.read_csv(f"{S13}/fin_distress_panel.csv", dtype={"bn": str})
fin["bn"] = fin.bn.str.replace(r"\D", "", regex=True).str.zfill(10)
W_["fy"] = W_.yr4.astype(int) - 1
W_ = W_.merge(fin.rename(columns={"bn": "k", "year": "fy"}), on=["k", "fy"], how="left")
inc = W_[W_.emp_primary == True]; exc = W_[W_.emp_primary != True]
def cmp_col(col, kind="num"):
    a = pd.to_numeric(inc[col], errors="coerce").dropna(); b = pd.to_numeric(exc[col], errors="coerce").dropna()
    if kind == "bin":
        pa, pb = float(a.mean()), float(b.mean())
        # 이항 비교: 카이제곱 대신 정규근사 차이 p
        se = np.sqrt(pa*(1-pa)/max(len(a),1) + pb*(1-pb)/max(len(b),1)); z = (pa-pb)/se if se > 0 else 0
        return dict(inc_mean=round(pa, 3), exc_mean=round(pb, 3), n_inc=len(a), n_exc=len(b),
                    p=round(float(2*(1-sps.norm.cdf(abs(z)))), 3))
    p = sps.mannwhitneyu(a, b).pvalue if len(a) > 5 and len(b) > 5 else np.nan
    return dict(inc_median=round(float(a.median()), 3), exc_median=round(float(b.median()), 3),
                inc_mean=round(float(a.mean()), 3), exc_mean=round(float(b.mean()), 3),
                n_inc=len(a), n_exc=len(b), mwu_p=round(float(p), 3))
R["D_selection"] = dict(n_feasible=len(W_), n_included=len(inc), n_excluded=len(exc),
                        event_year=cmp_col("yr4"), stake=cmp_col("stake"),
                        rescue_purpose=cmp_col("rescue", "bin"), equity=cmp_col("equity", "bin"),
                        leverage=cmp_col("lev"), roa=cmp_col("roa"), cash=cmp_col("cash"),
                        loss=cmp_col("loss", "bin"), impaired=cmp_col("impaired", "bin"))
print(f"  [D] feasible {len(W_)} = included {len(inc)} + excluded {len(exc)}")
for kk in ("event_year", "stake", "roa", "leverage", "loss", "rescue_purpose"):
    print(f"      {kk}: {R['D_selection'][kk]}")

json.dump(R, open(f"{OUT14}/wp14_comment_battery.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("→ wp14_comment_battery.json (A 하위창은 wp14a 별도)")
