# Data access

None of the four primary sources can be redistributed in this repository. Two are licensed; two are public but bulk-download restricted. This file states what each contains, what it is used for, and how to obtain it.

| Source | Used for | Redistributable here | How to obtain |
|---|---|---|---|
| **National Pension Service establishment register** (monthly, firm level) | The employment outcome: monthly headcount, new enrolments (hires) and losses (separations) by business-registration number | **No** — licensed microdata | Korean National Pension Service public-data portal, under its data-use terms |
| **DART electronic disclosures** (Financial Supervisory Service) | Treatment identification, event dates, allotment method, new and pre-issue share counts, stated use of proceeds, payment dates, structural-change filings | **Not in bulk** — but each filing is individually public | DART OpenAPI (`opendart.fss.or.kr`) with a free API key; every filing cited in the paper is identified by its receipt number in the analysis code |
| **KRX adjusted price series** | Announcement CARs and twelve-month BHARs | **No** — vendor file | Korea Exchange, or any vendor carrying KRX adjusted prices |
| **Commercial Korean financial-statement and deal databases** | Leverage, ROA, cash, capital impairment, loss flags; allottee identity and deal size | **No** — licensed | The respective vendors |

## What *is* here instead

`artifacts/` holds 47 aggregate result files. They contain estimates, confidence intervals, sample counts, balance diagnostics and curve grids — the quantities reported in the paper — and no firm identifiers. Every table and figure in the paper is rebuilt from these files by the notebooks, so the reported results can be checked without any licensed input.

Firm-level derived files (business numbers, tickers, headcounts, per-firm outcomes) are **deliberately excluded** from this repository because they are derived from the licensed register and would identify individual employers.

## Reproducing from raw data

`code/pipeline/` contains the complete pipeline. With the four sources in place and `BASE` pointed at the project root, it rebuilds every artifact in `artifacts/`. Scripts are numbered by work package; `rerun_*.py` are the copies used for the final re-execution on the harmonised treatment universe (2015–2025 window enforced in code, employment sample fixed at 210 firms, clean listed control pool).
