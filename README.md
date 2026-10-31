# E-commerce Discount Intelligence

## Should we send this shopper a discount or would they buy anyway

An end-to-end Business Analytics case study using SQL, Python, chronological purchase prediction, and an interactive financial scenario report. The business decision is whether to offer a coupon after a shopper leaves a product in their cart for 24 hours.

**Status: first complete pipeline run.** Historical behavior is measured; financial outputs are simulations, not actual profit gains.

## Verified results

| Evidence | Result |
|---|---:|
| Source behavioral events inventoried | 225,224,262 |
| Cleaned cart, purchase and removal events directly analyzed | 11,852,529 |
| Eligible first shopper-product journeys, including purge periods | 2,959,441 |
| Test journeys | 1,280,495 |
| Observed test return-purchase rate | 2.448% |
| Selected model test average precision | 0.06813 |
| Constant baseline test average precision | 0.02448 |
| Test ROC-AUC | 0.7351 |
| Return purchases captured by highest-scoring 20% | 50.80% |

The gradient boosting model was selected using validation average precision against a logistic regression alternative. Only the selected model and the prespecified constant baseline were evaluated on the final test period. Available training journeys number 880,660; fitting uses a fixed uniform sample of 500,000. Validation contains 494,175 journeys. Seven-day purge gaps prevent labels crossing period boundaries.

**Interpretation:** the model ranks observed return purchasers better than a constant score. It does not identify the causal effect of a coupon. Under some financial assumptions blanket offers outperform selective offers; the report shows both winning and losing conditions rather than presenting one scenario as realized uplift.

## View the work

- [Recommendation memo](reports/EXECUTIVE_SUMMARY.md)
- [Interactive offline dashboard](reports/dashboard.html): download or open this HTML file locally; GitHub's file preview does not execute the interactive controls.
- [Model evaluation chart](reports/model_evaluation.png)
- [Methodology and experiment proposal](docs/METHODOLOGY.md)
- [SQL journey pipeline](sql/01_build_journeys.sql)
- [Power BI assembly guide](powerbi/BUILD_REPORT.md): aggregate import tables are provided; no native .pbix has been authored.

## Reproduce on Windows

Python 3.11 is required. In PowerShell from the repository folder:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1
```

Download and extract the raw **Synerise dataset** from https://recsys.synerise.com/data-set into `data/raw/`. Use the raw retailer dataset, not the preprocessed competition version. Required files: add_to_cart.parquet, product_buy.parquet, remove_from_cart.parquet, product_properties.parquet, page_visit.parquet, search_query.parquet.

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_all.ps1
```

Individual stages:

```powershell
.\.venv\Scripts\python.exe scripts\profile_data.py
.\.venv\Scripts\python.exe scripts\run_pipeline.py --stage journeys
.\.venv\Scripts\python.exe scripts\run_pipeline.py --stage model
.\.venv\Scripts\python.exe scripts\run_pipeline.py --stage report
```

The SQL stage runs the full core event tables with DuckDB, uses two threads and a 3 GB memory limit, and may spill to local disk. Allow several GB of free disk space beyond the source files. Training uses at most 500,000 uniformly sampled journeys; validation and test scoring use all eligible rows. Exact dependencies are saved in requirements-lock.txt. Tests cover purchase-window boundaries, cart removal/re-add behavior, duplicate events, decision-time history, and tied baseline scores.

## How the decision is defined

Use the first observed cart for a shopper-product pair. After 24 hours, exclude products already bought or removed, allow 30 days of observation warm-up, and require seven full days of follow-up. A purchase in those seven days is the outcome. Only history available by the decision is used in predictors. Repeated journeys for the same shopper-product pair are excluded.

Source activity is from June 23 through December 8, **2022**; RecSys 2025 is the challenge label. Exact duplicate events are collapsed. Anonymous price bucket IDs are not money. Page visits and searches are counted in the source manifest but are not features in this version. The model uses cart/purchase history and decision-time attributes; removals determine eligibility.

## Financial scenarios

Compare no new offers, blanket offers, random offers to 20%, and selective offers to the lowest-propensity 20%. Vary hypothetical order values, margins, discounts, response among otherwise nonbuyers, and the selected segment's relative responsiveness. Random versus selective holds contact count fixed; blanket versus selective does not. Existing purchasers incur coupon costs in the simulation. A zero-response scenario is included.

Actual currency prices, costs, historical offer exposure and coupon response are unavailable. Historical purchases are only a proxy for no-new-intervention outcomes. A live customer-randomized experiment is required to measure actual incremental profit. See the methodology for formulas and the proposed experiment.

## Repository layout

```text
data/raw/          Original files; excluded from Git
data/processed/    DuckDB, journeys, model, individual scores; excluded from Git
docs/              Definitions, provenance and learning guide
notebooks/         Guided audits and result review
scripts/           Setup and pipeline commands
sql/               Reproducible shopping-journey transformations
src/               Modeling, explanation and reporting
reports/           Published aggregates, charts, dashboard and memo
powerbi/           Optional report assembly instructions
tests/             Boundary and evaluation checks
```

## Dataset attribution

Synerise Universal Behavioral Modeling Dataset, released for ACM RecSys Challenge 2025. Source: https://recsys.synerise.com/data-set. Publisher license: Creative Commons Attribution-NonCommercial 4.0 International. Review the original terms before reuse. Raw data is not redistributed. File checksums and row counts are recorded in reports/pipeline_audit.json. See docs/DATA_SOURCE.md.
