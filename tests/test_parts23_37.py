import unittest
from unittest.mock import patch
from backend.schemas import UserIntent
from backend.services.location import haversine_km
from backend.services.chat_results import json_safe
from backend.services.chat_pipeline import apply_followup, answer_pending, route_with_new_features

class LocalTests(unittest.TestCase):
    def test_distance_zero(self):
        self.assertAlmostEqual(haversine_km(26.4, 90.3, 26.4, 90.3), 0)
    def test_distance_symmetry(self):
        a=haversine_km(26.4, 90.3, 26.5, 90.4)
        b=haversine_km(26.5, 90.4, 26.4, 90.3)
        self.assertAlmostEqual(a,b)
    def test_location_no_consent(self):
        i=UserIntent(intent='hospital_search',near_me=True)
        self.assertEqual(route_with_new_features(i,None)['status'],'needs_location')
    def test_budget_clarification(self):
        p=UserIntent(intent='doctor_search',needs_clarification=True,
                     clarification_question='Maximum fee?').model_dump()
        i=answer_pending('₹500',p)
        self.assertEqual(i.max_price,500)
        self.assertFalse(i.needs_clarification)
    def test_followup_hospital(self):
        last=UserIntent(intent='facility_search',facility='ICU',city='Kokrajhar').model_dump()
        parsed=UserIntent(intent='hospital_search',hospital_name='Nilachal')
        got=apply_followup('What about Nilachal?',parsed,last)
        self.assertEqual(got.intent,'facility_search')
        self.assertEqual(got.facility,'ICU')
        self.assertEqual(got.hospital_name,'Nilachal')
    def test_unsupported_pharmacy(self):
        i=UserIntent(intent='pharmacy_search')
        self.assertEqual(route_with_new_features(i,None)['status'],'not_implemented')
    def test_unknown_coords(self):
        with patch('backend.services.location.fetch_rows',return_value=[]):
            i=UserIntent(intent='hospital_search',near_me=True)
            r=route_with_new_features(i,{'latitude':26.4,'longitude':90.3})
        self.assertEqual(r['status'],'missing_coordinates')
    def test_comparison_missing_service(self):
        i=UserIntent(intent='hospital_comparison')
        self.assertEqual(route_with_new_features(i,None)['status'],'needs_clarification')
    def test_json_currency(self):
        from decimal import Decimal
        self.assertEqual(json_safe({'fee':Decimal('250.00')}),{'fee':'250.00'})
    def test_comparison_price_limits(self):
        i=UserIntent(intent='hospital_comparison', service='CBC', max_price=500)
        with patch('backend.services.chat_pipeline.compare_service_prices',return_value={'status':'no_results','intent':'hospital_comparison','message':'no','count':0,'results':[]}) as f:
            route_with_new_features(i,None)
        f.assert_called_once_with('CBC',max_price=500)
if __name__=='__main__':
    unittest.main()

class PipelineTests(unittest.IsolatedAsyncioTestCase):
    async def test_pipeline_without_memory(self):
        from backend.services.chat_pipeline import process_chat
        from unittest.mock import AsyncMock
        intent = UserIntent(intent='hospital_search', city='Kokrajhar')
        with patch('backend.services.chat_pipeline._memory_enabled', return_value=False), \
             patch('backend.services.chat_pipeline.extract_intent', new_callable=AsyncMock, return_value=intent), \
             patch('backend.services.chat_pipeline.route_with_new_features', return_value={
                 'intent':'hospital_search','status':'ok','message':'found','count':1,
                 'results':[{'name':'Example Hospital'}]}), \
             patch('backend.services.chat_pipeline.generate_grounded_answer', new_callable=AsyncMock, return_value='Found Example Hospital.'):
            answer = await process_chat('Find hospitals in Kokrajhar')
        self.assertEqual(answer['count'], 1)
        self.assertEqual(answer['answer'], 'Found Example Hospital.')
        self.assertTrue(answer['session_id'])
