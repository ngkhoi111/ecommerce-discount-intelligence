"""Reproducible shopping journeys, temporal evaluation, and scenario economics."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import time
import warnings

import duckdb
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SEED = 42
FEATURES = ['product_cart_events_24h', 'user_cart_events', 'user_buy_events',
            'days_since_buy', 'observed_history_days', 'sku_cart_events',
            'sku_buy_events', 'decision_hour', 'decision_dow']

def save_json(path, value):
    path.write_text(json.dumps(value, indent=2, default=str, allow_nan=False), encoding='utf-8')

def connect(root):
    processed = root/'data/processed'
    processed.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(processed/'analytics.duckdb'))
    con.execute("SET threads=2")
    con.execute("SET memory_limit='3GB'")
    temp = str(processed/'duckdb_tmp').replace("'", "''")
    con.execute(f"SET temp_directory='{temp}'")
    return con

def extract(root):
    start = time.time()
    raw = root/'data/raw'
    expected = ['add_to_cart', 'product_buy', 'remove_from_cart', 'product_properties', 'page_visit', 'search_query']
    for name in expected:
        if not (raw/f'{name}.parquet').exists():
            raise FileNotFoundError(f'Missing {name}.parquet in {raw}')
    con = connect(root)
    manifest = []
    for name in expected:
        path = raw/f'{name}.parquet'
        digest = hashlib.sha256()
        with path.open('rb') as f:
            for chunk in iter(lambda: f.read(8*1024*1024), b''):
                digest.update(chunk)
        src = str(path).replace("'", "''")
        n = con.execute(f"SELECT count(*) FROM read_parquet('{src}')").fetchone()[0]
        manifest.append({'file':path.name,'rows':n,'bytes':path.stat().st_size,'sha256':digest.hexdigest()})
        print(f'Source verified: {name}: {n:,} rows', flush=True)
    source_events = sum(x['rows'] for x in manifest if x['file'] != 'product_properties.parquet')
    if source_events < 200_000:
        raise ValueError('At least 200,000 source events required.')
    sql = (root/'sql/01_build_journeys.sql').read_text(encoding='utf-8').replace('{{RAW}}',str(raw).replace('\\','/').replace("'", "''"))
    for statement in re.split(r';\s*(?:\n|$)', sql):
        if not statement.strip():
            continue
        match = re.search(r'CREATE OR REPLACE TABLE (\w+)',statement)
        print('Building '+(match.group(1) if match else 'SQL step')+' ...',flush=True)
        con.execute(statement)
    counts = {name:con.execute(f'SELECT count(*) FROM {name}').fetchone()[0]
              for name in ['carts','buys','removals','first_carts','eligible','features']}
    if counts['carts'] + counts['buys'] + counts['removals'] < 200_000:
        raise ValueError('Fewer than 200,000 cleaned core events.')
    assert counts['eligible'] == counts['features'], 'History joins multiplied journeys'
    assert con.execute('SELECT count(*) FROM (SELECT client_id,sku FROM features GROUP BY 1,2 HAVING count(*)>1)').fetchone()[0] == 0
    assert con.execute('SELECT count(*) FROM features WHERE user_cart_events IS NULL OR sku_cart_events IS NULL OR days_since_buy<0 OR observed_history_days<0').fetchone()[0] == 0
    assert con.execute("SELECT count(*) FROM features WHERE (split='train' AND outcome_end >= TIMESTAMP '2022-09-15') OR (split='validation' AND outcome_end >= TIMESTAMP '2022-10-15')").fetchone()[0] == 0
    coverage=con.execute('SELECT * FROM coverage').fetchone()
    splits=con.execute('SELECT split,count(*) AS journeys,sum(purchased_7d) AS purchasers,avg(purchased_7d) AS purchase_rate,min(decision_time) AS first_decision,max(decision_time) AS last_decision FROM features GROUP BY split ORDER BY first_decision').fetchdf()
    assert all(s in set(splits['split']) for s in ['train','validation','test'])
    splits.to_csv(root/'reports/split_summary.csv',index=False)
    daily=con.execute("SELECT CAST(decision_time AS DATE) AS decision_date,split,count(*) AS journeys,sum(purchased_7d) AS purchasers,avg(purchased_7d) AS purchase_rate FROM features GROUP BY 1,2 ORDER BY 1").fetchdf()
    daily.to_csv(root/'reports/daily_journeys.csv',index=False)
    props=str(raw/'product_properties.parquet').replace("'", "''")
    assert con.execute(f"SELECT count(*)-count(DISTINCT sku) FROM read_parquet('{props}')").fetchone()[0] == 0
    categories=con.execute(f"SELECT coalesce(cast(p.category AS VARCHAR),'unknown') AS category,count(*) AS journeys,sum(f.purchased_7d) AS purchasers,avg(f.purchased_7d) AS purchase_rate FROM features f LEFT JOIN read_parquet('{props}') p USING (sku) WHERE f.split='test' GROUP BY 1 HAVING count(*) >= 100 ORDER BY journeys DESC LIMIT 100").fetchdf()
    categories.to_csv(root/'reports/category_summary.csv',index=False)
    target=str(root/'data/processed/journeys.parquet').replace("'", "''")
    con.execute(f"COPY features TO '{target}' (FORMAT PARQUET, COMPRESSION ZSTD)")
    audit={'source_events':source_events,'manifest':manifest,'counts':counts,
           'cleaned_core_events':counts['carts']+counts['buys']+counts['removals'],
           'observation_start':coverage[0],'observation_end':coverage[1],
           'eligible_shoppers':con.execute('SELECT count(DISTINCT client_id) FROM features').fetchone()[0],
           'elapsed_seconds':round(time.time()-start,1)}
    save_json(root/'reports/pipeline_audit.json',audit)
    con.close()
    print(splits.to_string(index=False),flush=True)

def metrics(y,p):
    from sklearn.metrics import average_precision_score,roc_auc_score,brier_score_loss,log_loss
    n=max(1,int(np.ceil(len(y)*.2)))
    top=np.argsort(-p,kind='stable')[:n]
    return {'average_precision':float(average_precision_score(y,p)),
            'roc_auc':float(roc_auc_score(y,p)), 'brier_score':float(brier_score_loss(y,p)),
            'log_loss':float(log_loss(y,p,labels=[0,1])),
            'top20_purchase_capture':float(n/len(y) if np.ptp(p)==0 else y[top].sum()/max(y.sum(),1))}

def model(root):
    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import FunctionTransformer, StandardScaler
    from sklearn.calibration import calibration_curve
    import joblib
    con=connect(root)
    columns=','.join(FEATURES+['purchased_7d','split'])
    frames={s:con.execute(f"SELECT {columns} FROM features WHERE split='{s}' ORDER BY decision_time,client_id,sku").fetchdf() for s in ['train','validation','test']}
    if len(frames['train'])>500_000:
        frames['train']=frames['train'].sample(n=500_000,random_state=SEED)
    train,val,test=[frames[s] for s in ['train','validation','test']]
    for frame in frames.values():
        if not np.isfinite(frame[FEATURES].to_numpy()).all():
            raise ValueError('Features contain missing or infinite values')
        if frame.purchased_7d.nunique()!=2:
            raise ValueError('Every split requires both outcome classes')
    xtrain=train[FEATURES].to_numpy(dtype=np.float64)
    ytrain=train.purchased_7d.to_numpy()
    xval=val[FEATURES].to_numpy(dtype=np.float64)
    yval=val.purchased_7d.to_numpy()
    xtest=test[FEATURES].to_numpy(dtype=np.float64)
    ytest=test.purchased_7d.to_numpy()
    models={
      'logistic_regression':make_pipeline(FunctionTransformer(np.log1p),StandardScaler(),LogisticRegression(max_iter=400,C=1.0,random_state=SEED)),
      'gradient_boosting':HistGradientBoostingClassifier(max_iter=100,max_leaf_nodes=15,learning_rate=.08,l2_regularization=5,early_stopping=False,random_state=SEED)
    }
    validation=[]
    for name,estimator in models.items():
        print(f'Training {name} on {len(train):,} journeys ...',flush=True)
        # Limit native parallelism to keep a personal computer responsive.
        from threadpoolctl import threadpool_limits
        with threadpool_limits(limits=2):
            estimator.fit(xtrain,ytrain)
            p=estimator.predict_proba(xval)[:,1]
        validation.append({'model':name,**metrics(yval,p)})
    selected=max(validation,key=lambda m:m['average_precision'])['model']
    estimator=models[selected]
    print(f'Validation selected {selected}; scoring untouched test period ...',flush=True)
    with threadpool_limits(limits=2):
        ptest=estimator.predict_proba(xtest)[:,1]
    prevalence=float(ytrain.mean())
    baseline=np.full(len(test),prevalence)
    test_metrics=[{'model':'constant_baseline',**metrics(ytest,baseline)}, {'model':selected,**metrics(ytest,ptest)}]
    pd.DataFrame(validation).to_csv(root/'reports/validation_metrics.csv',index=False)
    pd.DataFrame(test_metrics).to_csv(root/'reports/test_metrics.csv',index=False)
    observed,predicted=calibration_curve(ytest,ptest,n_bins=10,strategy='quantile')
    pd.DataFrame({'predicted_probability':predicted,'observed_purchase_rate':observed}).to_csv(root/'reports/calibration.csv',index=False)
    # Save only anonymous outcome/score arrays locally; no shopper identifiers published.
    pd.DataFrame({'purchased_7d':ytest,'probability':ptest}).to_parquet(root/'data/processed/test_scores.parquet',index=False)
    joblib.dump({'model':estimator,'features':FEATURES,'seed':SEED},root/'data/processed/purchase_model.joblib')
    rng=np.random.default_rng(SEED)
    n=len(test); budget=int(np.ceil(n*.2))
    low=np.argsort(ptest,kind='stable')[:budget]
    random=rng.choice(n,size=budget,replace=False)
    policies=[('no_new_offers',0,0),('blanket',n,int(ytest.sum())),
              ('random_20pct',budget,int(ytest[random].sum())),
              ('selective_20pct',budget,int(ytest[low].sum()))]
    policy_summary=[{'policy':name,'contacts':contacts,'observed_buyers_contacted':buyers,
                    'observed_nonbuyers_contacted':contacts-buyers} for name,contacts,buyers in policies]
    pd.DataFrame(policy_summary).to_csv(root/'reports/policy_segments.csv',index=False)
    rows=[]
    for value in [50.,100.,150.]:
      for margin in [.2,.35,.5]:
       for discount in [.05,.1,.15]:
        for response in [0.,.01,.03,.05,.1]:
         for factor in [0.,.25,1.]:
          for name,contacts,buyers in policies:
           effective=response*(factor if name=='selective_20pct' else 1.)
           incremental=-buyers*value*discount+(contacts-buyers)*effective*value*(margin-discount)-contacts*.05
           contribution=int(ytest.sum())*value*margin+incremental
           rows.append({'policy':name,'assumed_order_value':value,'assumed_margin':margin,'assumed_discount':discount,'assumed_response':response,'selective_response_multiplier':factor,'contact_cost':.05,'contacts':contacts,'expected_incremental_contribution':incremental,'contribution_per_1000':contribution/n*1000,'incremental_per_1000':incremental/n*1000})
    scenarios=pd.DataFrame(rows)
    scenarios.to_csv(root/'reports/policy_scenarios.csv',index=False)
    central=scenarios[(scenarios.assumed_order_value==100)&(scenarios.assumed_margin==.35)&(scenarios.assumed_discount==.1)&(scenarios.selective_response_multiplier==1)]
    central.to_csv(root/'reports/central_scenarios.csv',index=False)
    summary={'selected_model':selected,'training_sample':len(train),'validation_journeys':len(val),
             'test_journeys':n,'test_buyers':int(ytest.sum()),'test_purchase_rate':float(ytest.mean()),
             'training_prevalence':prevalence,'validation':validation,'test':test_metrics,
             'policy_segments':policy_summary,'seed':SEED,
             'primary_scenario_assumptions':{'order_value':100,'margin':.35,'discount':.1,'contact_cost':.05},
             'warning':'Purchase propensity does not identify coupon response. Financial outputs are simulations, not realized profit.'}
    save_json(root/'reports/model_summary.json',summary)
    # Daily/group output contains no raw client or SKU identifiers.
    con.close()
    print(json.dumps(summary,indent=2),flush=True)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage',choices=['journeys','model','report','all'],default='all')
    parser.add_argument('--root',type=Path,default=ROOT)
    args=parser.parse_args()
    root=args.root.resolve()
    (root/'reports').mkdir(exist_ok=True)
    if args.stage in ['journeys','all']: extract(root)
    if args.stage in ['model','all']: model(root)
    if args.stage in ['report','all']:
        from src.reporting import report
        report(root)

if __name__=='__main__':
    main()
