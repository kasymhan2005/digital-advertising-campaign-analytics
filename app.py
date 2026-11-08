"""Digital Advertising Campaign Analytics | Streamlit portfolio application.

Deployment: streamlit run app.py
On Streamlit Community Cloud, the original data is NOT shipped by default.
Users can upload their licensed CSV, or inspect a clearly labelled synthetic demo.
"""
from __future__ import annotations

from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from src.analysis import load_ads, group_summary, overall_summary, add_ad_metrics, quality_report, campaign_concentration

ROOT = Path(__file__).resolve().parent
REAL = ROOT / 'data' / 'raw' / 'conversion.csv'
DEMO = ROOT / 'data' / 'demo' / 'synthetic_ads.csv'
BLUE, CYAN, ORANGE, GREEN = '#59B7FF', '#86E0EA', '#FDA76C', '#48C9A7'
PALETTE = ['#59B7FF', '#FDA76C', '#48C9A7', '#BDA8FC']
CONFIG = {'displayModeBar': False}

st.set_page_config(page_title='Ad Campaign Intelligence | Analytics Portfolio', page_icon='📊', layout='wide', initial_sidebar_state='expanded')
st.markdown('''<style>
.block-container{padding-top:2.0rem;padding-bottom:4rem;max-width:1450px}
[data-testid="stMetric"]{background:#14243A;border:1px solid #26405C;border-radius:15px;padding:18px}
[data-testid="stMetricLabel"]{font-size:.9rem}
.subdued{color:#9BB3CA;font-size:.9rem}
.big-heading{font-size:2.15rem;font-weight:750;letter-spacing:-.025em;margin-bottom:.2rem}
.section-note{border-left:3px solid #59B7FF;padding:.5rem .9rem;color:#C8D8E8;background:#14243A;border-radius:0 6px 6px 0;margin:1rem 0}
</style>''', unsafe_allow_html=True)

@st.cache_data(show_spinner=False)
def get_csv(path: str):
    return load_ads(path)

with st.sidebar:
    st.markdown('### 📊 Campaign Intelligence')
    st.caption('Interactive marketing analytics · portfolio project')
    upload = st.file_uploader('Analyze your own conversion.csv', type='csv', help='Use a file with the original 11-column schema.')
    try:
        if upload:
            raw = load_ads(upload)
            source_mode = 'UPLOADED CSV'
        elif REAL.exists():
            raw = get_csv(str(REAL))
            source_mode = 'ORIGINAL LOCAL CSV'
        else:
            raw = get_csv(str(DEMO))
            source_mode = 'SYNTHETIC DEMO'
    except Exception as exc:
        st.error(f'Cannot load dataset: {exc}')
        st.stop()
    if source_mode == 'SYNTHETIC DEMO':
        st.warning('**SYNTHETIC DEMO** — Figures are illustrative. Upload the source CSV to analyze the real campaigns.')
    else:
        st.success(f'Data source: {source_mode}')
    st.divider()
    st.markdown('**Audience & campaign filters**')
    campaigns = sorted(raw['xyz_campaign_id'].unique().tolist())
    selected_campaigns = st.multiselect('XYZ campaign IDs', campaigns, default=campaigns)
    genders = sorted(raw['gender'].unique().tolist())
    selected_gender = st.multiselect('Gender', genders, default=genders)
    ages = sorted(raw['age'].unique().tolist())
    selected_ages = st.multiselect('Age bands', ages, default=ages)
    interests = sorted(raw['interest'].unique().tolist())
    selected_interests = st.multiselect('Interest codes (optional)', interests, default=[], help='Leave empty to include every interest code.')
    st.divider()
    st.caption('Click-through and conversion rates are weighted ratios of totals. Currency is unspecified in the source file.')

filtered = raw.loc[
    raw['xyz_campaign_id'].isin(selected_campaigns)
    & raw['gender'].isin(selected_gender)
    & raw['age'].isin(selected_ages)
    & (raw['interest'].isin(selected_interests) if selected_interests else True)
].copy()
if filtered.empty:
    st.warning('No ads match the selected filters. Widen the sidebar filters.')
    st.stop()

st.markdown('<div class="big-heading">Advertising Campaign Performance</div>', unsafe_allow_html=True)
st.markdown('Explore campaign-level efficiency, audience segments, and conversion outcomes. <span class="subdued">Historical cross-sectional dataset · no event dates or purchase revenue.</span>', unsafe_allow_html=True)
if source_mode == 'SYNTHETIC DEMO':
    st.info('This cloud preview uses deliberately synthetic records. Real results require uploading conversion.csv in the sidebar.')

metrics = overall_summary(filtered)
q = quality_report(filtered)
labels = [
    ('Impressions', f"{metrics['impressions']:,}"),
    ('Clicks', f"{metrics['clicks']:,}"),
    ('CTR', f"{100 * metrics['ctr']:.4f}%"),
    ('Confirmed purchases', f"{metrics['purchases']:,}"),
    ('Cost / purchase', f"{metrics['cost_per_purchase']:,.2f}" if pd.notna(metrics['cost_per_purchase']) else 'N/A')
]
cols = st.columns(5)
for c,(label,value) in zip(cols,labels):
    with c:
        st.metric(label,value)

st.caption(f"Selected: {len(filtered):,} of {len(raw):,} ads · {metrics['campaigns']} campaigns · Total spend {metrics['spent']:,.2f} dataset currency units")

TABS = st.tabs(['📈 Overview','🎯 Campaigns','👥 Audience','🔎 Ad explorer','🧪 Data quality','📖 Methodology'])


def plot_bar(df, x, y, title, color=None, orientation='v'):
    df = df.copy()
    if 'xyz_campaign_id' in df.columns:
        df['xyz_campaign_id'] = df['xyz_campaign_id'].astype(str)
    fig = px.bar(df, x=x, y=y, color=color, title=title,
                 color_discrete_sequence=PALETTE, orientation=orientation,
                 template='plotly_dark', text_auto='.3s')
    fig.update_layout(margin=dict(l=8,r=12,t=54,b=15),paper_bgcolor='rgba(0,0,0,0)',
                      plot_bgcolor='rgba(0,0,0,0)', legend_title_text='',
                      font=dict(color='#DCE8F4'), height=375)
    fig.update_traces(textposition='outside',cliponaxis=False)
    return fig


def plain_chart(fig):
    fig.update_layout(template='plotly_dark',paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',
                      font=dict(color='#DCE8F4'),margin=dict(l=10,r=10,t=50,b=20))
    return fig

with TABS[0]:
    campaign = group_summary(filtered,'xyz_campaign_id')
    left,right = st.columns(2)
    with left:
        st.plotly_chart(plot_bar(campaign,'xyz_campaign_id','purchases','Purchases by campaign',color='xyz_campaign_id'),use_container_width=True,config=CONFIG)
    with right:
        st.plotly_chart(plot_bar(campaign,'xyz_campaign_id','spent','Spend by campaign',color='xyz_campaign_id'),use_container_width=True,config=CONFIG)
    st.markdown('#### Overall advertising metrics')
    m1,m2,m3 = st.columns(3)
    m1.metric('Cost per click (CPC)', f"{metrics['cpc']:.3f}" if pd.notna(metrics['cpc']) else 'N/A')
    m2.metric('Purchases / clicks (aggregate)', f"{100*metrics['click_to_purchase_rate']:.2f}%" if pd.notna(metrics['click_to_purchase_rate']) else 'N/A')
    m3.metric('Interested actions',f"{metrics['interested']:,}")
    st.markdown('<div class="section-note">These are <strong>counts aggregated across ads</strong>, not a validated chronological user funnel. The source contains some ads with more purchases than clicks.</div>',unsafe_allow_html=True)
    event_values=pd.DataFrame({'Event count':['Impressions','Clicks','Interested','Approved purchases'],
                               'count':[metrics['impressions'],metrics['clicks'],metrics['interested'],metrics['purchases']]})
    fig=px.bar(event_values,x='Event count',y='count',log_y=True,title='Event volumes (logarithmic scale)',
               color='Event count',color_discrete_sequence=PALETTE,text_auto='.3s')
    fig.update_layout(showlegend=False,height=350)
    st.plotly_chart(plain_chart(fig),use_container_width=True,config=CONFIG)

with TABS[1]:
    campaign = campaign_concentration(filtered).sort_values('xyz_campaign_id')
    c1,c2=st.columns(2)
    with c1:
        st.plotly_chart(plot_bar(campaign,'xyz_campaign_id','ctr','Weighted CTR (fraction)',color='xyz_campaign_id'),use_container_width=True,config=CONFIG)
    with c2:
        st.plotly_chart(plot_bar(campaign,'xyz_campaign_id','cost_per_purchase','Cost per approved purchase',color='xyz_campaign_id'),use_container_width=True,config=CONFIG)
    st.markdown('#### Share of spending vs. share of purchases')
    comp=campaign[['xyz_campaign_id','spend_share','purchase_share']].copy()
    comp['xyz_campaign_id'] = comp['xyz_campaign_id'].astype(str)
    comp=comp.melt(id_vars='xyz_campaign_id',var_name='Metric',value_name='Share')
    fig=px.bar(comp,x='xyz_campaign_id',y='Share',color='Metric',barmode='group',color_discrete_sequence=[BLUE,ORANGE],
               title='Campaign contributions to total spend and purchases')
    fig.update_layout(yaxis_tickformat='.0%',height=350)
    st.plotly_chart(plain_chart(fig),use_container_width=True,config=CONFIG)
    display=campaign.copy()
    for col in ['ctr','click_to_purchase_rate','spend_share','purchase_share']:
        display[col] = display[col].map(lambda v: f'{v*100:.3f}%' if pd.notna(v) else '—')
    st.dataframe(display,use_container_width=True,hide_index=True)
    st.caption('Low cost per purchase does not establish profitability. Revenue per purchase is unavailable; therefore ROAS and ROI cannot be calculated.')

with TABS[2]:
    seg = group_summary(filtered,['age','gender'])
    seg['age']=pd.Categorical(seg['age'],categories=sorted(raw['age'].unique()),ordered=True)
    a,b=st.columns(2)
    with a:
        fig=px.bar(seg.sort_values('age'),x='age',y='purchases',color='gender',barmode='group',
                   title='Purchases by age and gender',color_discrete_sequence=[BLUE,ORANGE])
        fig.update_layout(height=385)
        st.plotly_chart(plain_chart(fig),use_container_width=True,config=CONFIG)
    with b:
        eligible = seg.loc[seg.clicks>=20].sort_values('click_to_purchase_rate',ascending=False)
        fig=px.bar(eligible,x='age',y='click_to_purchase_rate',color='gender',barmode='group',
                   title='Purchases / clicks · segments with ≥20 clicks',color_discrete_sequence=[BLUE,ORANGE])
        fig.update_layout(yaxis_tickformat='.1%',height=385)
        st.plotly_chart(plain_chart(fig),use_container_width=True,config=CONFIG)
    st.markdown('#### Interest category performance')
    by_interest=group_summary(filtered,'interest')
    min_clicks=st.slider('Minimum clicks per interest code',min_value=0,max_value=max(100,int(by_interest.clicks.max())),value=30,step=10)
    by_interest=by_interest.loc[by_interest.clicks>=min_clicks].sort_values('purchases',ascending=False).head(15)
    if len(by_interest):
        fig=px.bar(by_interest,x='interest',y='purchases',color='cost_per_purchase',
                   title='Top interest codes by approved purchases · colored by cost / purchase',
                   color_continuous_scale='Blues',text_auto=True)
        fig.update_layout(height=430)
        st.plotly_chart(plain_chart(fig),use_container_width=True,config=CONFIG)
    else:
        st.info('No interest codes meet the selected click minimum.')
    st.caption('Interest numbers represent category IDs, not inherently ranked preferences. Segment rankings can be unstable when denominators are small.')

with TABS[3]:
    ads=add_ad_metrics(filtered)
    st.markdown('#### Ad-level performance')
    fig=px.scatter(ads,x='Spent',y='Approved_Conversion',size='Impressions',color='xyz_campaign_id',
                   hover_data=['ad_id','age','gender','Clicks','Impressions','ctr','cpc'],
                   title='Ad spend vs. approved purchases · marker size = impressions',
                   color_discrete_sequence=PALETTE,opacity=.65)
    fig.update_layout(height=460)
    st.plotly_chart(plain_chart(fig),use_container_width=True,config=CONFIG)
    st.markdown('#### Inspect and export filtered ads')
    st.caption('Ad-level CR and CPC are undefined if Clicks = 0; undefined values are left empty.')
    cols_show=['ad_id','xyz_campaign_id','age','gender','interest','Impressions','Clicks','Spent',
               'Approved_Conversion','ctr','cpc','click_to_purchase_rate','cost_per_purchase']
    st.dataframe(ads[cols_show].sort_values('Spent',ascending=False),use_container_width=True,hide_index=True)
    st.download_button('Download filtered ads as CSV',ads[cols_show].to_csv(index=False).encode('utf-8'),
                       file_name='filtered_ad_performance.csv',mime='text/csv')

with TABS[4]:
    st.markdown('#### Data quality audit')
    st.info('Zero-click ads with purchases and ads with purchase counts larger than click counts exist in the original file. These may reflect attribution/modeling differences or errors. We flag them, not silently alter them.')
    a,b,c,d=st.columns(4)
    a.metric('Missing cells',q['missing_cells'])
    b.metric('Duplicate rows',q['duplicates'])
    c.metric('Zero-click ads',q['zero_click_ads'])
    d.metric('Purchases > clicks',q['purchases_gt_clicks'])
    st.metric('Purchases with zero clicks',q['purchases_with_zero_clicks'])
    flag=filtered.loc[(filtered['Approved_Conversion']>filtered['Clicks']) | (filtered['Total_Conversion']>filtered['Clicks'])]
    if not flag.empty:
        st.dataframe(flag[['ad_id','xyz_campaign_id','Clicks','Total_Conversion','Approved_Conversion','Spent']].head(200),
                     use_container_width=True,hide_index=True)
    st.markdown('**Why weighted aggregation?** Summing clicks and impressions first avoids averaging rates across differently sized ads.')
    st.code('weighted_ctr = df["Clicks"].sum() / df["Impressions"].sum()',language='python')

with TABS[5]:
    st.markdown('### Dataset and metric definitions')
    st.markdown('''
- **Row grain:** one advertisement (`ad_id`); campaign is `xyz_campaign_id`; `fb_campaign_id` is a separate Facebook campaign identifier.
- **CTR:** total clicks / total impressions. Displayed as a fraction in tables and percentages in KPI cards.
- **CPC:** total advertising spend / total clicks. Undefined when clicks = 0.
- **Click-to-purchase ratio:** approved conversions / clicks. This is an aggregated descriptive ratio, **not** a validated user-level funnel because some rows have conversions with no clicks.
- **Cost per approved purchase (CPA proxy):** advertising spend / approved conversions. Undefined when purchases = 0.
- **Spend units:** dataset monetary units; the source does not reliably specify a currency.
- **Do not infer:** ROAS, ROI, causality, or time trends. Sales revenue, randomized assignment, and timestamps are not provided.
- **Source usage:** the original CSV was provided as coursework. Public-repository code excludes it unless redistribution permission is confirmed.
''')
    st.markdown('#### Source data structure')
    st.dataframe(pd.DataFrame({'column':list(raw.columns),'dtype':list(raw.dtypes.astype(str))}),hide_index=True,use_container_width=True)
    st.caption('Built using Streamlit, Pandas, and Plotly. Statistical reporting is descriptive, not an A/B test.')
