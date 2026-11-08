"""Generate reproducible executive summary, tables and static charts.
Run from anywhere: python scripts/generate_report.py
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.analysis import load_ads, group_summary, overall_summary, quality_report, add_ad_metrics
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

DATA=ROOT/'data/raw/conversion.csv'
OUT=ROOT/'reports'; FIG=OUT/'figures'
OUT.mkdir(exist_ok=True); FIG.mkdir(exist_ok=True)
BLUE='#5BB6E8'; ORANGE='#F3A869'; GREEN='#5BC8A5'; BG='#F8FAFC'; DARK='#173454'


def chart_setup():
    plt.rcParams.update({'font.size':10,'axes.titlesize':15,'axes.titleweight':'bold',
                         'figure.facecolor':'white','axes.spines.top':False,'axes.spines.right':False,
                         'axes.labelcolor':DARK,'text.color':DARK,'xtick.color':'#48596A','ytick.color':'#48596A',
                         'axes.titlepad':16,'savefig.bbox':'tight'})


def save(name):
    plt.tight_layout(pad=2)
    plt.savefig(FIG/name,dpi=170,facecolor='white')
    plt.close()


def build():
    if not DATA.is_file():
        raise SystemExit('Missing data/raw/conversion.csv. See data/README.md')
    chart_setup()
    data=load_ads(DATA)
    metrics=overall_summary(data)
    campaign=group_summary(data,'xyz_campaign_id').sort_values('xyz_campaign_id')
    gender=group_summary(data,'gender').sort_values('gender')
    target=group_summary(data,['age','gender']).sort_values(['age','gender'])
    interests=group_summary(data,'interest').sort_values('purchases',ascending=False)
    q=quality_report(data)
    campaign.to_csv(OUT/'campaign_summary.csv',index=False)
    gender.to_csv(OUT/'gender_summary.csv',index=False)
    target.to_csv(OUT/'audience_segments.csv',index=False)
    interests.to_csv(OUT/'interest_summary.csv',index=False)
    pd.Series(q).to_csv(OUT/'quality_metrics.csv',header=['value'])

    # Figure: campaign performance with per-campaign information and rates
    fig,(ax1,ax2)=plt.subplots(1,2,figsize=(12,4.3))
    names=campaign['xyz_campaign_id'].astype(str)
    barcolors=[BLUE,GREEN,ORANGE]
    bars=ax1.bar(names,campaign['purchases'],color=barcolors)
    ax1.bar_label(bars,padding=3)
    ax1.set_ylabel('Approved purchases')
    ax1.set_title('Confirmed purchases by campaign')
    bars2=ax2.bar(names,campaign['cost_per_purchase'],color=barcolors)
    ax2.bar_label(bars2,fmt='%.1f',padding=3)
    ax2.set_ylabel('Spend units / approved purchase')
    ax2.set_title('Cost per approved purchase')
    fig.suptitle('Campaign performance | real coursework dataset',fontsize=18,fontweight='bold')
    fig.subplots_adjust(top=.78)
    save('campaign_performance.png')

    # CTR by campaign in percent
    fig,ax=plt.subplots(figsize=(9,4.3))
    bars=ax.bar(names,campaign['ctr']*100,color=barcolors)
    ax.bar_label(bars,labels=[f'{v:.5f}%' for v in campaign['ctr']*100],padding=4)
    ax.set_ylabel('CTR (%)')
    ax.set_xlabel('XYZ campaign')
    ax.set_title('Weighted click-through rate')
    save('campaign_ctr.png')

    # distributions impressions before/after log
    fb=data.groupby('fb_campaign_id',as_index=False)['Impressions'].sum()
    fig,(ax1,ax2)=plt.subplots(1,2,figsize=(12,4.3))
    ax1.hist(fb['Impressions'],bins=30,color=BLUE,edgecolor='white')
    ax1.set_title('Raw summed impressions')
    ax1.set_xlabel('Impressions by Facebook campaign')
    ax1.set_ylabel('Frequency')
    ax2.hist(np.log(fb['Impressions'].clip(lower=1)),bins=30,color=GREEN,edgecolor='white')
    ax2.set_title('Log-transformed impressions')
    ax2.set_xlabel('ln(impressions)')
    ax2.set_ylabel('Frequency')
    save('impressions_distribution.png')

    # audience cohorts
    d=target.pivot_table(index='age',columns='gender',values='purchases',fill_value=0,observed=True).sort_index()
    fig,ax=plt.subplots(figsize=(10,4.5))
    idx=np.arange(len(d)); w=.34
    for i, gender_name in enumerate(d.columns):
        b=ax.bar(idx+(i-.5)*w,d[gender_name],width=w,label=gender_name,color=[BLUE,ORANGE][i%2])
        ax.bar_label(b,padding=2,fontsize=8)
    ax.set_xticks(idx,d.index)
    ax.set_title('Approved purchases by age and gender')
    ax.set_xlabel('Age band');ax.set_ylabel('Purchases');ax.legend(frameon=False,title='Gender')
    save('audience_segments.png')

    # CPC by gender - one ad per point, drop undefined CPC
    d=add_ad_metrics(data)
    fig,ax=plt.subplots(figsize=(10,4.5))
    for gender_name, col in [('F',ORANGE),('M',BLUE)]:
        v=d.loc[(d['gender']==gender_name) & d['cpc'].notna(),'cpc']
        ax.hist(v,bins=np.linspace(0,2.7,36),alpha=.48,label=f'{gender_name} · {len(v)} ads',color=col)
    ax.set_title('Ad-level CPC distributions by gender')
    ax.set_ylabel('Frequency');ax.set_xlabel('Cost per click (dataset units)')
    ax.legend(frameon=False)
    save('cpc_by_gender.png')

    # spend vs conversions; on log axes? use scatter with marker proportional to impressions
    fig,ax=plt.subplots(figsize=(10,4.5))
    for c,col in zip(sorted(data['xyz_campaign_id'].unique()),barcolors):
        x=data.loc[data.xyz_campaign_id==c]
        ax.scatter(x.Spent,x.Approved_Conversion,alpha=.48,s=17,color=col,label=str(c))
    ax.set_title('Spend vs. approved purchases by advertisement')
    ax.set_xlabel('Spend (dataset units)');ax.set_ylabel('Approved purchases')
    ax.legend(frameon=False,title='Campaign')
    save('spend_vs_purchases.png')

    iqr=d.cpc.quantile(.75)-d.cpc.quantile(.25)
    top=max(campaign.itertuples(index=False),key=lambda r:r.purchases)
    efficient=min(campaign.itertuples(index=False),key=lambda r:r.cost_per_purchase)
    report=f'''# Digital Advertising Campaign Analytics — Executive Insights

**Source:** user-supplied `conversion.csv` from a coursework exercise.  
**Scope:** {metrics['ads']:,} advertisement-level records, {metrics['campaigns']} XYZ campaigns, no time dimension.  
**Data currency:** unspecified; costs are displayed in *dataset monetary units*.

## Verified headline KPIs

| Metric | Result | Definition |
|---|---:|---|
| Ads | {metrics['ads']:,} | source rows |
| Impressions | {metrics['impressions']:,} | summed exposure events |
| Clicks | {metrics['clicks']:,} | summed clicks |
| Click-through rate | {100*metrics['ctr']:.5f}% | total clicks ÷ total impressions |
| Total ad spend | {metrics['spent']:,.2f} | dataset monetary units |
| Cost per click | {metrics['cpc']:.3f} | total spend ÷ clicks |
| Interested actions | {metrics['interested']:,} | `Total_Conversion` sum |
| Approved purchases | {metrics['purchases']:,} | `Approved_Conversion` sum |
| Approved purchases / clicks | {100*metrics['click_to_purchase_rate']:.2f}% | descriptive aggregate ratio |
| Cost per approved purchase | {metrics['cost_per_purchase']:.2f} | spend ÷ approved purchases |
| CPC IQR (per-ad, non-null) | {iqr:.4f} | Q3 − Q1 |

## Campaign comparisons

| XYZ campaign | Ads | Clicks | Purchases | CTR | CPC | Cost / purchase |
|---:|---:|---:|---:|---:|---:|---:|
'''
    for v in campaign.itertuples(index=False):
        report+=f'| {v.xyz_campaign_id} | {v.ads:,} | {v.clicks:,} | {v.purchases:,} | {100*v.ctr:.5f}% | {v.cpc:.2f} | {v.cost_per_purchase:.2f} |\n'
    report+=f'''
The highest **absolute count of approved purchases** is in campaign **{top.xyz_campaign_id}** ({top.purchases:,} approved purchases). Campaign **{efficient.xyz_campaign_id}** has the lowest **observed cost per approved purchase** ({efficient.cost_per_purchase:.2f} dataset units). These are descriptive comparisons, not causal estimates or proof of profitability. Campaign sizes differ greatly.

![Campaign performance](figures/campaign_performance.png)

![Campaign CTR](figures/campaign_ctr.png)

## Audience / ad distribution

![Audience](figures/audience_segments.png)

![CPC distribution](figures/cpc_by_gender.png)

![Impressions distribution](figures/impressions_distribution.png)

![Spend versus purchases](figures/spend_vs_purchases.png)

## Data-quality audit

| Check | Value |
|---|---:|
'''
    for k,v in q.items():
        report+=f'| {k.replace("_"," ").capitalize()} | {v:,} |\n'
    report+='''
**Important:** source rows can contain approved conversions with zero clicks, and conversions greater than clicks. These cases can reflect attribution/modeling quirks, definitions that differ from a strict user funnel, or source errors. We **retain and flag** them, and call clicks-to-purchases a *descriptive ratio*, not a validated individual-user conversion probability. Do not infer causality.

## Business-oriented next steps (hypotheses, not proven outcomes)

1. Investigate the data-generation and attribution logic behind click/conversion inconsistencies before making channel-allocation decisions.
2. Compare weighted campaign cost per purchase, not average ad-level CPC, and check sample sizes for low-volume cohorts.
3. Explore interests and gender/age strata with a minimum-click threshold; avoid ranking tiny groups based on noisy ratios.
4. Obtain purchase revenue, timestamps, ad objectives, and attribution windows for ROAS, time trends, controlled testing, or optimization recommendations.

## Reproduction

```bash
pip install -r requirements.txt
python scripts/generate_report.py
python -m pytest -q
streamlit run app.py
```

Report generated from original local file, not from synthetic demo data.
'''
    (OUT/'insights.md').write_text(report,encoding='utf-8')
    print(f"Generated report from {metrics['ads']} ads | {metrics['purchases']} purchases | CPC IQR {iqr:.4f}")

if __name__=='__main__':
    build()
