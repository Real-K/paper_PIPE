# -*- coding: utf-8 -*-
import os,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from build_notebooks import build
NB="notebooks"; os.makedirs(NB,exist_ok=True)

LOAD = '''import json, os
import pandas as pd
pd.set_option("display.width", 200); pd.set_option("display.max_colwidth", 90)

ART = "../artifacts"
def A(name):
    """Load one aggregate result artifact by file stem."""
    with open(os.path.join(ART, name + ".json"), encoding="utf-8") as f:
        return json.load(f)

def show(df, title):
    print(title); print("-" * len(title)); print(df.to_string(index=False)); print()

print("artifacts available:", len(os.listdir(ART)))'''

INTRO_COMMON = [
 "Every number below is read from an aggregate result artifact in `../artifacts/`.",
 "No licensed microdata is used or required — see `../DATA_ACCESS.md`.",
 "Outputs are stored in this notebook, so the tables render on GitHub without running anything.",
]

# ─────────── 01 main tables ───────────
c1=[]
c1.append((["## Setup"],LOAD))
c1.append((["## Table 1 — Sample construction and allottee stakes",
            "Panel A is the treatment-universe flow; Panel B the allottee post-money stake distribution."],
'''u = A("wp13a_universe")
flow = pd.DataFrame(u["flow"])[["n","step","note"]].rename(columns={"n":"N","step":"Step","note":"Definition / use"})
show(flow[["Step","N","Definition / use"]], "Table 1, Panel A. Sample construction")

s = A("wp10ab")["A_stake"]
panelB = pd.DataFrame([
    ("Median", f"{100*s['median']:.2f}%"), ("p25 / p75", f"{100*s['p25']:.1f}% / {100*s['p75']:.1f}%"),
    ("p90", f"{100*s['p90']:.1f}%"), ("Share >= 30%", f"{100*s['ge30']:.1f}%"),
    ("Share >= 50%", f"{100*s['ge50']:.1f}%"), ("n", s["n_stake"]),
], columns=["Statistic","Value"])
show(panelB, "Table 1, Panel B. Allottee post-money stake")'''))
c1.append((["## Table 2 — Announcement cumulative abnormal returns"],
'''w = A("wp8b_car")["windows"]
rows = [(k.replace("m1_p1","[-1,+1]").replace("e0_p1","[0,+1]").replace("e0_p5","[0,+5]").replace("e0_p20","[0,+20]"),
         f"{100*v['mean_CAR']:+.2f}%", f"{v['t']:.2f}", f"[{100*v['ci95'][0]:.1f}%, {100*v['ci95'][1]:.1f}%]",
         f"{100*v['median']:+.1f}%", f"{100*v['pct_pos']:.1f}%") for k,v in w.items()]
show(pd.DataFrame(rows, columns=["Window","Mean CAR","t","95% CI","Median","% positive"]),
     f"Panel A. Equal-weighted proxy (n = {A('wp8b_car')['n_car']})")

b = A("wp10ab")["B_car"]; p = b["purpose_full"]
rows = [("Rescue (working capital / debt repayment)", p["n_surv"], f"{100*p['surv_car11']:+.2f}%", f"{p['surv_bmp_t']:.2f}"),
        ("Growth (facilities / acquisitions)",        p["n_grow"], f"{100*p['grow_car11']:+.2f}%", f"{p['grow_bmp_t']:.2f}"),
        ("Difference", "", f"{100*p['diff']:+.2f} pp", f"Welch p = {p['welch_p']}")]
show(pd.DataFrame(rows, columns=["Purpose","n","Mean CAR [-1,+1]","BMP t"]),
     "Panel B. Purpose split, value-weighted exchange-index proxy")'''))
c1.append((["## Table 3 — Average employment path",
            "Listed clean-pool ATT, the pseudo-event gradient, and the two event-year anchors."],
'''l = A("wp10c_listed"); e = A("wp11e"); fg = A("wp11fg")
rows = [("ATT, avg months +1..+12 (listed clean pool)", l["ATT_avg1_12"]["point"], l["ATT_avg1_12"]["ci"], l["ATT_avg1_12"]["n"]),
        ("ATT, avg months +7..+12", l["ATT_avg7_12"]["point"], l["ATT_avg7_12"]["ci"], l["ATT_avg7_12"]["n"]),
        ("Validated counterfactual model (OOS winner)", e["G4"]["event_effect"], e["G4"]["ci"], e["G4"]["n_event"]),
        ("Trajectory break vs. preceding year", e["G5a_trajbreak"]["tau_accel"], e["G5a_trajbreak"]["ci"], e["G5a_trajbreak"]["n_t"]),
        ("DR-DiD with distress covariates", e["G5b_dr"]["ATT_dr"], e["G5b_dr"]["ci"], e["G5b_dr"]["n_treat"])]
show(pd.DataFrame([(a, f"{b:+.4f}", f"[{c[0]:+.4f}, {c[1]:+.4f}]", d) for a,b,c,d in rows],
                  columns=["Estimate","Point","95% CI","n"]), "Panel A. Benchmarks")

g = fg["g_placebo_grid"]
rows = [(k, f"{v['mean']:+.4f}", f"[{v['mean_ci'][0]:+.4f}, {v['mean_ci'][1]:+.4f}]",
         "yes" if v["mean_equiv"] else "NO", v["n"]) for k,v in g.items()]
rows.append(("event", f"{fg['f_honest']['mean']['effect']:+.4f}",
             f"[{fg['f_honest']['mean']['grid'][0]['ci'][0]:+.4f}, {fg['f_honest']['mean']['grid'][0]['ci'][1]:+.4f}]", "NO", ""))
show(pd.DataFrame(rows, columns=["Date","Mean gap","95% CI",f"Within +/-{fg['delta_mean']}?","n"]),
     "Panel B. Pseudo-event grid (mean)")'''))
c1.append((["## Table 4 — The collapse tail"],
'''d = A("wp11d"); c3 = A("wp13c_pooled_placebo")["runs"]
grid = d["grid"]
cur = pd.DataFrame({"c": grid, "Event": d["event"]["point"], "Pseudo (t-24)": d["placebo"]["point"],
                    "Difference": d["ddd"]["point"],
                    "Uniform lo": d["ddd"]["lo_unif"], "Uniform hi": d["ddd"]["hi_unif"]})
cur["Band above 0"] = ["yes" if x > 0 else "no" for x in d["ddd"]["lo_unif"]]
show(cur.round(4), "Panel B. Collapse-probability curve (probability points)")
print("Uniform-significant thresholds:", d["ddd_sig_region_uniform"])
print("Joint max-|t| adjusted p:", d["joint_multiplicity"], "\\n")

rows = []
for k, lab in (("A_pooled_cluster","Pooled 4 pseudo-dates, firm-clustered"),
               ("B_t24_cluster","t-24 only, firm-clustered"),
               ("C_common_pooled_cluster","Common sample (event + all 4 dates)")):
    r = c3[k]
    rows.append((lab, r["n_event"], r["n_placebo"],
                 f"{r['p10']['obs']:+.4f}", f"[{r['p10']['ci'][0]:+.4f}, {r['p10']['ci'][1]:+.4f}]",
                 f"{r['mean']['obs']:+.4f}", f"{r['median']['obs']:+.4f}"))
show(pd.DataFrame(rows, columns=["Contrast","n event","n pseudo","p10 diff","95% CI","mean diff","median diff"]),
     "Panel A. Event vs. pseudo-event quantile contrasts")'''))
c1.append((["## Table 5 — Recipients vs. non-recipients in the same measured distress state"],
'''b = A("wp12b")["runs"]
def row(key, lab):
    r = b[key]
    return (lab, r.get("n_treated",""), r.get("n_ctrl_events",""),
            f"{r['mean']['obs']:+.4f} [{r['mean']['ci'][0]:+.4f}, {r['mean']['ci'][1]:+.4f}]",
            f"{r['median']['obs']:+.4f} [{r['median']['ci'][0]:+.4f}, {r['median']['ci'][1]:+.4f}]",
            f"{r['p10']['obs']:+.4f} [{r['p10']['ci'][0]:+.4f}, {r['p10']['ci'][1]:+.4f}]")
rows = [row("B_distress_1","Distressed stratum"), row("B_distress_0","Non-distressed stratum")]
p = b["E_pool_distress"]
rows.append(("Pooled (recipient weights)", p["n_treated"], "",
             f"{p['mean']['obs']:+.4f} [{p['mean']['ci'][0]:+.4f}, {p['mean']['ci'][1]:+.4f}]",
             f"{p['median']['obs']:+.4f} [{p['median']['ci'][0]:+.4f}, {p['median']['ci'][1]:+.4f}]",
             f"{p['p10']['obs']:+.4f} [{p['p10']['ci'][0]:+.4f}, {p['p10']['ci'][1]:+.4f}]"))
show(pd.DataFrame(rows, columns=["Stratum","n recipients","n non-recipient events","Mean","Median","p10"]), "Table 5")

d1 = b["B_distress_1"]
print("Distressed stratum, P(outcome <= c):")
print("  recipients        ", d1["cprob_treated"])
print("  weighted non-recip", d1["cprob_ctrl_w"])
print("  thresholds with uniform band above zero:", len(d1["curve"]["sig_region"]), "of", len(d1["curve"]["grid"]))
bal = A("wp12c_balance")["runs"]["B_distress_1"]
print("\\nBalance after weighting — by covariate:", bal["smd_by_covariate"])
print("Worst covariate:", bal["worst_covariate"], "| max |SMD| =", bal["max_abs_smd"])
print("Weight diagnostics:", bal["weight_diagnostics"])'''))
build(f"{NB}/01_main_tables.ipynb","# P-016 — Main tables (Tables 1–5)",INTRO_COMMON,c1)
