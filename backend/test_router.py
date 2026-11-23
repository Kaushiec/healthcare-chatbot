import unittest
from unittest.mock import patch

from backend.schemas import UserIntent
from backend.services.router import execute_intent


class RouterTests(unittest.TestCase):

    @patch("backend.services.router.search_facilities")
    def test_facility_routing(self, mock_search):

        mock_search.return_value = [
            {
                "hospital_name": "Example Hospital",
                "facility_name": "ICU"
            }
        ]

        intent = UserIntent(
            intent="facility_search",
            city="Kokrajhar",
            facility="ICU"
        )

        result = execute_intent(intent)

        mock_search.assert_called_once_with(
            facility="ICU",
            city="Kokrajhar"
        )

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["count"], 1)

    def test_pharmacy_not_implemented(self):

        intent = UserIntent(
            intent="pharmacy_search"
        )

        result = execute_intent(intent)

        self.assertEqual(
            result["status"],
            "not_implemented"
        )

    def test_near_me_not_ignored(self):

        intent = UserIntent(
            intent="hospital_search",
            near_me=True
        )

        result = execute_intent(intent)

        self.assertEqual(
            result["status"],
            "needs_location"
        )


if __name__ == "__main__":
    unittest.main()