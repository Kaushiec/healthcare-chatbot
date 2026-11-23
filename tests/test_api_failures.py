
import unittest
from unittest.mock import AsyncMock, patch

import httpx
from fastapi.testclient import TestClient
from mysql.connector import Error as MySQLError

from backend.main import app
from backend.llm.intent import IntentExtractionError


class ChatFailureTests(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    @patch(
        "backend.main.process_chat",
        new_callable=AsyncMock
    )
    def test_ollama_unavailable(self, mock_process):

        mock_process.side_effect = httpx.ConnectError(
            "Simulated Ollama outage"
        )

        response = self.client.post(
            "/api/chat",
            json={"message": "Find hospitals in Kokrajhar"}
        )

        self.assertEqual(response.status_code, 503)

    @patch(
        "backend.main.process_chat",
        new_callable=AsyncMock
    )
    def test_database_unavailable(self, mock_process):

        mock_process.side_effect = MySQLError(
            "Simulated database outage"
        )

        response = self.client.post(
            "/api/chat",
            json={"message": "Find hospitals in Kokrajhar"}
        )

        self.assertEqual(response.status_code, 503)

    @patch(
        "backend.main.process_chat",
        new_callable=AsyncMock
    )
    def test_null_response_rejected(self, mock_process):

        mock_process.return_value = None

        response = self.client.post(
            "/api/chat",
            json={"message": "Find hospitals"}
        )

        self.assertEqual(response.status_code, 500)

    def test_empty_message_rejected(self):

        response = self.client.post(
            "/api/chat",
            json={"message": ""}
        )

        self.assertEqual(response.status_code, 422)

    
    @patch(
        "backend.main.process_chat",
        new_callable=AsyncMock
    )
    def test_llm_timeout(self, mock_process):

        mock_process.side_effect = httpx.ReadTimeout(
            "Simulated LLM timeout"
        )

        response = self.client.post(
            "/api/chat",
            json={
                "message": "Find hospitals in Kokrajhar"
            }
        )

        self.assertEqual(
            response.status_code,
            503
        )

        self.assertIn(
            "detail",
            response.json()
        )

    
    @patch(
        "backend.main.process_chat",
        new_callable=AsyncMock
    )
    def test_invalid_llm_output(self, mock_process):

        mock_process.side_effect = IntentExtractionError(
            "Simulated invalid intent output"
        )

        response = self.client.post(
            "/api/chat",
            json={
                "message": "Find doctors in Kokrajhar"
            }
        )

        self.assertEqual(
            response.status_code,
            502
        )

        self.assertIn(
            "detail",
            response.json()
        )




if __name__ == "__main__":
    unittest.main()
