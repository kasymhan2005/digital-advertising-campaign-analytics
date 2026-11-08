-- Compatible with SQLite if conversion.csv is imported as a table named ads.
-- NULLIF prevents division by zero. All campaign ratios are weighted.

-- 1) Campaign-level marketing KPIs
SELECT xyz_campaign_id, COUNT(*) AS ads,
       SUM(Impressions) AS impressions, SUM(Clicks) AS clicks,
       ROUND(100.0 * SUM(Clicks) / NULLIF(SUM(Impressions), 0), 5) AS ctr_percent,
       ROUND(SUM(Spent) / NULLIF(SUM(Clicks), 0), 3) AS cpc,
       SUM(Approved_Conversion) AS purchases,
       ROUND(SUM(Spent) / NULLIF(SUM(Approved_Conversion), 0), 2) AS cost_per_purchase
FROM ads
GROUP BY xyz_campaign_id
ORDER BY purchases DESC;

-- 2) Age and gender segments (minimum sample-size rule)
SELECT age, gender, COUNT(*) AS ads,
       SUM(Clicks) AS clicks,
       SUM(Approved_Conversion) AS purchases,
       ROUND(100.0 * SUM(Approved_Conversion) / NULLIF(SUM(Clicks), 0), 2) AS click_to_purchase_pct,
       ROUND(SUM(Spent) / NULLIF(SUM(Approved_Conversion), 0), 2) AS cost_per_purchase
FROM ads
GROUP BY age, gender
HAVING SUM(Clicks) >= 20
ORDER BY cost_per_purchase ASC;

-- 3) Interest categories (minimum click threshold)
SELECT interest, SUM(Clicks) AS clicks,
       SUM(Approved_Conversion) AS purchases,
       ROUND(SUM(Spent) / NULLIF(SUM(Approved_Conversion), 0), 2) AS cost_per_purchase
FROM ads
GROUP BY interest
HAVING SUM(Clicks) >= 30
ORDER BY purchases DESC
LIMIT 15;

-- 4) Data quality inconsistencies by campaign
SELECT xyz_campaign_id,
       SUM(CASE WHEN Clicks = 0 THEN 1 ELSE 0 END) AS zero_click_ads,
       SUM(CASE WHEN Approved_Conversion > Clicks THEN 1 ELSE 0 END) AS purchases_gt_clicks,
       SUM(CASE WHEN Clicks = 0 AND Approved_Conversion > 0 THEN 1 ELSE 0 END) AS purchases_with_zero_clicks
FROM ads
GROUP BY xyz_campaign_id;
