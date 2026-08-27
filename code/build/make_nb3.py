# -*- coding: utf-8 -*-
import os,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from build_notebooks import build
NB="notebooks"
INTRO=["Appendix tables A1–F1, plus the robustness batteries the appendices cite.",
       "Read from `../artifacts/` only; outputs stored so they render on GitHub."]
SETUP='''import json, os
import pandas as pd
pd.set_option("display.width", 210)
ART = "../artifacts"
def A(n):
    with open(os.path.join(ART, n + ".json"), encoding="utf-8") as f: return json.load(f)
def show(df, t): print(t); print("-"*len(t)); print(df.to_string(index=False)); print()
print("ready")'''
C=[(["## Setup"],SETUP)]
C.append((["## Table A1 / A2 — Estimator battery and counterfactual-model audit"],
'''a = A("wp9a_audit")
rows = [(k, f"{v['point']:+.4f}", f"[{v['ci'][0]:+.4f}, {v['ci'][1]:+.4f}]", v.get("n",""))
        for k,v in a.items() if isinstance(v,dict) and "point" in v]
show(pd.DataFrame(rows, columns=["Specification","Point","95% CI","n"]), "Table A1. Employment ATT battery (legacy mixed pool)")
qk = [k for k in a if k.startswith("F_QTE")][0]; q = a[qk]
show(pd.DataFrame([(k, f"{v['point']:+.4f}", f"[{v['ci'][0]:+.4f}, {v['ci'][1]:+.4f}]") for k,v in q.items()],
                  columns=["Quantile","Point","95% CI"]), f"Table A1, quantile treatment effects ({qk})")
e = A("wp11e")
print("Table A2. Out-of-sample MSE by counterfactual model:", e["G4"]["oos_mse"])
print("  winner:", e["G4"]["winner"], "| event effect", e["G4"]["event_effect"], e["G4"]["ci"], "n =", e["G4"]["n_event"])
print("  trajectory break:", e["G5a_trajbreak"]["tau_accel"], e["G5a_trajbreak"]["ci"])
print("  DR-DiD:", e["G5b_dr"]["ATT_dr"], e["G5b_dr"]["ci"])'''))
C.append((["## Table B1 / B2 — Permutation benchmark and pseudo-event equivalence"],
'''p = A("wp9c_permutation")
print("Table B1. Legacy mixed-pool permutation benchmark")
print(json.dumps(p, ensure_ascii=False, indent=1)[:1200], "\\n")
fg = A("wp11fg"); g = fg["g_placebo_grid"]
rows = [(k, f"{v['mean']:+.4f}", "yes" if v["mean_equiv"] else "NO",
         f"{100*v['tail']:+.1f} pp", "yes" if v["tail_equiv"] else "NO", v["n"]) for k,v in g.items()]
rows.append(("event", f"{fg['f_honest']['mean']['effect']:+.4f}", "NO",
             f"{100*fg['f_honest']['tail']['effect']:+.1f} pp", "NO", ""))
show(pd.DataFrame(rows, columns=["Date","Mean gap",f"Mean within ±{fg['delta_mean']}?","Tail excess",
                                 f"Tail within ±{100*fg['delta_tail']:.0f} pp?","n"]),
     "Table B2. Pseudo-event grid: equivalence verdicts")
print("HonestDiD relative-magnitude breakdown M̄ — mean:", fg["f_honest"]["mean"]["breakdown_Mbar"],
      "| tail:", fg["f_honest"]["tail"]["breakdown_Mbar"])'''))
C.append((["## Table C1 — Exploratory heterogeneity and announcement-return prediction"],
'''r = A("wp13e_bhar_prediction")["runs"]
rows = [("Subgroup ATT: growth", r["subgroup_growth"]["n"], f"{r['subgroup_growth']['mean']:+.4f}", str(r["subgroup_growth"]["ci"])),
        ("Subgroup ATT: rescue", r["subgroup_rescue"]["n"], f"{r['subgroup_rescue']['mean']:+.4f}", str(r["subgroup_rescue"]["ci"])),
        ("Subgroup ATT: unclassified", r["subgroup_unclassified"]["n"], f"{r['subgroup_unclassified']['mean']:+.4f}", str(r["subgroup_unclassified"]["ci"]))]
show(pd.DataFrame(rows, columns=["Panel A","n","ATT","95% CI"]), "Table C1, Panel A. Locating the employment tail")
rows = [("OLS: outcome on CAR[-1,+1] + controls, HC1", f"{r['pred_ols_car11']['coef']:+.4f}",
         f"{r['pred_ols_car11']['ci']}, p = {r['pred_ols_car11']['p']}, n = {r['pred_ols_car11']['n']}"),
        ("Spearman rank correlation", f"{r['pred_spearman']['rho']:+.4f}", f"p = {r['pred_spearman']['p']}"),
        ("LPM 1(outcome <= -0.35) on CAR", f"{r['pred_lpm_severe']['coef']:+.4f}", f"{r['pred_lpm_severe']['ci']}, p = {r['pred_lpm_severe']['p']}"),
        ("CAR of severely contracting firms vs. rest", f"{100*r['pred_car_severe_vs_rest']['diff']:+.2f} pp", f"Welch p = {r['pred_car_severe_vs_rest']['p']}")]
show(pd.DataFrame(rows, columns=["Panel B — no predictive content","Estimate","Inference"]), "Table C1, Panel B")
print("CAR terciles (mean outcome):", {k: v["mean_d2"] for k,v in r["pred_tercile"].items()})'''))
C.append((["## Table D1 — Alternative state definitions, and the balance diagnostics"],
'''b = A("wp12b")["runs"]
keys = [("A_all_vs_all","All (no stratification)"),("C_declfar_1","Pre-event decline, months −25..−13"),
        ("C_declfar_0","No pre-event decline"),("D_d1_f1","Distressed ∧ decline"),("D_d1_f0","Distressed ∧ no decline"),
        ("D_d0_f1","Non-distressed ∧ decline"),("D_d0_f0","Non-distressed ∧ no decline")]
rows=[]
for k,lab in keys:
    r=b.get(k)
    if not r: continue
    rows.append((lab, r["n_treated"], r["n_ctrl_events"],
                 f"{r['median']['obs']:+.4f} {r['median']['ci']}", f"{r['p10']['obs']:+.4f} {r['p10']['ci']}",
                 f"{len(r['curve']['sig_region'])}/{len(r['curve']['grid'])}"))
show(pd.DataFrame(rows, columns=["Stratum","n rec.","n non-rec. events","Median [95% CI]","p10 [95% CI]","Uniform bands > 0"]),
     "Table D1, Panel A. Alternative stratifications")
old = A("wp11c")
print("Panel B (superseded comparator, retained deliberately): median", old["median_diff"], "| mean", old["mean_diff"],
      "| p10", old["p10_diff"], "| n", old["n_treated"], "vs", old["n_distressed_ne"])
g = A("wp13h_flow_bands")["runs"]["B_band_sensitivity"]
for bnd,row in g.items():
    n_eq = sum(1 for k,v in row.items() if k != "event" and v["equiv"])
    print(f"  Equivalence band {bnd}: {n_eq}/4 pseudo-dates equivalent; event equivalent = {row['event']['equiv']}")'''))
C.append((["## Table F1 — Long-run returns and delisting bounds"],
'''r = A("wp13e_bhar_prediction")["runs"]
rows=[]
for lab,key in (("All","all"),("Rescue","rescue"),("Growth","growth"),("Unclassified","unclassified")):
    o=r[f"관측_{key}"]; d=r[f"하한_{key}"]
    rows.append((lab, o["n"], f"{100*o['mean']:+.2f}%", f"[{100*o['ci'][0]:+.1f}%, {100*o['ci'][1]:+.1f}%]", f"{100*o['median']:+.1f}%",
                 d["n"], f"{100*d['mean']:+.2f}%", f"[{100*d['ci'][0]:+.1f}%, {100*d['ci'][1]:+.1f}%]", f"{100*d['median']:+.1f}%"))
show(pd.DataFrame(rows, columns=["Group","n obs","Mean (obs)","95% CI","Median (obs)","n bound","Mean (bound)","95% CI (bound)","Median (bound)"]),
     "Table F1. Twelve-month market-adjusted BHAR by purpose")
print("Rescue − growth: observed", r["관측_rescue_vs_growth"], "\\n                 bounded", r["하한_rescue_vs_growth"])
print("\\nDelisting-suspect decomposition:")
for k in ("susp_overall","susp_tail","susp_rest","susp_rescue","susp_growth"): print("  ", k, r[k])
print("  tail vs rest Fisher p =", r["susp_tail_vs_rest"]["fisher_p"], "| rescue vs growth p =", r["susp_rescue_vs_growth"]["fisher_p"])
print("  absent-firm composition:", r["absent_composition"])'''))
C.append((["## Robustness batteries the appendices cite"],
'''h = A("wp13h_flow_bands")["runs"]
for k,lab in (("E_flow_all","All recipients"),("E_flow_tail","Tail quartile"),("E_flow_non_tail","Non-tail")):
    if k in h:
        r=h[k]; print(f"{lab}: hires {r['hire']['obs']:+.4f} {r['hire']['ci']} · separations {r['sep']['obs']:+.4f} {r['sep']['ci']} · "
                      f"difference {r['diff']['obs']:+.4f} {r['diff']['ci']} (bootstrap corr {r['corr_hire_sep']:+.2f}, n={r['n']})")
print("Flow–headcount consistency:", h["E_identity"], "\\n")
f = A("wp13f_allottee_rd")["runs"]
print("RD probe at the capital-impairment boundary:")
for k in [x for x in f if x.startswith("B_rd_h")]:
    o=f[k]; print(f"  h=±{o['bandwidth']}: left {100*o['left_p']:.3f}% (n={o['left_n']}) vs right {100*o['right_p']:.3f}% (n={o['right_n']}), Fisher p = {o['fisher_p']}")
print("\\nAllottee moderation:", {k:f["A_coverage"][k] for k in ("n_named","share_named","share_financial","share_other")})
print("  employment difference:", f["A_emp_diff"], "| CAR difference:", f["A_car_diff"])
i = A("wp13i_case_prescreen"); print("\\nTail case pre-screen:", i["n_with_struct_filing"], "of", i["n_cases"], "flagged;", i["note"][:90])''' ))
build(f"{NB}/03_appendix_tables.ipynb","# P-016 — Appendix tables and robustness batteries",INTRO,C)
