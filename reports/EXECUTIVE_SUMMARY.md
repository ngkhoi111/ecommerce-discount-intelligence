# Discount targeting analysis

## Main finding

The selected gradient boosting model achieved test average precision of 0.0681, versus 0.0245 for a constant baseline (+178.3% relative difference). The observed test purchase rate was 2.45% across 1,280,495 eligible journeys. These are purchase-prediction results, not measured discount effects.

## Data and scope

The source contains 225,224,262 behavioral events. The journey pipeline directly cleans 11,852,529 cart, purchase and removal events and produces 2,959,441 eligible first shopper-product journeys. Page visits and searches are inventoried but not model inputs. Activity is from 2022-06-23 00:12:25 through 2022-12-08 00:09:15; the dataset was released for the 2025 challenge. A 30-day warm-up and full seven-day outcome window are required. Exact duplicate events are collapsed.

## Financial scenario

At an assumed $100 order value, 35% contribution margin, 10% discount, $0.05 contact cost, and a uniform 3% coupon response among otherwise nonbuyers, selective offers differ from blanket offers by $-309.95 in simulated contribution per 1,000 eligible journeys. This assumption-driven comparison changes the number of contacts. The random-20% policy provides an equal-contact comparator. The dashboard varies response, margins, discounts and the selected group's relative responsiveness, including zero-response conditions.

This is not realized profit. Costs, actual prices, historical promotions, stockouts, quantities and incremental response are not observed. The model predicts return purchasing, not who a coupon persuades. No-new-offer outcomes are approximated using historical outcomes under unknown existing marketing.

## Recommendation

Use the purchase-ranking model to define strata for a randomized coupon experiment. Do not deploy the simulated best policy as a proven revenue intervention. Within each propensity band, compare coupon assignment with no new offer, using consent, customer-level assignment and contribution net of actual discounts and returns. Choose a minimum worthwhile effect and determine sample size from pilot variance. Monitor margin, opt-outs and repeated discount dependence.

## Reproduce

Run `.venv/Scripts/python.exe scripts/run_pipeline.py --stage all` from the repository root. Raw data, intermediate DuckDB tables, individual scores and model artifacts remain local. Published results are aggregates. See docs/METHODOLOGY.md for exact boundaries, exclusions, feature definitions and split dates.
