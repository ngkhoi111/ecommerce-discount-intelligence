"""Create an offline dashboard and an evidence-based project memo."""
import base64
import html
import json
from pathlib import Path
import numpy as np
import pandas as pd

def report(root):
    from src.insights import insights
    insights(root)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    reports=root/'reports'
    audit=json.loads((reports/'pipeline_audit.json').read_text(encoding='utf-8'))
    summary=json.loads((reports/'model_summary.json').read_text(encoding='utf-8'))
    metrics=pd.read_csv(reports/'test_metrics.csv')
    calibration=pd.read_csv(reports/'calibration.csv')
    daily=pd.read_csv(reports/'daily_journeys.csv',parse_dates=['decision_date'])
    splits=pd.read_csv(reports/'split_summary.csv')
    central=pd.read_csv(reports/'central_scenarios.csv')
    segments=pd.read_csv(reports/'behavior_segments.csv')
    importance=pd.read_csv(reports/'validation_importance.csv')
    base,selected=summary['test']
    ap_relative=(selected['average_precision']/base['average_precision']-1)*100
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(1,2,figsize=(11,4),layout='constrained')
    axes[0].bar(['Constant baseline','Selected model'],[base['average_precision'],selected['average_precision']],color=['#9ba9ba','#177d9a'],width=.55)
    axes[0].set(title='Purchase ranking on the later test period',ylabel='Average precision')
    for i,v in enumerate([base['average_precision'],selected['average_precision']]):
        axes[0].text(i,v,f'{v:.4f}',ha='center',va='bottom')
    axes[0].set_ylim(0,max(selected['average_precision'],base['average_precision'])*1.2)
    axes[1].plot([0,1],[0,1],color='#9ba9ba',linestyle='--',label='Perfect calibration')
    axes[1].plot(calibration.predicted_probability,calibration.observed_purchase_rate,'o-',color='#177d9a',label='Selected model')
    axes[1].set(title='Do probabilities match observed outcomes?',xlabel='Mean predicted probability',ylabel='Observed purchase rate')
    high=max(calibration.predicted_probability.max(),calibration.observed_purchase_rate.max())*1.15
    axes[1].set_xlim(0,high);axes[1].set_ylim(0,high);axes[1].legend(frameon=False)
    chart=reports/'model_evaluation.png'
    fig.savefig(chart,dpi=160,facecolor='white');plt.close(fig)
    fig,ax=plt.subplots(figsize=(11,3.5),layout='constrained')
    colors={'train':'#177d9a','validation':'#b77723','test':'#643da6','purged':'#b6bdc9'}
    for split,group in daily.groupby('split'):
        ax.plot(group.decision_date,group.purchase_rate*100,'.',markersize=3,color=colors[split],label=split)
    ax.set(title='Observed return purchasing across decision dates',ylabel='Seven-day purchase rate (%)',xlabel='Decision date in 2022')
    ax.legend(ncol=4,frameon=False)
    fig.savefig(reports/'journey_trend.png',dpi=160,facecolor='white');plt.close(fig)
    primary=central[np.isclose(central.assumed_response,.03)].set_index('policy')
    gain=float(primary.loc['selective_20pct','contribution_per_1000']-primary.loc['blanket','contribution_per_1000'])
    relative=gain/abs(float(primary.loc['blanket','contribution_per_1000']))*100 if primary.loc['blanket','contribution_per_1000']!=0 else None
    state={'n':summary['test_journeys'],'buyers':summary['test_buyers'],'policies':summary['policy_segments']}
    figures=[]
    for name in ['model_evaluation.png','journey_trend.png']:
        encoded=base64.b64encode((reports/name).read_bytes()).decode()
        figures.append(f'<img class="chart" alt="{name.replace("_"," ")}" src="data:image/png;base64,{encoded}">')
    template='''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>E-commerce Discount Intelligence</title>
<style>
:root{font-family:Segoe UI,Arial,sans-serif;color:#17263b;background:#f2f5f8}*{box-sizing:border-box}body{margin:0}main{max-width:1160px;margin:auto;padding:44px 28px}header{border-bottom:2px solid #177d9a;padding-bottom:24px}h1{font-size:38px;letter-spacing:-1px;max-width:850px;line-height:1.15}h2{font-size:24px;margin-top:32px}p{line-height:1.65;max-width:950px}.eyebrow{color:#177d9a;font-weight:700;letter-spacing:2px;font-size:12px}.lead{font-size:19px;color:#43546a}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin:25px 0}.stat{background:white;padding:22px;border:1px solid #dce3ea;border-radius:10px}.number{font-size:30px;font-weight:700;display:block}.label{color:#52647b;font-size:13px}.section{background:white;padding:26px;border:1px solid #dce3ea;border-radius:10px;margin:20px 0}.note{color:#705115;background:#fff5de;padding:14px 18px;border-radius:6px}.chart{display:block;width:100%;height:auto;margin:20px 0}table{border-collapse:collapse;width:100%;font-size:14px}th,td{text-align:right;padding:12px 9px;border-bottom:1px solid #e0e7ee}th:first-child,td:first-child{text-align:left}th{color:#52647b}label{font-size:13px;color:#52647b;display:block}input{display:block;width:100%;padding:10px;border:1px solid #bccbd8;border-radius:5px;margin-top:6px;font-size:16px}.controls{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin:20px 0}.best{background:#edf8f4;font-weight:600}a{color:#126a87}footer{font-size:12px;color:#52647b;margin-top:35px}.scroll{overflow:auto}@media(max-width:700px){main{padding:25px 14px}h1{font-size:29px}.grid,.controls{grid-template-columns:1fr}.section{padding:16px}}
</style></head><body><main>
<header><div class="eyebrow">RETAIL ANALYTICS / HISTORICAL CASE STUDY</div><h1>Should we send this shopper a discount—or would they buy anyway?</h1><p class="lead">Observed shopping behavior, a tested purchase-ranking model, and an adjustable financial scenario. No live coupon experiment has been conducted.</p></header>
<div class="grid"><div class="stat"><span class="number">__EVENTS__</span><span class="label">Cleaned cart, purchase and removal events analyzed</span></div><div class="stat"><span class="number">__JOURNEYS__</span><span class="label">Eligible first shopper–product journeys</span></div><div class="stat"><span class="number">__TEST_RATE__</span><span class="label">Observed seven-day purchase rate in test</span></div></div>
<div class="note"><b>What the evidence supports:</b> purchase propensity and observed return behavior. Promotion exposure and coupon response are unknown. Financial results below are simulated using explicit assumptions.</div>
<section class="section"><h2>1. Define the decision before predicting it</h2><p>Start with the first observed cart for each shopper–product pair. Wait 24 hours; exclude pairs already purchased or currently removed. Observe purchases for seven more days. Require 30 days of warm-up and full follow-up. Repeated journeys for the same pair are excluded.</p><p>The dataset records June–December <b>2022</b> activity. “RecSys 2025” is the challenge release label. Of __SOURCE_EVENTS__ source events, this model uses cart and purchase histories; cart removals establish eligibility. Page visits and searches are inventoried but excluded from predictors.</p><div class="scroll">__SPLITS__</div>__TREND__</section>
<section class="section"><h2>2. Evaluate on later shoppers’ decisions</h2><p>The selected model is <b>__MODEL__</b>, chosen on validation average precision. Training outcomes end before validation begins, and validation outcomes end before test decisions begin. Shopper IDs, product IDs and future behavior are excluded from predictors.</p><div class="scroll">__METRICS__</div>__MODEL_CHART__<p>The selected model’s average precision differs from the constant baseline by <b>__AP_GAIN__%</b> on the test period. This is a ranking result, not a sales or profit uplift. Calibration must also be assessed before using the probabilities for decisions.</p></section>
<section class="section"><h2>3. Explore the economics instead of assuming the answer</h2><p>Target the lowest purchase-propensity 20%, compare with random targeting at the same contact count, blanket offers, and no new offers. Lower purchase propensity does not prove a shopper is persuadable. Adjust the selective response multiplier to test that risk.</p><div class="controls">
<label>Assumed order value ($)<input id="value" type="number" min="1" max="10000" step="10" value="100"></label>
<label>Pre-discount contribution margin (%)<input id="margin" type="number" min="0" max="100" step="1" value="35"></label>
<label>Discount (% of full price)<input id="discount" type="number" min="0" max="100" step="1" value="10"></label>
<label>Response among otherwise nonbuyers (%)<input id="response" type="number" min="0" max="100" step="0.5" value="3"></label>
<label>Selective response multiplier<input id="factor" type="number" min="0" max="2" step="0.1" value="1"></label>
<label>Cost per contact ($)<input id="cost" type="number" min="0" max="100" step="0.01" value="0.05"></label>
</div><p id="scenario-note" aria-live="polite"></p><div class="scroll"><table><thead><tr><th>Policy</th><th>Contacts</th><th>Existing buyers contacted</th><th>Contribution / 1,000 journeys</th><th>Change vs no new offers / 1,000</th></tr></thead><tbody id="policy-rows"></tbody></table></div><p id="winner" aria-live="polite"></p><p>Formula: incremental contribution = − existing buyers contacted × value × discount + nonbuyers contacted × assumed response × value × (margin − discount) − contact cost. This is a single-unit scenario using historical outcomes as a proxy for no-new-offer behavior. Actual quantities, costs, returns and historical coupons are unavailable.</p></section>
<section class="section"><h2>4. Test the recommendation in a real experiment</h2><p>Randomize consenting shoppers within propensity bands to a coupon or no new offer. Use customer-level assignment, actual contribution net of discounts and returns, and a prespecified seven-day outcome. Measure incremental profit and monitor opt-outs. Determine sample size from a pilot before launching. The historical dataset cannot establish that sending or withholding a coupon causes any improvement.</p><p>Read <a href="../docs/METHODOLOGY.md">the methodology</a> and the generated <a href="EXECUTIVE_SUMMARY.md">recommendation memo</a>. Power BI-ready aggregate tables are in this folder; no native Power BI report has been authored.</p></section>
<footer>Source: <a href="https://recsys.synerise.com/data-set">Synerise Universal Behavioral Modeling dataset</a>. Noncommercial educational portfolio analysis. Raw data and per-journey predictions stay local. Fixed random seed: 42.</footer>
</main><script>
const state=__STATE__;
const names={no_new_offers:'No new offers',blanket:'Blanket offers',random_20pct:'Random 20%',selective_20pct:'Selective 20%'};
const money=x=>new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',maximumFractionDigits:2}).format(x);
function update(){const get=id=>Number(document.getElementById(id).value);const v=get('value'),m=get('margin')/100,d=get('discount')/100,r=get('response')/100,f=get('factor'),c=get('cost');
const inputs=['value','margin','discount','response','factor','cost'].map(id=>document.getElementById(id));if(inputs.some(el=>!el.checkValidity()||el.value==='')){document.getElementById('scenario-note').textContent='Enter values within the displayed input limits.';return;}
const base=state.buyers*v*m;const rows=state.policies.map(p=>{const effective=Math.min(1,r*(p.policy==='selective_20pct'?f:1));const delta=-p.observed_buyers_contacted*v*d+p.observed_nonbuyers_contacted*effective*v*(m-d)-p.contacts*c;return {...p,delta,total:base+delta};});
const best=Math.max(...rows.map(p=>p.total));document.getElementById('policy-rows').innerHTML=rows.map(p=>`<tr class="${Math.abs(p.total-best)<1e-8?'best':''}"><td>${names[p.policy]}</td><td>${p.contacts.toLocaleString()}</td><td>${p.observed_buyers_contacted.toLocaleString()}</td><td>${money(p.total/state.n*1000)}</td><td>${money(p.delta/state.n*1000)}</td></tr>`).join('');
document.getElementById('scenario-note').textContent='Illustrative assumptions only. Response means additional buyers among historical nonbuyers, not the observed conversion rate.';
document.getElementById('winner').textContent='Highest simulated contribution under these assumptions: '+rows.filter(p=>Math.abs(p.total-best)<1e-8).map(p=>names[p.policy]).join(', ')+'. This is not evidence of actual policy uplift.';}
document.querySelectorAll('input').forEach(el=>el.addEventListener('input',update));update();
</script></body></html>'''
    behavior_html='<h3>Observed behavior in the test period</h3><p>These are associations, not causal effects. Compare rates within each dimension; do not add counts across dimensions.</p><div class="scroll">'+segments.to_html(index=False,border=0,float_format=lambda x:f'{x:.4f}')+'</div><p>Largest validation permutation-importance feature: <b>'+html.escape(str(importance.iloc[0]['feature']))+'</b>. Importance measures ranking sensitivity and does not establish causation.</p>'
    template=template.replace('<section class="section"><h2>3.','<section class="section">'+behavior_html+'</section><section class="section"><h2>3.',1)
    split_table=splits[['split','journeys','purchasers','purchase_rate']].to_html(index=False,border=0,float_format=lambda x:f'{x:.4f}')
    metric_table=metrics.to_html(index=False,border=0,float_format=lambda x:f'{x:.4f}')
    replacements={'__EVENTS__':f"{audit['cleaned_core_events']:,}",'__JOURNEYS__':f"{audit['counts']['eligible']:,}",
                  '__SOURCE_EVENTS__':f"{audit['source_events']:,}",'__TEST_RATE__':f"{summary['test_purchase_rate']:.2%}",
                  '__MODEL__':html.escape(summary['selected_model'].replace('_',' ')),
                  '__AP_GAIN__':f'{ap_relative:+.1f}','__SPLITS__':split_table,'__METRICS__':metric_table,
                  '__TREND__':figures[1],'__MODEL_CHART__':figures[0],'__STATE__':json.dumps(state)}
    for key,value in replacements.items(): template=template.replace(key,value)
    (reports/'dashboard.html').write_text(template,encoding='utf-8')
    memo=f'''# Discount targeting analysis

## Main finding

The selected {summary['selected_model'].replace('_',' ')} model achieved test average precision of {selected['average_precision']:.4f}, versus {base['average_precision']:.4f} for a constant baseline ({ap_relative:+.1f}% relative difference). The observed test purchase rate was {summary['test_purchase_rate']:.2%} across {summary['test_journeys']:,} eligible journeys. These are purchase-prediction results, not measured discount effects.

## Data and scope

The source contains {audit['source_events']:,} behavioral events. The journey pipeline directly cleans {audit['cleaned_core_events']:,} cart, purchase and removal events and produces {audit['counts']['eligible']:,} eligible first shopper-product journeys. Page visits and searches are inventoried but not model inputs. Activity is from {audit['observation_start']} through {audit['observation_end']}; the dataset was released for the 2025 challenge. A 30-day warm-up and full seven-day outcome window are required. Exact duplicate events are collapsed.

## Financial scenario

At an assumed $100 order value, 35% contribution margin, 10% discount, $0.05 contact cost, and a uniform 3% coupon response among otherwise nonbuyers, selective offers differ from blanket offers by ${gain:,.2f} in simulated contribution per 1,000 eligible journeys. This assumption-driven comparison changes the number of contacts. The random-20% policy provides an equal-contact comparator. The dashboard varies response, margins, discounts and the selected group's relative responsiveness, including zero-response conditions.

This is not realized profit. Costs, actual prices, historical promotions, stockouts, quantities and incremental response are not observed. The model predicts return purchasing, not who a coupon persuades. No-new-offer outcomes are approximated using historical outcomes under unknown existing marketing.

## Recommendation

Use the purchase-ranking model to define strata for a randomized coupon experiment. Do not deploy the simulated best policy as a proven revenue intervention. Within each propensity band, compare coupon assignment with no new offer, using consent, customer-level assignment and contribution net of actual discounts and returns. Choose a minimum worthwhile effect and determine sample size from pilot variance. Monitor margin, opt-outs and repeated discount dependence.

## Reproduce

Run `.venv/Scripts/python.exe scripts/run_pipeline.py --stage all` from the repository root. Raw data, intermediate DuckDB tables, individual scores and model artifacts remain local. Published results are aggregates. See docs/METHODOLOGY.md for exact boundaries, exclusions, feature definitions and split dates.
'''
    (reports/'EXECUTIVE_SUMMARY.md').write_text(memo,encoding='utf-8')
    print(f'Created {reports/"dashboard.html"} and recommendation memo.',flush=True)
