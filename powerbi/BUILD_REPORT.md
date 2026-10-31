# Power BI report assembly

The runnable end-to-end report is reports/dashboard.html. This folder supplies an optional native Power BI extension; no .pbix has been created.

## Import

In Power BI Desktop, choose Get data > Text/CSV and import these aggregate files from reports/: split_summary.csv, daily_journeys.csv, category_summary.csv, test_metrics.csv, validation_metrics.csv, calibration.csv, policy_segments.csv, policy_scenarios.csv. Each table is a separate analytical grain. Do not join scenario rows directly to daily journeys. Single-table visuals do not require a relationship. Never sum ratios or purchase rates; calculate sum(purchasers)/sum(journeys).

## Pages

1. Data and journeys: cards for counts; daily line chart of purchase rate with split as legend; split table. Show that dates are in 2022 and that purged journeys are excluded from modeling.
2. Model evaluation: model comparison by average precision; Brier score and log loss cards; calibration scatter with predicted and observed rates. Lower Brier/log loss is better. Validation metrics selected the model; test metrics evaluate that selection.
3. Scenario economics: single-select slicers for assumed_order_value, assumed_margin, assumed_discount, assumed_response and selective_response_multiplier. Compare contribution_per_1000 by policy. Select one combination before aggregating; adding all scenario values is invalid. Show the caption 'Simulated contribution; response and costs are assumed'.

## Example measures

```dax
Observed Purchase Rate = DIVIDE(SUM(daily_journeys[purchasers]), SUM(daily_journeys[journeys]))

Scenario Contribution per 1000 =
IF(
    HASONEVALUE(policy_scenarios[assumed_order_value]) &&
    HASONEVALUE(policy_scenarios[assumed_margin]) &&
    HASONEVALUE(policy_scenarios[assumed_discount]) &&
    HASONEVALUE(policy_scenarios[assumed_response]) &&
    HASONEVALUE(policy_scenarios[selective_response_multiplier]),
    SELECTEDVALUE(policy_scenarios[contribution_per_1000]),
    BLANK()
)
```

Use policy on the scenario visual axis so SELECTEDVALUE resolves one scenario row per bar. Keep anonymized category IDs as text labels. Price bucket IDs are not currency. Provide source and methodology links on the report.
