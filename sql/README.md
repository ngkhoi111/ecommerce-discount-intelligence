# Shopping journey SQL

`01_build_journeys.sql` is executed by the Python pipeline with the local raw path substituted. It creates deduplicated core events, first shopper-product carts, decision-time cart state, eligibility, cumulative user/SKU histories, and features with chronological split labels.

The first observed cart anchors one journey per shopper-product pair. Eligibility is evaluated 24 hours later. Purchase labels cover the next seven days, with full follow-up and a 30-day warm-up. A removal tied with the latest cart excludes the journey. Purchases at the decision exclude eligibility; purchases exactly at the seven-day endpoint count as outcomes. See docs/METHODOLOGY.md and tests/test_journeys.py.

Raw dates are cast explicitly. Histories aggregate exact timestamp ties before cumulative sums. ASOF joins select the latest history at or before the decision, and the first purchase at or after the original cart. The pipeline asserts that joins preserve one row per eligible pair and that outcome windows do not cross split boundaries.
