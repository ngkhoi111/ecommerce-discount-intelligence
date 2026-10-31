# Project guide

## 1 Verify the dataset

Run the audit before modeling. Inspect file counts, columns, row counts, actual timestamps, missing IDs, and event coverage. The audit scans full files and may take time. It does not extract archives. Confirm at least 200,000 usable events after cleaning; raw rows alone do not meet that requirement. Record source URL, download date, license, file checksums, and date coverage. Do not use price bucket IDs as money.

## 2 Define journeys

Write the exact unit of analysis in sql/README.md. Begin with user-product pairs and specify how repeated cart additions reset or preserve a journey, how cart removals affect eligibility, and how purchases close journeys. A missing purchase is an observed nonpurchase within a window, not proof of lost revenue. Avoid incomplete seven-day outcome windows and duplicate eligible journeys.

## 3 Analyze behavior with SQL

Measure natural return purchasing, time to purchase, history, category, and price-bucket patterns. Report denominators and uncertainty. Check whether prices are ordered buckets and how anonymous categories limit interpretation. Reconcile event totals before and after joins to detect multiplication of rows.

## 4 Predict later purchases

Start with a constant prevalence baseline and a transparent logistic regression. Add complexity only if it improves holdout performance. Features stop at the 24-hour decision. Split by decision time, purge overlapping outcome windows, and retain a final untouched test period. Quantify average precision and calibration; accuracy alone is inadequate for rare outcomes. Repeated shoppers may appear across time splits if that matches the proposed deployment; report this choice.

## 5 Simulate discount decisions

Use explicit assumptions for currency value, cost margin, discount cost, contact cost, and incremental response. State that coupon exposure and product costs are absent. Model both discounts to existing buyers and incremental buyers. Compare policies on identical eligible populations and budgets. Vary coupon responsiveness independently of purchase propensity, include zero-response scenarios, and publish break-even conditions. Never optimize the policy on the final test set.

## 6 Present the business decision

Create Power BI pages for data quality, shopper journeys, model evaluation, and scenario economics. Write a short recommendation with a proposed randomized experiment and guardrails. Report actual profit only if later supported by a live experiment; otherwise use the phrase simulated contribution profit under stated assumptions.
