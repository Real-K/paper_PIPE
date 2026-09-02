# Rescue Premiums and Employment Tails — replication materials

Code and result artifacts for *Rescue Premiums and Employment Tails: Third-Party Equity Placements in Listed Korean Firms* (P-016). The paper links 415 completed third-party allotments by KOSPI/KOSDAQ-listed firms — 360 within the stated 2015–2025 window — to mandatory DART disclosures and to monthly National Pension Service payroll records.

## Start here — the notebooks render on GitHub

**Current FRL submission** (`notebooks_FRL/`): [`01_paper_FRL.ipynb`](notebooks_FRL/01_paper_FRL.ipynb) rebuilds Figure 1 and Table 1 of the FRL manuscript and asserts every printed number; [`02_appendix_FRL.ipynb`](notebooks_FRL/02_appendix_FRL.ipynb) does the same for appendix Tables A1–E1. The `notebooks/` folder below reflects the earlier full-length manuscript.

| Notebook | Contents |
|---|---|
| [`notebooks/01_main_tables.ipynb`](notebooks/01_main_tables.ipynb) | Tables 1–5 of the manuscript |
| [`notebooks/02_figures.ipynb`](notebooks/02_figures.ipynb) | Figures 1–3 |
| [`notebooks/03_appendix_tables.ipynb`](notebooks/03_appendix_tables.ipynb) | Appendix Tables A1–F1 and the robustness batteries |
| [`notebooks/04_comment_robustness.ipynb`](notebooks/04_comment_robustness.ipynb) | Referee-comment analyses (2026-09-02): sub-window tail dynamics, four-benchmark threshold grids, influence of extreme recipients, sample-selection comparison |

**Outputs are stored in the notebooks**, so every table and figure is visible on GitHub without installing anything or obtaining any data. Each notebook reads only the aggregate result artifacts in [`artifacts/`](artifacts/) — no licensed microdata is used or required.

To re-execute them yourself: Python 3.11+, `pandas`, `numpy`, `matplotlib`. Run from inside `notebooks/`.

## What is here

```
notebooks/    tables and figures, rebuilt from artifacts, with outputs stored
artifacts/    49 aggregate result files (JSON) — every number in the paper traces to one of these
code/
  pipeline/     the full analysis pipeline (requires licensed inputs; see DATA_ACCESS.md)
  verification/ two checkers run against the manuscript before submission
figures/      the vector (PDF) and raster (PNG) figures as submitted
```

## Verification

Two checks are run against the manuscript itself and are included here:

- `code/verification/wp13_verify_draft.py` — extracts every number in the manuscript and supplement and matches it against the artifact pool, with an explicit block-list for values retracted during revision.
- `code/verification/wp13_check_refs.py` — confirms that every `Section N` and `Appendix X` reference resolves to a heading that exists.

Both require the manuscript source, which is not in this repository while the paper is under review.

## Data

The disclosure-based inputs are public and reproducible from the filing identifiers; the payroll register and the commercial financial and deal databases are licensed and cannot be redistributed here. [`DATA_ACCESS.md`](DATA_ACCESS.md) states, source by source, what each contains and how to obtain it.

## Licence

Code is released under the MIT Licence (see `LICENSE`). The result artifacts are aggregate statistics derived from licensed sources and are shared for verification of the reported results.
