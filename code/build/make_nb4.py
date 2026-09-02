# -*- coding: utf-8 -*-
"""04_comment_robustness.ipynb — referee-comment analyses (wp14/wp14a), journal formatting (4 dp, n, p)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_notebooks import build
NB = "notebooks"
LOAD = '''import json, os
import pandas as pd
pd.set_option("display.width", 200); pd.set_option("display.max_colwidth", 90)
ART = "../artifacts"
def A(name):
    with open(os.path.join(ART, name + ".json"), encoding="utf-8") as f: return json.load(f)
def show(df, t): print(t); print("-" * len(t)); print(df.to_string(index=False)); print()
def f4(x): return f"{x:+.4f}"
def ci4(c): return f"[{c[0]:+.4f}, {c[1]:+.4f}]"
B = A("wp14_comment_battery"); SW = A("wp14a_subwindow")
print("loaded: wp14_comment_battery, wp14a_subwindow")'''
C1 = '''rows = []
for w, lab in (("m+1..+6", "Months +1 to +6"), ("m+7..+12", "Months +7 to +12")):
    r = SW[w]
    rows.append({"Outcome window": lab,
                 "P10 diff": f4(r["p10"]["obs"]), "95% CI": ci4(r["p10"]["ci"]),
                 "Severe excess": f4(r["sev"]["obs"]), "CI ": ci4(r["sev"]["ci"]),
                 "Median diff": f4(r["median"]["obs"]),
                 "N (event/pseudo)": f"{r['n_event']}/{r['n_placebo']}"})
show(pd.DataFrame(rows), "Table R1. Sub-window tail dynamics: actual event vs pooled pseudo-events")
print("Notes. Baseline window fixed at months -12..-1; matching identical to the primary design.")
print("Severe excess = difference in Pr(outcome <= -0.35). Firm-clustered bootstrap CIs (B=4,000).")'''
C2 = '''rows = []
for key, lab in (("vs_pooled", "Pooled pseudo-events (561)"), ("vs_t24", "t-24 (published basis, n=142)"),
                 ("vs_t36_replic", "t-36 (125)"), ("vs_t18", "t-18 (163)")):
    g = B["B_grid"][key]
    rows.append({"Benchmark": lab, "Positive thresholds": f"{sum(1 for d in g['diff'] if d > 0)}/11",
                 "Uniform lower>0": f"{g['n_pos_lower']}/11",
                 "Diff at -0.35": f4(g["at_035"]["diff"]), "Uniform band": ci4(g["at_035"]["band"]),
                 "max-t adj p (P10)": f"{g['maxt_adj_p']['p10']:.4f}", "N bench": g["n_bench"]})
show(pd.DataFrame(rows), "Table R2. Collapse-probability grid under four pseudo-event benchmarks")
print("Reconciliation. The manuscript grid (+0.1199 [0.0515, 0.1884] at -0.35; max-t P10 p=0.0055) is the")
print("wp11d event-minus-t-24 contrast; the t-24 row above re-estimates the same contrast from the pooled-")
print("contrast pipeline (wp13c cache). The ~1pp gap reflects placebo-vector implementation, not benchmark choice.")
w11 = A("wp11d"); i35 = w11["grid"].index(-0.35)
assert abs(w11["ddd"]["point"][i35] - 0.1199) < 5e-4
print(f"wp11d ddd at -0.35 = {w11['ddd']['point'][i35]:+.4f} uniform [{w11['ddd']['lo_unif'][i35]:+.4f}, {w11['ddd']['hi_unif'][i35]:+.4f}]  (matches manuscript B.5)")'''
C3 = '''ci = B["C_influence"]
rows = [{"Removed (most extreme)": "none", "P10, event": f4(ci["p10_event"]), "Event-pseudo P10 diff": f4(ci["p10_diff_full"]),
         "Severe rate": f"{ci['severe_rate']:.4f}"}]
for m in (5, 10, 15):
    d = ci["drop_bottom_cum"][m - 1]
    rows.append({"Removed (most extreme)": f"bottom {m}", "P10, event": f4(d["p10"]),
                 "Event-pseudo P10 diff": f4(d["p10_diff"]), "Severe rate": f"{d['sev']:.4f}"})
show(pd.DataFrame(rows), "Table R3. Influence of extreme recipients (matched outcome, event arm)")
sing = ci["drop_single_bottom15_p10diff"]
print(f"Counts: matched outcome <= -0.35 for {ci['n_severe_035']} of {ci['n']} recipients (own-firm outcome: 30 of 210, Appendix D1).")
print(f"Single deletions of each of the bottom 15 recipients keep the pooled P10 contrast negative: min {min(sing):+.4f}, max {max(sing):+.4f}.")
assert all(v < 0 for v in sing)'''
C4 = '''d = B["D_selection"]
rows = []
for key, lab, kind in (("event_year", "Event year", "num"), ("stake", "Allottee stake", "num"),
                       ("rescue_purpose", "Rescue purpose share", "bin"), ("equity", "Equity placement share", "bin"),
                       ("leverage", "Leverage", "num"), ("roa", "ROA", "num"), ("cash", "Cash holdings", "num"),
                       ("loss", "Loss share", "bin"), ("impaired", "Capital impairment share", "bin")):
    v = d[key]
    if kind == "num":
        rows.append({"Variable": lab, "Included (210)": f"{v['inc_median']:.4f}", "Excluded (50)": f"{v['exc_median']:.4f}",
                     "Statistic": "median", "p": f"{v['mwu_p']:.4f}", "n (inc/exc)": f"{v['n_inc']}/{v['n_exc']}"})
    else:
        rows.append({"Variable": lab, "Included (210)": f"{v['inc_mean']:.4f}", "Excluded (50)": f"{v['exc_mean']:.4f}",
                     "Statistic": "share", "p": f"{v['p']:.4f}", "n (inc/exc)": f"{v['n_inc']}/{v['n_exc']}"})
show(pd.DataFrame(rows), "Table R4. Included vs calendar-feasible excluded transactions")
print("Notes. p from Mann-Whitney (continuous) or normal-approximation proportion tests (shares).")
print("Only leverage differs (p=0.0270): excluded transactions are more levered, so exclusion tilts the")
print("sample away from the most levered issuers; the Appendix D1 adverse bound already covers this margin.")'''
C5 = '''# Consistency with the published headline numbers
b3 = A("wp13c_pooled_placebo")["runs"]["A_pooled_cluster"]
print("Table 1 Panel A (published) vs this battery's basis:")
print(f"  pooled P10 contrast: published {b3['p10']['obs']:+.4f} [{b3['p10']['ci'][0]:+.4f}, {b3['p10']['ci'][1]:+.4f}] · battery basis {B['C_influence']['p10_diff_full']:+.4f}")
assert abs(b3["p10"]["obs"] - B["C_influence"]["p10_diff_full"]) < 5e-4
sw = SW["m+7..+12"]
print(f"  primary-window subcheck (m+7..+12) equals the headline basis: {sw['p10']['obs']:+.4f} (point), CI re-bootstrapped {ci4(sw['p10']['ci'])}")
print("  severe counts: matched-outcome 35/210; own-firm outcome 30/210 (14.29%, Appendix D1) — two distinct bases, both reported.")
print("consistency checks passed")'''
build(os.path.join("notebooks", "04_comment_robustness.ipynb"),
      "# Referee-comment robustness analyses (wp14, 2026-09-02)",
      ["Four analyses added in response to the pre-submission referee review: sub-window tail dynamics, multi-benchmark threshold grids, influence of extreme recipients, and the sample-selection comparison.",
       "All numbers are read from `artifacts/wp14_comment_battery.json` and `artifacts/wp14a_subwindow.json`; formatting follows the manuscript (log points to 4 dp, empirical p to 4 dp, explicit n)."],
      [(["## Setup"], LOAD),
       (["## R1 — Sub-window tail dynamics"], C1),
       (["## R2 — Threshold grid under four benchmarks", "The published manuscript grid is the event-minus-t-24 contrast (wp11d); the t-36 label in the draft is corrected in the submission edits."], C2),
       (["## R3 — Influence of extreme recipients"], C3),
       (["## R4 — Sample-selection comparison"], C4),
       (["## Consistency checks against published numbers"], C5)])
print("built 04_comment_robustness.ipynb")
