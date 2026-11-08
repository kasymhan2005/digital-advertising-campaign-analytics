"""Reusable, audited metrics for the ad-campaign portfolio project.

All rates from aggregated data are *weighted ratios of sums*, not unweighted
averages of per-ad rates. Undefined rates with denominator 0 are NaN.
"""
from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd

REQUIRED = (
    'ad_id', 'xyz_campaign_id', 'fb_campaign_id', 'age', 'gender', 'interest',
    'Impressions', 'Clicks', 'Spent', 'Total_Conversion', 'Approved_Conversion'
)
COUNTS = ('Impressions', 'Clicks', 'Total_Conversion', 'Approved_Conversion')
SUM_COLUMNS = (*COUNTS, 'Spent')


def load_ads(source: str | Path | object) -> pd.DataFrame:
    """Read and validate the basic file schema, without altering source rows."""
    df = pd.read_csv(source)
    missing = sorted(set(REQUIRED) - set(df.columns))
    if missing:
        raise ValueError(f'Missing required columns: {missing}')
    df = df.loc[:, list(REQUIRED)].copy()
    for col in (*COUNTS, 'Spent'):
        df[col] = pd.to_numeric(df[col], errors='coerce')
    if df[list(SUM_COLUMNS)].isna().any().any():
        raise ValueError('Non-numeric or missing metrics; inspect the source file')
    if (df[list(SUM_COLUMNS)] < 0).any().any():
        raise ValueError('Negative counts or spend cannot be used for this analysis')
    if df[list(REQUIRED)].isna().any().any():
        raise ValueError('The input has missing values in required fields')
    df['age'] = df['age'].astype(str)
    df['gender'] = df['gender'].astype(str)
    return df


def safe_ratio(numerator: pd.Series | float, denominator: pd.Series | float):
    """Return NaN for zero denominators (rather than infinity or a false 0%)."""
    a = np.asarray(numerator, dtype=float)
    b = np.asarray(denominator, dtype=float)
    result = np.full(np.broadcast_shapes(a.shape, b.shape), np.nan, dtype=float)
    np.divide(a, b, out=result, where=np.broadcast_to(b, result.shape) != 0)
    if isinstance(numerator, pd.Series):
        return pd.Series(result, index=numerator.index)
    return result.item() if result.ndim == 0 else result


def add_ad_metrics(df: pd.DataFrame) -> pd.DataFrame:
    x = df.copy()
    x['ctr'] = safe_ratio(x['Clicks'], x['Impressions'])
    x['cpc'] = safe_ratio(x['Spent'], x['Clicks'])
    x['click_to_purchase_rate'] = safe_ratio(x['Approved_Conversion'], x['Clicks'])
    x['cost_per_purchase'] = safe_ratio(x['Spent'], x['Approved_Conversion'])
    x['zero_clicks_with_purchases'] = (x['Clicks'] == 0) & (x['Approved_Conversion'] > 0)
    x['purchases_gt_clicks'] = x['Approved_Conversion'] > x['Clicks']
    x['interests_gt_clicks'] = x['Total_Conversion'] > x['Clicks']
    return x


def group_summary(df: pd.DataFrame, by: str | list[str]) -> pd.DataFrame:
    """A weighted summary suitable for campaign and audience comparisons."""
    keys = [by] if isinstance(by, str) else by
    g = df.groupby(keys, dropna=False, observed=True).agg(
        ads=('ad_id', 'size'),
        impressions=('Impressions', 'sum'),
        clicks=('Clicks', 'sum'),
        spent=('Spent', 'sum'),
        interested=('Total_Conversion', 'sum'),
        purchases=('Approved_Conversion', 'sum')
    ).reset_index()
    g['ctr'] = safe_ratio(g['clicks'], g['impressions'])
    g['cpc'] = safe_ratio(g['spent'], g['clicks'])
    g['click_to_purchase_rate'] = safe_ratio(g['purchases'], g['clicks'])
    g['cost_per_purchase'] = safe_ratio(g['spent'], g['purchases'])
    return g


def overall_summary(df: pd.DataFrame) -> dict:
    vals = {x: float(df[x].sum()) for x in SUM_COLUMNS}
    return {
        'ads': len(df),
        'campaigns': int(df['xyz_campaign_id'].nunique()),
        'impressions': int(vals['Impressions']),
        'clicks': int(vals['Clicks']),
        'spent': vals['Spent'],
        'interested': int(vals['Total_Conversion']),
        'purchases': int(vals['Approved_Conversion']),
        'ctr': safe_ratio(vals['Clicks'], vals['Impressions']),
        'cpc': safe_ratio(vals['Spent'], vals['Clicks']),
        'click_to_purchase_rate': safe_ratio(vals['Approved_Conversion'], vals['Clicks']),
        'cost_per_purchase': safe_ratio(vals['Spent'], vals['Approved_Conversion'])
    }


def quality_report(df: pd.DataFrame) -> dict:
    return {
        'rows': int(len(df)),
        'duplicates': int(df.duplicated().sum()),
        'missing_cells': int(df.isna().sum().sum()),
        'zero_click_ads': int((df['Clicks'] == 0).sum()),
        'purchases_gt_clicks': int((df['Approved_Conversion'] > df['Clicks']).sum()),
        'purchases_with_zero_clicks': int(((df['Clicks'] == 0) & (df['Approved_Conversion'] > 0)).sum()),
        'interests_gt_clicks': int((df['Total_Conversion'] > df['Clicks']).sum()),
        'negative_metrics': int((df[list(SUM_COLUMNS)] < 0).any(axis=1).sum())
    }


def campaign_concentration(df: pd.DataFrame) -> pd.DataFrame:
    """Shares of spending vs purchases, not a causal efficiency estimate."""
    g = group_summary(df, 'xyz_campaign_id')
    g['spend_share'] = safe_ratio(g['spent'], g['spent'].sum())
    g['purchase_share'] = safe_ratio(g['purchases'], g['purchases'].sum())
    return g
