import io
import math
import unittest
import pandas as pd
from src.analysis import load_ads, add_ad_metrics, group_summary, overall_summary, quality_report


class AnalysisTests(unittest.TestCase):
    def setUp(self):
        self.df = pd.DataFrame([
            [1, 916, 10, '30-34', 'M', 2, 100, 10, 20., 4, 2],
            [2, 916, 10, '30-34', 'F', 1, 900, 0, 0., 0, 1],
            [3, 936, 11, '35-39', 'F', 3, 100, 20, 40., 5, 4],
        ], columns=['ad_id','xyz_campaign_id','fb_campaign_id','age','gender','interest',
                    'Impressions','Clicks','Spent','Total_Conversion','Approved_Conversion'])

    def test_weighted_ctr_not_mean_ad_ctr(self):
        g = group_summary(self.df, 'xyz_campaign_id').set_index('xyz_campaign_id')
        self.assertAlmostEqual(g.loc[916, 'ctr'], 10 / 1000)
        self.assertAlmostEqual(g.loc[916, 'cpc'], 2.)
        self.assertAlmostEqual(g.loc[916, 'cost_per_purchase'], 20/3)

    def test_zero_click_metrics_undefined(self):
        x = add_ad_metrics(self.df)
        self.assertTrue(math.isnan(x.loc[1, 'cpc']))
        self.assertTrue(math.isnan(x.loc[1, 'click_to_purchase_rate']))
        self.assertTrue(math.isnan(x.loc[1, 'ctr']) is False)

    def test_ratios_and_totals(self):
        o = overall_summary(self.df)
        self.assertEqual(o['ads'], 3)
        self.assertEqual(o['purchases'], 7)
        self.assertAlmostEqual(o['click_to_purchase_rate'], 7/30)

    def test_quality_flags(self):
        q = quality_report(self.df)
        self.assertEqual(q['zero_click_ads'], 1)
        self.assertEqual(q['purchases_gt_clicks'], 1)
        self.assertEqual(q['purchases_with_zero_clicks'], 1)
        self.assertEqual(q['duplicates'], 0)

    def test_schema_rejection(self):
        with self.assertRaisesRegex(ValueError, 'Missing required'):
            load_ads(io.StringIO('Clicks,Spent\n10,2.0\n'))

    def test_load_roundtrip(self):
        io_obj = io.StringIO(self.df.to_csv(index=False))
        loaded = load_ads(io_obj)
        self.assertEqual(loaded.shape, self.df.shape)

    def test_zero_purchase_undefined_cpa(self):
        x = self.df.copy()
        x['Approved_Conversion'] = 0
        g = group_summary(x, 'xyz_campaign_id')
        self.assertTrue(g['cost_per_purchase'].isna().all())

    def test_no_source_mutation(self):
        old = list(self.df.columns)
        add_ad_metrics(self.df)
        self.assertEqual(list(self.df.columns), old)

if __name__ == '__main__':
    unittest.main()
