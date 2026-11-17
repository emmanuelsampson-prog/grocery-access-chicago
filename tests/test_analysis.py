"""Checks for interpretation-critical date, route and emissions behavior."""
import unittest
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra
from src.prepare import active
from src.analysis import conditional_co2
from src.mobility import first_full_post_week,missing_is_not_zero
from src.network import usable
from src.download import ROOT

class MethodTests(unittest.TestCase):
    def test_last_open_day_is_inclusive(self):
        r=pd.DataFrame({'reviewed_start':pd.to_datetime(['2021-01-01']),
                        'reviewed_end':pd.to_datetime(['2023-04-16'])})
        self.assertEqual(len(active(r,'2023-04-16',True)),1)
        self.assertEqual(len(active(r,'2023-04-17',True)),0)
    def test_opening_day_is_inclusive(self):
        r=pd.DataFrame({'reviewed_start':pd.to_datetime(['2023-05-11']),
                        'reviewed_end':pd.to_datetime([None])})
        self.assertEqual(len(active(r,'2023-05-10',True)),0)
        self.assertEqual(len(active(r,'2023-05-11',True)),1)
    def test_directed_round_trip(self):
        graph=csr_matrix(np.array([[0.,2,0],[0,0,3],[7,0,0]]))
        outgoing=dijkstra(graph,indices=0)[1]
        returning=dijkstra(graph.T.tocsr(),indices=0)[1]
        self.assertEqual(outgoing+returning,12)
        self.assertNotEqual(outgoing*2,outgoing+returning)
    def test_roundtrip_not_doubled_in_emissions(self):
        self.assertAlmostEqual(conditional_co2(1.609344,1,trips=1),.4)
        self.assertEqual(conditional_co2(1,0),0)
        self.assertLess(conditional_co2(-1,.5),0)
    def test_invalid_car_share(self):
        with self.assertRaises(ValueError):conditional_co2(1,1.1)
    def test_event_week(self):
        self.assertEqual(str(first_full_post_week('2023-05-11').date()),'2023-05-15')
        self.assertEqual(str(first_full_post_week('2023-04-16').date()),'2023-04-17')
    def test_missing_is_not_zero(self):
        x=pd.DataFrame({'store_id':['a','a'],'week':pd.to_datetime(['2023-01-02','2023-01-16']),'visits':[5,8]})
        y=missing_is_not_zero(x)
        self.assertTrue(pd.isna(y.loc[1,'visits']))
    def test_mode_permissions(self):
        self.assertFalse(usable({'highway':'motorway'},'walk'))
        self.assertFalse(usable({'highway':'footway'},'drive'))
        self.assertFalse(usable({'highway':'residential','access':'private'},'walk'))
        self.assertTrue(usable({'highway':'path','access':'private','foot':'yes'},'walk'))

class DataChecks(unittest.TestCase):
    def test_six_events_five_sites(self):
        e=pd.read_csv(ROOT/'data/processed/verified_events.csv')
        self.assertEqual(len(e),6)
        self.assertEqual(e[['longitude','latitude']].drop_duplicates().shape[0],5)
    def test_no_unmatched_tracts(self):
        t=pd.read_csv(ROOT/'data/processed/tract_context.csv')
        self.assertEqual(len(t),789)
        self.assertFalse(t.population.isna().any())
        self.assertTrue(t.geoid.is_unique)
    def test_primary_comparisons_monotonic(self):
        r=pd.read_csv(ROOT/'data/processed/event_access_origins.csv')
        r=r[r.main_included & r.variant.eq('main')]
        closures=r[~r.period.eq('save_a_lot_opening')]
        opening=r[r.period.eq('save_a_lot_opening')]
        for c in ['walk_change_minutes','drive_change_roundtrip_km']:
            self.assertTrue((closures[c]>=-1e-8).all())
            self.assertTrue((opening[c]<=1e-8).all())
    def test_exact_six_event_dates(self):
        e=pd.read_csv(ROOT/'data/processed/verified_events.csv')
        self.assertEqual(e.loc[e.event_id.str.startswith('walmart'),'event_date'].unique().tolist(),['2023-04-16'])
        self.assertEqual(e.set_index('event_id').loc['save_a_lot_englewood','administrative_date_gap_days'],127)

if __name__=='__main__':unittest.main()
