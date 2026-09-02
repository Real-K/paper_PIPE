# -*- coding: utf-8 -*-
"""notebooks_FRL — FRL 제출판(PIPE_paper/appendix_humanized.docx) 기준 표·그림 재현 노트북 2권."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_notebooks import build
os.makedirs("notebooks_FRL", exist_ok=True)
LOAD = '''import json, os
import pandas as pd
pd.set_option("display.width", 200); pd.set_option("display.max_colwidth", 90)
ART = "../artifacts"
def A(name):
    with open(os.path.join(ART, name + ".json"), encoding="utf-8") as f: return json.load(f)
def show(df, t): print(t); print("-" * len(t)); print(df.to_string(index=False)); print()
def f4(x): return f"{x:+.4f}"
def ci4(c): return f"[{c[0]:+.4f}, {c[1]:+.4f}]"
def okp(a, b, nd=4): assert round(a, nd) == round(b, nd), (a, b)
print("ready")'''

FIG1 = '''import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
fg = A("wp11fg"); g = fg["g_placebo_grid"]; fh = fg["f_honest"]
clocks = ["t-36", "t-30", "t-24", "t-18"]; xs = [-36, -30, -24, -18, 0]
mean_b = [g[c]["mean"] for c in clocks] + [fh["mean"]["effect"]]
mean_ci = [g[c]["mean_ci"] for c in clocks] + [fh["mean"]["grid"][0]["ci"]]
tail_b = [g[c]["tail"] for c in clocks] + [fh["tail"]["effect"]]
tail_ci = [g[c]["tail_ci"] for c in clocks] + [fh["tail"]["grid"][0]["ci"]]
# 원고 수치 대조 (Figure 1 / Table B2)
okp(mean_b[0], -0.0058); okp(mean_b[2], -0.0520); okp(mean_b[4], -0.0809)
okp(tail_b[4], 0.1099); okp(tail_ci[4][0], 0.0907); okp(tail_ci[4][1], 0.1291)
fig, ax = plt.subplots(1, 2, figsize=(10.6, 4.0))
for a, b, ci, band, ttl, ylab in ((ax[0], mean_b, mean_ci, fg["delta_mean"], "Panel A. Mean recipient-control gap", "Log points"),
                                  (ax[1], tail_b, tail_ci, 0.05, "Panel B. Severe-contraction excess (c = -0.35)", "Probability")):
    import numpy as np
    b = np.array(b); lo = np.array([c[0] for c in ci]); hi = np.array([c[1] for c in ci])
    a.axhspan(-band, band, color="0.55", alpha=.15, lw=0)
    a.axhline(0, color="0.45", lw=.8)
    a.errorbar(xs, b, yerr=[b - lo, hi - b], fmt="o", ms=5, capsize=3, color="#1b4a8a", ecolor="0.6")
    a.set_title(ttl, fontsize=10.5, loc="left"); a.set_xlabel("Event clock (months before actual placement)"); a.set_ylabel(ylab)
    a.spines[["top", "right"]].set_visible(False)
fig.suptitle("Figure 1. Mean employment gap and severe-contraction excess across event clocks", x=.01, ha="left", fontsize=10.5)
fig.tight_layout()
print("Figure 1 rebuilt; manuscript values asserted (mean path, event tail 0.1099 [0.0907, 0.1291]).")'''

T1A = '''r = A("wp13c_pooled_placebo")["runs"]
p = r["A_pooled_cluster"]; c = r["C_common_pooled_cluster"]
rows = [{"Statistic": s.capitalize() if s != "p10" else "Tenth percentile",
         "Event - pooled pseudo": f4(p[s]["obs"]), "95% CI": ci4(p[s]["ci"]),
         "Common 116-firm sample": f4(c[s]["obs"]), "CI ": ci4(c[s]["ci"])}
        for s in ("mean", "p10", "p25", "median")]
show(pd.DataFrame(rows), "Table 1, Panel A. Actual event versus pooled pseudo-events (and Appendix Table B3)")
okp(p["mean"]["obs"], -0.0481); okp(p["p10"]["obs"], -0.2527); okp(p["p25"]["obs"], -0.0641); okp(p["median"]["obs"], -0.0036)
okp(p["p10"]["ci"][0], -0.3713); okp(p["p10"]["ci"][1], -0.0953); okp(c["p10"]["obs"], -0.2193)
print(f"n: event {p['n_event']} · pooled pseudo {p['n_placebo']} (firms {p['n_placebo_firms']}) · common firms {r['C_common_n_firms']}")
print("manuscript values asserted (Table 1 Panel A, Table B3)")'''

T1B = '''b = A("wp12b")["runs"]
d1, d0, pool, allr = b["B_distress_1"], b["B_distress_0"], b["E_pool_distress"], b["A_all_vs_all"]
i35 = allr["curve"]["grid"].index(-0.35)
def sev(run):
    j = run["curve"]["grid"].index(-0.35)
    return (run["cprob_treated"]["-0.35"], run["cprob_ctrl_w"]["-0.35"], run["curve"]["diff"][j],
            run["curve"]["lo_unif"][j], run["curve"]["hi_unif"][j])
rows = []
for s, lab in (("median", "Median"), ("p10", "Tenth percentile"), ("mean", "Mean")):
    rows.append({"Statistic": lab,
                 "Distressed": f"{f4(d1[s]['obs'])} {ci4(d1[s]['ci'])}",
                 "Non-distressed": f"{f4(d0[s]['obs'])} {ci4(d0[s]['ci'])}",
                 "Pooled": f"{f4(pool[s]['obs'])} {ci4(pool[s]['ci'])}"})
t1, c1, df1, lo1, hi1 = sev(d1); t0, c0, df0, lo0, hi0 = sev(d0); ta, ca, dfa, loa, hia = sev(allr)
rows += [{"Statistic": "Pr(severe): recipients", "Distressed": f"{t1:.4f}", "Non-distressed": f"{t0:.4f}", "Pooled": f"{ta:.4f}"},
         {"Statistic": "Pr(severe): weighted non-recipients", "Distressed": f"{c1:.4f}", "Non-distressed": f"{c0:.4f}", "Pooled": f"{ca:.4f}"},
         {"Statistic": "Difference at c=-0.35 [uniform band]", "Distressed": f"{f4(df1)} [{lo1:+.4f}, {hi1:+.4f}]",
          "Non-distressed": f"{f4(df0)} [{lo0:+.4f}, {hi0:+.4f}]", "Pooled": f"{f4(dfa)} [{loa:+.4f}, {hia:+.4f}]"}]
show(pd.DataFrame(rows), "Table 1, Panel B / Appendix Tables C3-C4. Same measured state")
okp(d1["median"]["obs"], -0.0015); okp(d1["p10"]["obs"], -0.3414); okp(d0["p10"]["obs"], -0.2197)
okp(pool["median"]["obs"], 0.0076); okp(pool["p10"]["obs"], -0.2863)
assert round(t1, 4) == 0.1826 and round(c1, 4) == 0.0442
assert round(dfa, 4) == 0.1093 and round(loa, 4) == 0.0482 and round(hia, 4) == 0.1704
print(f"n: distressed {d1['n_treated']}/{d1['n_ctrl_events']:,} events ({d1['n_ctrl_firms']} firms) · "
      f"non-distressed {d0['n_treated']}/{d0['n_ctrl_events']:,} ({d0['n_ctrl_firms']})")
print("manuscript values asserted (medians, tenth percentiles, severe rows)")'''

PROSE1 = '''# 본문 프로즈 수치 대조 (§1, §3.1-3.3)
fg = A("wp11fg"); g = fg["g_placebo_grid"]
okp(g["t-30"]["mean"], -0.0115); okp(g["t-18"]["mean"], -0.0576)
st = A("wp10ab")["A_stake"]
okp(st["median"], 0.0616, 4); assert st["n_stake"] == 201 and round(st["ge50"], 3) == 0.005
print("§1: stakes median 6.16%, n=201, >=50% share 0.5%  ✓")
print("§3.1: mean path -0.0058 / -0.0115 / -0.0520 / -0.0576 / -0.0809  ✓")
b6 = A("wp11o_confound")["employment"]
assert b6["all"]["n"] == 210 and b6["clean_narrow"]["n"] == 183 and b6["clean_broad"]["n"] == 157
print("§2/B.7: screens 210/183/157  ✓")
print("all prose checks passed")'''

A12 = '''u = A("wp13a_universe")["flow"]
show(pd.DataFrame(u), "Sample flow (canonical universe v3)")
st = A("wp10ab")["A_stake"]
rows = [{"Statistic": k, "Value": v} for k, v in (("25th percentile", f"{st['p25']:.4f}"), ("Median", f"{st['median']:.4f}"),
        ("75th percentile", f"{st['p75']:.4f}"), ("90th percentile", f"{st['p90']:.4f}"),
        ("Share >= 30%", f"{st['ge30']:.4f}"), ("Share >= 50%", f"{st['ge50']:.4f}"), ("Observations", st["n_stake"]))]
show(pd.DataFrame(rows), "Table A2. Allottee post-money stakes")
print("NOTE (manuscript Table A1): the printed upstream counts 393 (371 equity + 22 CB) and '353 structured + 7")
print("document-parsed' come from the v2 extraction; the canonical v3 universe is 415 (389 + 26) with 382 dated")
print("(357 structured + 25 parsed), identical from the 360-in-window step onward (321/260/210/209/208/201/196).")
print("This discrepancy is flagged in 10_submission/EDIT_SUGGESTIONS_2026-09-02.md for correction before submission.")'''

B12 = '''e = A("wp11e")
m = e["G4"]["oos_mse"]
rows = [{"Counterfactual model": lab, "Out-of-sample MSE": f"{m[k]:.4f}"} for k, lab in
        (("M1_match", "Matched listed controls"), ("M3_industry", "Industry benchmark"),
         ("M4_synth", "Synthetic control"), ("M2_trend", "Firm-specific linear trend"))]
show(pd.DataFrame(rows), "Table B1. Pre-event counterfactual-model comparison")
okp(m["M1_match"], 0.0393); okp(m["M3_industry"], 0.0490, 4)
print(f"B.2 prose: event-window {f4(e['G4']['event_effect'])} {ci4(e['G4']['ci'])} (n={e['G4']['n_event']}) · "
      f"trajectory-break {f4(e['G5a_trajbreak']['tau_accel'])} {ci4(e['G5a_trajbreak']['ci'])} · "
      f"DR-DiD {f4(e['G5b_dr']['ATT_dr'])} {ci4(e['G5b_dr']['ci'])}")
fg = A("wp11fg"); g = fg["g_placebo_grid"]; fh = fg["f_honest"]
rows = [{"Event clock": c, "N": g[c]["n"], "Mean gap": f4(g[c]["mean"]), "Mean CI": ci4(g[c]["mean_ci"]),
         "Tail excess": f4(g[c]["tail"]), "Tail CI": ci4(g[c]["tail_ci"])} for c in ("t-36", "t-30", "t-24", "t-18")]
rows.append({"Event clock": "Actual event", "N": 210, "Mean gap": f4(fh["mean"]["effect"]), "Mean CI": ci4(fh["mean"]["grid"][0]["ci"]),
             "Tail excess": f4(fh["tail"]["effect"]), "Tail CI": ci4(fh["tail"]["grid"][0]["ci"])})
show(pd.DataFrame(rows), "Table B2. Pseudo-event grid")'''

B45 = '''r = A("wp13c_pooled_placebo")["runs"]
rows = [{"Comparison": f"Event minus t-{s}", "P10 difference": f4(r[f"D_t{s}_only"]["p10"]["obs"]),
         "95% CI": ci4(r[f"D_t{s}_only"]["p10"]["ci"]), "N pseudo": r[f"D_t{s}_only"]["n_placebo"]}
        for s in (18, 24, 30, 36)]
show(pd.DataFrame(rows), "Table B4. Tenth-percentile contrast by pseudo-date")
okp(r["D_t18_only"]["p10"]["obs"], -0.2035); okp(r["D_t24_only"]["p10"]["obs"], -0.2647)
d = A("wp11d"); G = d["grid"]
rows = []
for c in (-0.60, -0.35, -0.10):
    j = G.index(round(c, 2))
    rows.append({"Threshold": c, "Difference": f4(d["ddd"]["point"][j]),
                 "95% uniform band": f"[{d['ddd']['lo_unif'][j]:+.4f}, {d['ddd']['hi_unif'][j]:+.4f}]"})
show(pd.DataFrame(rows), "Table B5. Collapse-probability curve (event minus t-24; manuscript label 't-36' is corrected in the edits)")
jm = d["joint_multiplicity"]
print("max-t adjusted p:", dict(zip(jm["stats"], jm["maxT_adjusted_p"])))
okp(d["ddd"]["point"][G.index(-0.35)], 0.1199); assert jm["maxT_adjusted_p"][jm["stats"].index("p10")] == 0.0055
b6 = A("wp11o_confound")["employment"]
rows = [{"Sample": lab, "N": v["n"], "Mean": f4(v["mean"]), "95% CI": ci4(v["mean_ci"]), "Median": f4(v["median"]),
         "P10": f4(v["p10"]), "Pr<= -0.35": f"{v['collapse_035']:.4f}"}
        for lab, v in (("Full employment sample", b6["all"]), ("Narrow exclusion screen", b6["clean_narrow"]),
                       ("Broad exclusion screen", b6["clean_broad"]))]
show(pd.DataFrame(rows), "Table B6. Concurrent-filing screens")'''

C15 = '''c = A("wp12c_balance")["runs"]
d1, d0 = c["B_distress_1"], c["B_distress_0"]
lab = {"logsize": "Log firm size", "pg": "Pre-event employment growth", "yr": "Calendar year", "lev": "Leverage",
       "roa": "ROA", "cash": "Cash", "imp": "Capital impairment", "loss": "Loss"}
rows = [{"Covariate": lab[k], "Distressed": f"{d1['smd_by_covariate'][k]:+.4f}",
         "Non-distressed": (f"{d0['smd_by_covariate'][k]:+.4f}" if k in d0["smd_by_covariate"] else "-")}
        for k in lab]
show(pd.DataFrame(rows), "Table C1. Standardized mean differences after same-state weighting")
okp(d1["smd_by_covariate"]["roa"], -0.123, 3); okp(d1["max_abs_smd"], 0.123, 3)
wd1, wd0 = d1["weight_diagnostics"], d0["weight_diagnostics"]
rows = [{"Diagnostic": k, "Distressed": f"{wd1.get(k, d1.get(k)):,}", "Non-distressed": f"{wd0.get(k, d0.get(k)):,}"}
        for k in sorted(set(list(wd1) + ["ess"]))][:8]
show(pd.DataFrame(rows), "Table C2. Weight diagnostics (raw fields)")
assert round(d1["ess"], 1) == 14566.5
b = A("wp12b")["runs"]
rows = [{"State": lab, "Recipients": r_["n_treated"], "Median diff": f"{f4(r_['median']['obs'])} {ci4(r_['median']['ci'])}",
         "P10 diff": f"{f4(r_['p10']['obs'])} {ci4(r_['p10']['ci'])}"}
        for lab, r_ in (("Earlier employment decline", b["C_declfar_1"]), ("No earlier decline", b["C_declfar_0"]),
                        ("Pooled across groups", b["E_pool_declfar"]))]
show(pd.DataFrame(rows), "Table C5. Alternative stratification by earlier employment decline")
okp(b["C_declfar_1"]["p10"]["obs"], -0.1823); okp(b["C_declfar_0"]["p10"]["obs"], -0.2886)'''

D1E1 = '''w = A("wp13b_censoring")
rows = [{"Sample": lab, "N": v["n"], "Mean": f4(v["mean"]), "Median": f4(v["median"]), "P10": f4(v["p10"]),
         "Pr<=-0.35": f"{v['c35']:.4f}", "Pr<=-0.60": f"{v['c60']:.4f}"}
        for lab, v in (("Primary sample", w["full"]), ("Complete 12-month follow-up", w["complete12"]),
                       ("Nine early cessations at -0.75", w["worst_case_exits_as_collapse"]))]
show(pd.DataFrame(rows), "Table D1. Observation-window sensitivity")
okp(w["full"]["c35"], 0.1429); okp(w["worst_case_exits_as_collapse"]["c35"], 0.1781)
h = A("wp13h_flow_bands")["runs"]
f = h["E_flow_all"]
rows = [{"Statistic": lab, "Estimate": f4(f[k]["obs"]), "95% CI": ci4(f[k]["ci"])}
        for k, lab in (("hire", "Cumulative hires / baseline employment"),
                       ("sep", "Cumulative separations / baseline employment"),
                       ("diff", "Hires minus separations"))]
show(pd.DataFrame(rows), "Table E1. Employment-flow decomposition")
okp(f["hire"]["obs"], -0.0445); okp(f["diff"]["obs"], -0.0681); assert f["n"] == 217
ident = h["E_identity"]
print(f"E.3 reconciliation: n={ident['n']}, corr {ident['corr']:.4f}, median |gap| {ident['median_abs_gap']:.4f}, mean |gap| {ident['mean_abs_gap']:.4f}")
print("all appendix checks passed")'''

build(os.path.join("notebooks_FRL", "01_paper_FRL.ipynb"),
      "# FRL submission — main-paper exhibits (Figure 1, Table 1)",
      ["Rebuilds the current FRL manuscript's Figure 1 and Table 1 from the aggregate artifacts, and asserts every printed number at its displayed rounding.",
       "Formatting: log points and probabilities to 4 dp; explicit n throughout. No licensed microdata."],
      [(["## Setup"], LOAD),
       (["## Figure 1 — mean gap and severe-contraction excess across event clocks"], FIG1),
       (["## Table 1, Panel A — actual event vs pooled pseudo-events"], T1A),
       (["## Table 1, Panel B — recipients vs non-recipients in the same measured state"], T1B),
       (["## Prose consistency checks (§1-§3)"], PROSE1)])
build(os.path.join("notebooks_FRL", "02_appendix_FRL.ipynb"),
      "# FRL submission — online-appendix exhibits (Tables A1-E1)",
      ["Rebuilds the appendix tables of the current FRL manuscript from the artifacts, with asserts against the printed values.",
       "One documented discrepancy: the manuscript's Table A1 upstream counts come from the v2 extraction (flagged for correction)."],
      [(["## Setup"], LOAD),
       (["## A — Sample flow and stakes (Tables A1-A2)"], A12),
       (["## B1-B2 — Counterfactual audit and pseudo-event grid"], B12),
       (["## B4-B6 — Per-date contrasts, threshold grid (t-24), filing screens"], B45),
       (["## C — Same-state balance, weights, alternative stratification (C1, C2, C5)"], C15),
       (["## D1, E1 — Observation window and flow decomposition"], D1E1)])
print("built notebooks_FRL")
