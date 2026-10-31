# E-commerce Discount Intelligence

## Should we send this shopper a discount or would they buy anyway

This Business Analytics project investigates shoppers who return and purchase after leaving an item in their cart. It combines SQL shopping-journey analysis, purchase prediction, and a financial simulation to inform a proposed discount-targeting experiment.

**Status: project setup. Data has not been downloaded or validated. No improvement results have been established.**

## Start here on Windows

Open PowerShell in this folder and run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1
```

Download and extract the raw **Synerise dataset** from https://recsys.synerise.com/data-set into `data/raw/`. Choose the retailer interaction dataset, not the preprocessed challenge version. Review and follow its attribution and noncommercial license requirements; do not commit the source data.

```powershell
.\.venv\Scripts\python.exe scripts\profile_data.py
.\.venv\Scripts\python.exe -m jupyterlab
```

The setup uses `requirements-lock.txt` to reproduce the verified dependency versions. VS Code is configured to use the local environment.

Open `notebooks/01_data_profile.ipynb`. Read [the project guide](docs/PROJECT_GUIDE.md) for the sequence of work.

## Data acceptance criteria

- At least 200,000 verified usable events; target several million while retaining complete user histories within the analysis window.
- Inspect actual timestamp coverage. The 2025 challenge year does not establish transaction recency.
- Confirm usable client IDs, product IDs, cart events, purchases, and enough follow-up.
- The candidate covers six months according to its publisher. Product prices are bucket IDs, not currency amounts. Verify bucket ordering before treating IDs as numerical prices.
- A purchase without an observed offer is not proof that no offer occurred: promotion exposure is unobserved.

## Planned decision and evaluation

At 24 hours after an eligible cart addition, identify user-product journeys without a matching purchase. Predict a matching purchase in the following seven days using only information available at the decision time. Define repeat cart additions, removals, purchases, and overlapping journeys explicitly before implementation.

Split chronologically and purge training labels that overlap validation or test periods. Require complete outcome windows and compare against a simple baseline. Report average precision, calibration, and purchase capture at a fixed targeting budget.

Simulate blanket, delayed, and selective offers under stated price, margin, response, and delivery-cost assumptions. Report modeled contribution profit and sensitivity, including conditions where targeting loses. Purchase propensity is not incremental coupon response. A live randomized experiment is required to establish actual business uplift.

## Repository layout

```text
data/raw/          Local source files, ignored by Git
data/processed/    Local derived files, ignored by Git
notebooks/         Guided exploration
scripts/           Environment setup and full-file audit
sql/               Journey definitions and SQL analysis
src/               Reusable analysis code
reports/           Generated audits and final findings
powerbi/           Dashboard files and notes
docs/              Analysis plan and metric definitions
```

## Expected outputs

Verified data audit, reproducible SQL journeys, chronological model evaluation, policy simulation, Power BI report, and a recommendation memo. Publish actual counts and measured results only after verification. Do not describe simulated improvement as realized revenue or profit.

## Sources

- Dataset and schema: https://recsys.synerise.com/data-set
- Challenge: https://www.recsyschallenge.com/2025/
