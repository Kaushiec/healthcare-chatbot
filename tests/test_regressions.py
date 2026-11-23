
import unittest
from unittest.mock import AsyncMock, patch

from backend.schemas import UserIntent

from backend.services.chat_pipeline import (
    apply_followup,
    answer_pending,
    process_chat
)

from backend.services.comparison import (
    normalize_service_name
)


class ConversationRegressionTests(unittest.TestCase):

    def test_budget_clarification(self):

        pending = UserIntent(
            intent="doctor_search",
            needs_clarification=True,
            clarification_question="What is your budget?"
        )

        result = answer_pending(
            "500",
            pending.model_dump()
        )

        self.assertIsNotNone(result)

        if result is not None:
            self.assertEqual(
                result.intent,
                "doctor_search"
            )
            self.assertEqual(result.max_price, 500)
            self.assertFalse(result.needs_clarification)

    def test_facility_followup(self):

        previous = UserIntent(
            intent="facility_search",
            facility="ICU",
            city="Kokrajhar"
        )

        current = UserIntent(
            intent="hospital_search",
            hospital_name="Nilachal"
        )

        result = apply_followup(
            "What about Nilachal?",
            current,
            previous.model_dump()
        )

        self.assertEqual(result.intent, "facility_search")
        self.assertEqual(result.facility, "ICU")
        self.assertEqual(result.hospital_name, "Nilachal")
        self.assertEqual(result.city, "Kokrajhar")

    def test_cbc_aliases(self):

        variations = [
            "CBC",
            "CBC test",
            "CBC test prices",
            "Complete Blood Count",
            "Compare CBC test prices."
        ]

        for term in variations:
            with self.subTest(term=term):
                self.assertEqual(
                    normalize_service_name(term),
                    "cbc"
                )

    def test_comparison_clarification(self):

        pending = UserIntent(
            intent="hospital_comparison",
            city="Kokrajhar",
            needs_clarification=True
        )

        result = answer_pending(
            "Compare CBC test prices.",
            pending.model_dump()
        )

        self.assertIsNotNone(result)

        if result is not None:
            self.assertEqual(
                result.intent,
                "hospital_comparison"
            )
            self.assertEqual(result.city, "Kokrajhar")
            self.assertEqual(
                normalize_service_name(result.service or ""),
                "cbc"
            )
            self.assertFalse(result.needs_clarification)


class PipelineRegressionTests(
    unittest.IsolatedAsyncioTestCase
):

    async def test_budget_not_treated_as_distance(self):

        incorrect_intent = UserIntent(
            intent="doctor_search",
            hospital_name="MRM",
            max_price=500,
            near_me=True,
            max_distance_km=500
        )

        mocked_result = {
            "intent": "doctor_search",
            "status": "no_results",
            "message": "No matching records.",
            "count": 0,
            "results": []
        }

        with (
            patch(
                "backend.services.chat_pipeline._memory_enabled",
                return_value=False
            ),
            patch(
                "backend.services.chat_pipeline.extract_intent",
                new_callable=AsyncMock,
                return_value=incorrect_intent
            ),
            patch(
                "backend.services.chat_pipeline.route_with_new_features",
                return_value=mocked_result
            ) as mocked_router,
            patch(
                "backend.services.chat_pipeline.generate_grounded_answer",
                new_callable=AsyncMock,
                return_value="No matching records."
            )
        ):

            response = await process_chat(
                "Find doctors at MRM with fees below ₹500."
            )

        routed_intent = mocked_router.call_args.args[0]

        self.assertFalse(routed_intent.near_me)
        self.assertIsNone(routed_intent.max_distance_km)
        self.assertEqual(routed_intent.max_price, 500)

        self.assertIsInstance(response, dict)
        self.assertEqual(response["status"], "no_results")

    async def test_best_hospital_unknown_intent(self):

        incorrect_intent = UserIntent(
            intent="unknown"
        )

        mocked_result = {
            "intent": "hospital_comparison",
            "status": "needs_clarification",
            "message": "Choose a comparison criterion.",
            "count": 0,
            "results": []
        }

        with (
            patch(
                "backend.services.chat_pipeline._memory_enabled",
                return_value=False
            ),
            patch(
                "backend.services.chat_pipeline.extract_intent",
                new_callable=AsyncMock,
                return_value=incorrect_intent
            ),
            patch(
                "backend.services.chat_pipeline.route_with_new_features",
                return_value=mocked_result
            ) as mocked_router,
            patch(
                "backend.services.chat_pipeline.generate_grounded_answer",
                new_callable=AsyncMock,
                return_value="Choose a comparison criterion."
            )
        ):

            response = await process_chat(
                "Which is the best hospital in Kokrajhar?"
            )

        routed_intent = mocked_router.call_args.args[0]

        self.assertEqual(
            routed_intent.intent,
            "hospital_comparison"
        )
        self.assertTrue(routed_intent.needs_clarification)

        self.assertIsInstance(response, dict)
        self.assertEqual(
            response["status"],
            "needs_clarification"
        )


if __name__ == "__main__":
    unittest.main()
