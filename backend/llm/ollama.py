
import os

import httpx
from dotenv import load_dotenv


load_dotenv()


async def generate_response(
    messages: list[dict],
    *,
    response_format: str | dict | None = None,
    temperature: float = 0.0
) -> str:

    model = os.getenv(
        "OLLAMA_MODEL",
        "qwen3:4b"
    )

    url = os.getenv(
        "OLLAMA_URL",
        "http://localhost:11434/api/chat"
    )

    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "think": False,
        "options": {
            "temperature": temperature
        }
    }

    if response_format is not None:
        payload["format"] = response_format

    async with httpx.AsyncClient(
        timeout=httpx.Timeout(180, connect=10)
    ) as client:

        response = await client.post(
            url,
            json=payload
        )

        response.raise_for_status()

        body = response.json()

    content = body.get("message", {}).get("content")

    if not isinstance(content, str) or not content.strip():
        raise ValueError(
            "Ollama returned an empty or invalid message.content"
        )

    return content
