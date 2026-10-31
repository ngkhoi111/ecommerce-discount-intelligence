"""Explain behavior with held-out aggregates and validation-only importance."""
import json
import numpy as np
import joblib
from sklearn.inspection import permutation_importance
from threadpoolctl import threadpool_limits
from src.pipeline import FEATURES, connect

def insights(root):
    con=connect(root)
    # Disjoint within each segmentation; counts are not additive across dimensions.
    segments=con.execute("""
      WITH segments AS (
        SELECT 'Prior observed purchases' AS dimension,
          CASE WHEN user_buy_events=0 THEN '0 purchases'
               WHEN user_buy_events<=2 THEN '1-2 purchases' ELSE '3+ purchases' END AS segment,
          purchased_7d FROM features WHERE split='test'
        UNION ALL
        SELECT 'Cart activity in first 24 hours',
          CASE WHEN product_cart_events_24h=1 THEN 'One cart event' ELSE 'Repeated cart events' END,
          purchased_7d FROM features WHERE split='test'
        UNION ALL
        SELECT 'Observed purchase recency',
          CASE WHEN user_buy_events=0 THEN 'No observed prior purchase'
               WHEN days_since_buy<=7 THEN 'Within 7 days'
               WHEN days_since_buy<=30 THEN '8-30 days' ELSE 'Over 30 days' END,
          purchased_7d FROM features WHERE split='test'
      )
      SELECT dimension,segment,count(*) AS journeys,sum(purchased_7d) AS purchasers,
             avg(purchased_7d) AS purchase_rate
      FROM segments GROUP BY dimension,segment ORDER BY dimension,segment
    """).fetchdf()
    segments.to_csv(root/'reports/behavior_segments.csv',index=False)
    columns=','.join(FEATURES+['purchased_7d'])
    val=con.execute(f"SELECT {columns} FROM features WHERE split='validation' ORDER BY hash(client_id,sku) LIMIT 30000").fetchdf()
    con.close()
    artifact=joblib.load(root/'data/processed/purchase_model.joblib')
    print('Explaining the selected model on a validation-only sample ...',flush=True)
    with threadpool_limits(limits=2):
        importance=permutation_importance(artifact['model'],val[FEATURES].to_numpy(dtype=np.float64),val.purchased_7d.to_numpy(),scoring='average_precision',n_repeats=3,random_state=42,n_jobs=1)
    import pandas as pd
    pd.DataFrame({'feature':FEATURES,'average_precision_decrease':importance.importances_mean,
                  'repeat_std':importance.importances_std}).sort_values('average_precision_decrease',ascending=False).to_csv(root/'reports/validation_importance.csv',index=False)
