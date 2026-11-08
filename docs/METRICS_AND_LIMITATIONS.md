# Methodology and limitations

## Data grain and features

Each row is a single advertisement `ad_id`. The field `xyz_campaign_id` represents the parent campaign in Company X, whereas `fb_campaign_id` identifies a Facebook campaign. Age is an ordered band; gender and interest are categorical; the integer interest code is an ID, not a numeric ranking.

## KPI calculations

| KPI | Formula | Interpretation |
|---|---|---|
| CTR | `sum(Clicks) / sum(Impressions)` | Proportion of impressions associated with clicks |
| CPC | `sum(Spent) / sum(Clicks)` | Monetary units spent per click |
| Approved purchases / clicks | `sum(Approved_Conversion) / sum(Clicks)` | Aggregate descriptive ratio (not user-level probability) |
| CPA proxy | `sum(Spent) / sum(Approved_Conversion)` | Advertising spend per approved purchase |
| Spend share | `campaign_spent / overall_spent` | Contribution to total ad spending |
| Purchase share | `campaign_purchases / overall_purchases` | Contribution to approved purchases |
| IQR | `Q3 - Q1` | Spread of the middle half of numeric observations |

Aggregate ratios use **weighted numerators and denominators**. For example, don't compute a campaign CTR as `mean(ad_ctr)`, since every ad has different impressions. Divisions by zero are undefined (`NaN`); undefined values are excluded in descriptive distributions.

## Data quality

Original source data (1,143 ads, 0 missing cells, 0 duplicate rows) include:

- 207 advertisements reporting zero clicks.
- 72 advertisements where approved purchases exceed clicks.
- 71 advertisements with zero clicks but at least one approved purchase.
- 218 advertisements where total interested actions exceed clicks.

This could be due to different definitions or attribution, or a data-quality defect; the source does not resolve the cause. A strict click→interested→purchase user funnel cannot be reconstructed from these data. Therefore the dashboard reports **counts** at each event type, not a customer-level funnel.

## Not supported by the dataset

- **ROAS, ROI and profit:** no purchase revenue, margin or product prices.
- **Trends / seasonality:** no event dates or campaign timestamps.
- **Causal effectiveness:** no randomized treatment/control or design to identify a causal effect.
- **Customer behavior:** no unique user identifiers, attribution windows or repeat-purchase flags.
- **Currency:** spend is provided without reliable currency metadata.

Cross-campaign differences can reflect targeting, competition, spend, bids, creative or many confounders. Business recommendations should be phrased as **hypotheses to validate**, not causal conclusions.
