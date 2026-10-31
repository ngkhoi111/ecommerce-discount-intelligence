# Analysis definitions

## Decision and population

One journey is the first observed add-to-cart for a shopper and SKU within the available window. Later carts for that same pair do not create additional journeys. This conservative first-journey definition avoids overlapping outcomes but does not represent every repeat-shopping opportunity. Allow 30 days of observed history before the first eligible cart; history before the dataset is unknown.

The decision occurs 24 hours after the first cart. Exclude pairs with a purchase at or before the decision and on or after the cart. At decision time, the last cart must be later than the last removal, or no removal must exist. A cart and removal tied at exactly the same timestamp are conservatively treated as removed. Require seven full days of follow-up to a common source endpoint. Include purchases strictly after the decision through the inclusive seven-day endpoint. This measures observed return purchasing, not verified purchases without promotions: historical offer exposure is unknown.

Exact duplicate shopper-SKU-timestamp events within each event type are collapsed. They may represent repeated units; these records lack quantity, so the project analyzes events and binary outcomes rather than item quantities or revenue. Page visits and searches are inventoried but not used in this first model; URLs cannot be mapped reliably to product IDs from the provided fields. Product metadata is used for descriptive reporting only. Anonymous price bucket IDs are never treated as dollar amounts or ordered prices.

## Features and chronology

Only cart and purchase histories at or before the decision are used: user and SKU cumulative counts, user purchase recency, observed history length, cart activity in the first 24 hours, and decision hour/day. Exact timestamp ties are aggregated before cumulative windows. No future review, outcome, future interaction, user ID, or SKU ID is fed to the model.

Training decisions have outcome endpoints before September 15, 2022. Validation decisions start September 15 and end early enough for outcomes before October 15. Test decisions start October 15, with full follow-up. Seven-day purge gaps separate decision periods. The validation period selects between logistic regression and gradient boosting; the selected fitted model is not refitted using test information. Training is uniformly sampled to at most 500,000 journeys with a fixed seed if necessary, retaining the observed class distribution. All validation and test journeys are scored.

Repeated shoppers and products can appear in successive periods, consistent with deployment to existing shoppers. Counts include the current cart. Product properties are descriptive snapshots, not assumed historically available predictors. Interactions prior to the dataset are missing. Historical offers, channel, device, inventory, stockouts, marketing acquisition, consent, currency prices and product costs are unavailable.

## Evaluation

Compare average precision, ROC-AUC, Brier score and log loss against a constant training-prevalence prediction. Average precision is the primary validation selection metric. Report reliability bins and return-purchase capture among the highest-propensity 20 percent. A low-propensity segment is not necessarily coupon-responsive. No causal treatment-effect or real profit claim is supported.

## Financial scenarios

Each eligible journey is a single hypothetical unit with an assumed $100 full-price order value, 35 percent pre-discount contribution margin, 10 percent discount and $0.05 contact cost. These are illustrative assumptions, not observed financials. Incremental response r is the assumed fraction of otherwise nonpurchasing journeys persuaded by a coupon.

For a targeted journey with held-out observed outcome y, contribution without an offer is y * V * m. Expected contribution with an offer is y * V * (m-d) + (1-y) * r * V * (m-d) - contact_cost. Incremental contribution is -y * V * d + (1-y) * r * V * (m-d) - contact_cost. Thus the model explicitly pays discount costs for shoppers who would have bought and only assumes benefits for incremental buyers. Historical outcomes are used as a proxy for no-new-intervention behavior, not verified untreated potential outcomes.

Compare no new offers, blanket offers, seeded random offers to 20 percent, and offers to the lowest-propensity 20 percent. Show zero through high response assumptions and alternative margins/discounts; do not infer r from this dataset. Report contribution per 1,000 eligible journeys, number contacted, and relative/absolute changes versus blanket offers. Unequal contact counts are part of the blanket versus targeted comparison; random versus targeted holds the budget fixed. A delayed intervention needs a different decision cohort and is reserved for later work.

## Proposed experiment

Among consenting eligible shoppers, randomize within propensity bands to no new offer or the same coupon, with a prespecified seven-day outcome and contribution margin net of discount, contact cost and returns. Log assignment, delivery, redemption, actual prices, costs and competing campaigns. Use intention-to-treat estimation, customer-level assignment to prevent cross-journey interference, and guardrails for opt-outs, discount dependence and margin. Estimate sample size from pilot variance and a prespecified minimum worthwhile effect before launch. No experiment has been run.
