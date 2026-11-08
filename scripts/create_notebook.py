"""Build an explanatory, reproducible notebook with the course tasks + extra analysis."""
from pathlib import Path
import nbformat as nbf
from nbclient import NotebookClient

root=Path(__file__).resolve().parents[1]
nb=nbf.v4.new_notebook()
C=[]

def md(s): C.append(nbf.v4.new_markdown_cell(s))
def code(s): C.append(nbf.v4.new_code_cell(s))

md('''# 📣 Digital Advertising Campaign Analytics
### A reproducible end-to-end exploratory data analysis

This notebook follows the course exercises and extends them with **weighted KPIs, targeting cohorts, campaign economics, and data-quality checks**.

**Dataset:** `conversion.csv` (1,143 ad-level records). No revenue, dates, or currency label are provided. Outcomes are observational — no A/B inference.

**Portfolio flow:** inspect → validate → visualize → engineer metrics → benchmark → audit → derive cautiously stated business insights.
''')
md('## 1. Setup and load data\nRun from the repository root. The raw CSV is included in the downloadable archive but intentionally excluded from Git commits until redistribution permission is confirmed.')
code('''from pathlib import Path
import sys
ROOT = Path.cwd() if (Path.cwd()/"src").is_dir() else Path.cwd().parent
sys.path.insert(0, str(ROOT))
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

from src.analysis import load_ads, add_ad_metrics, group_summary, overall_summary, quality_report

sns.set_theme(style="whitegrid")
pd.set_option("display.max_columns", 30)
DATA = ROOT / "data/raw/conversion.csv"
conversion = load_ads(DATA)
conversion.head()''')
md('## 2. Initial exploratory checks')
code('''print("Rows / columns:", conversion.shape)
print("Duplicate rows:", conversion.duplicated().sum())
print("Missing values per column:")
print(conversion.isna().sum().to_string())
print("\\nDtypes:")
print(conversion.dtypes.to_string())''')
md('''### Variable types
- Discrete counts: impressions, clicks, total conversions, approved purchases.
- Continuous: spend (recorded in monetary units).
- Nominal: gender, interest codes, ad/campaign IDs.
- Ordinal: age category (not individual age).''')
md('## 3. Campaign counts and impression distributions')
code('''print("Unique XYZ campaign IDs:", conversion.xyz_campaign_id.nunique())
print(conversion.xyz_campaign_id.value_counts().sort_index())
fb = conversion.groupby('fb_campaign_id', as_index=False)['Impressions'].sum()
fb['log_impressions'] = np.log(fb['Impressions'].clip(lower=1))
fig, axes = plt.subplots(1, 2, figsize=(12, 3.8))
sns.histplot(data=fb, x='Impressions', bins=30, ax=axes[0], color='steelblue')
sns.histplot(data=fb, x='log_impressions', bins=30, kde=True, ax=axes[1], color='seagreen')
axes[0].set_title('Before log transformation')
axes[1].set_title('After log transformation')
plt.tight_layout()
plt.show()''')
md('## 4. Course metrics: CTR, CPC, and click-to-purchase conversion')
code('''ads = add_ad_metrics(conversion)
columns=['ad_id','xyz_campaign_id','ctr','cpc','click_to_purchase_rate','cost_per_purchase']
display(ads[columns].head())
print('Highest CTR ad:', int(ads.loc[ads.ctr.idxmax(),'ad_id']))
print('CPC IQR:', round(ads.cpc.quantile(.75)-ads.cpc.quantile(.25),4))
print('Ad 1121814 click-to-purchase conversion %:',
      round(ads.loc[ads.ad_id==1121814,'click_to_purchase_rate'].iloc[0]*100,2))''')
md('''**Important:** a rate cannot be evaluated when its denominator equals zero. Such results appear as `NaN`, not as zero. Aggregated ratios are computed from the sums of numerators and denominators, to prevent unequal ad sizes from distorting rates.''')
md('## 5. CTR distributions by campaign')
code('''fig,axes=plt.subplots(1,3,figsize=(14,3.7),sharex=False)
for ax,(campaign,group) in zip(axes,ads.groupby('xyz_campaign_id')):
    sns.histplot(data=group, x='ctr', bins=20, kde=True, ax=ax, color='steelblue')
    ax.set_title(f'XYZ {campaign}: {len(group)} ads')
plt.tight_layout(); plt.show()''')
md('## 6. CPC by audience gender')
code('''sns.histplot(data=ads, x='cpc', hue='gender', bins=30, kde=True)
plt.title('Ad-level CPC by gender')
plt.xlim(left=0)
plt.show()''')
md('## 7. Weighted KPI summary (additional portfolio analysis)')
code('''summary=overall_summary(conversion)
display(pd.Series(summary, name='Value').to_frame())
by_campaign=group_summary(conversion,'xyz_campaign_id')
display(by_campaign.round(5))''')
md('''Campaign impressions, clicks and spends differ substantially. **Do not** compare campaigns by raw purchases alone when discussing efficiency; compare spend per approved purchase alongside sample sizes. Economic profitability cannot be measured because revenue is missing.''')
md('## 8. Campaign comparisons')
code('''fig,axes=plt.subplots(1,2,figsize=(12,4))
sns.barplot(data=by_campaign,x='xyz_campaign_id',y='purchases',ax=axes[0],color='steelblue')
sns.barplot(data=by_campaign,x='xyz_campaign_id',y='cost_per_purchase',ax=axes[1],color='coral')
axes[0].set_title('Approved purchases')
axes[1].set_title('Cost per purchase (spend units)')
plt.tight_layout();plt.show()''')
md('## 9. Age & gender targeting analysis')
code('''by_segment=group_summary(conversion,['age','gender'])
display(by_segment.sort_values('purchases',ascending=False).round(4))
plt.figure(figsize=(9,4))
sns.barplot(data=by_segment,x='age',y='purchases',hue='gender')
plt.title('Approved purchases by age and gender')
plt.show()''')
md('## 10. Interest segments and minimum sample size')
code('''by_interest=group_summary(conversion,'interest')
min_clicks = 30
reliable = by_interest.query('clicks >= @min_clicks').sort_values('purchases',ascending=False)
display(reliable.head(10).round(4))''')
md('## 11. Data quality (important caveat)')
code('''display(pd.Series(quality_report(conversion),name='value').to_frame())
print('Problematic example rows:')
display(conversion.loc[conversion.Approved_Conversion>conversion.Clicks,
    ['ad_id','xyz_campaign_id','Clicks','Approved_Conversion']].head(8))''')
md('''**Interpretation:** some rows report purchases without clicks or more purchases than clicks. This is inconsistent with a strictly nested, unique-user click → purchase funnel and may reflect source definitions, attribution or data errors. We retain those records but label `purchases/clicks` as a **descriptive aggregated ratio** rather than a verified person-level probability. We cannot infer causality, ROAS, or temporal trends.''')
md('## 12. Portfolio takeaways')
code('''by_campaign=by_campaign.sort_values('xyz_campaign_id')
lowest=by_campaign.loc[by_campaign.cost_per_purchase.idxmin()]
largest=by_campaign.loc[by_campaign.purchases.idxmax()]
print(f"Most approved purchases: campaign {int(largest.xyz_campaign_id)} with {int(largest.purchases):,} purchases.")
print(f"Lowest observed cost/purchase: campaign {int(lowest.xyz_campaign_id)} at {lowest.cost_per_purchase:.2f} spend units.")
print("Further analysis needs purchase revenue, timestamps and conversion attribution definitions.")''')
md('''### Reproducibility and limitations
- `python scripts/generate_report.py` regenerates the static visualizations and executive report.
- `streamlit run app.py` opens a filterable dashboard.
- `python -m pytest -q` verifies metric calculations on synthetic edge cases.
- Source CSV redistribution rights are **not independently verified**; the public repository should not include the original raw file without permission.
- Published demo data is explicitly **synthetic**, not a substitute for real results.
''')
nb.cells=C
nb.metadata={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},
             'language_info':{'name':'python'}}
path=root/'notebooks/01_marketing_eda.ipynb'
try:
    nb=NotebookClient(nb,timeout=120,kernel_name='python3',resources={'metadata':{'path':str(root)}}).execute()
    nbf.write(nb,path)
    print('Notebook executed and saved:',path,'cells=',len(nb.cells))
except Exception as exc:
    nbf.write(nb,path)
    raise
