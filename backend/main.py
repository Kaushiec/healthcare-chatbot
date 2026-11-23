
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.services.hospitals import (
    search_hospitals,
    search_departments,
    search_beds,
    search_facilities,
)

from backend.services.doctors import search_doctors
from backend.services.prices import search_prices
from backend.llm.ollama import generate_response

from fastapi import HTTPException
from fastapi.concurrency import run_in_threadpool

from backend.llm.intent import (
    extract_intent,
    IntentExtractionError
)

from backend.services.router import execute_intent
from backend.services.chat_pipeline import process_chat

import logging
import httpx

from mysql.connector import Error as MySQLError
from fastapi import HTTPException

from backend.llm.intent import IntentExtractionError

logger = logging.getLogger(__name__)
app = FastAPI(title="Healthcare Chatbot API")


class UserLocation(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    location: UserLocation | None = None
    session_id: str | None = Field(default=None, max_length=36)


@app.get("/api/health")
def health_check():
    return {"status": "ok"}



@app.post("/api/chat")
async def chat(request: ChatRequest):

    try:
        result = await process_chat(
            message=request.message,
            session_id=request.session_id,
            location=(
                request.location.model_dump()
                if request.location
                else None
            )
        )

        # Prevent another HTTP 200 / JSON null bug.
        if not isinstance(result, dict):
            raise RuntimeError(
                "Chat pipeline did not return a dictionary"
            )

        if not isinstance(result.get("answer"), str):
            raise RuntimeError(
                "Chat pipeline returned an invalid answer"
            )

        return result

    except IntentExtractionError as exc:
        logger.exception("Invalid LLM intent output")

        raise HTTPException(
            status_code=502,
            detail=(
                "The AI could not interpret this request "
                "reliably. Please try rephrasing it."
            )
        ) from exc

    except httpx.HTTPError as exc:
        logger.exception("Ollama HTTP request failed")

        raise HTTPException(
            status_code=503,
            detail=(
                "The AI service is temporarily unavailable. "
                "Please try again."
            )
        ) from exc

    except MySQLError as exc:
        logger.exception("Healthcare database request failed")

        raise HTTPException(
            status_code=503,
            detail=(
                "The healthcare database is temporarily "
                "unavailable."
            )
        ) from exc

    except HTTPException:
        raise

    except Exception as exc:
        logger.exception("Unexpected chatbot error")

        raise HTTPException(
            status_code=500,
            detail=(
                "An unexpected server error occurred. "
                "Please try again."
            )
        ) from exc



@app.get("/api/hospitals")
def api_hospitals(
    city: str | None = None,
    department: str | None = None,
    name: str | None = None
):
    return {
        "results": search_hospitals(
            city=city,
            department=department,
            name=name
        )
    }


@app.get("/api/doctors")
def api_doctors(
    specialization: str | None = None,
    hospital: str | None = None,
    max_price: float | None = Query(default=None, ge=0)
):
    return {
        "results": search_doctors(
            specialization=specialization,
            hospital=hospital,
            max_price=max_price
        )
    }


@app.get("/api/departments")
def api_departments(
    city: str | None = None,
    department: str | None = None
):
    return {
        "results": search_departments(
            city=city,
            department=department
        )
    }


@app.get("/api/beds")
def api_beds(
    hospital: str | None = None,
    bed_type: str | None = None,
    max_price: float | None = Query(default=None, ge=0)
):
    return {
        "results": search_beds(
            hospital=hospital,
            bed_type=bed_type,
            max_price=max_price
        )
    }


@app.get("/api/facilities")
def api_facilities(
    facility: str | None = None,
    city: str | None = None
):
    return {
        "results": search_facilities(
            facility=facility,
            city=city
        )
    }


@app.get("/api/prices")
def api_prices(
    service: str | None = None,
    hospital: str | None = None,
    category: str | None = None,
    max_price: float | None = Query(default=None, ge=0)
):
    return {
        "results": search_prices(
            service=service,
            hospital=hospital,
            category=category,
            max_price=max_price
        )
    }


@app.post("/api/ai-test")
async def ai_test(message: str):

    messages = [
        {
            "role": "system",
            "content": "You are a helpful healthcare information assistant."
        },
        {
            "role": "user",
            "content": message
        }
    ]

    answer = await generate_response(messages)

    return {
        "answer": answer
    }



class IntentTestRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


@app.post("/api/intent-test")
async def api_intent_test(request: IntentTestRequest):

    try:
        parsed = await extract_intent(request.message)

        return {
            "extracted_intent": parsed.model_dump(
                mode="json"
            )
        }

    except (IntentExtractionError, ValueError) as exc:
        raise HTTPException(
            status_code=502,
            detail="Unable to extract a valid intent"
        ) from exc

    except Exception as exc:
        print(
            f"Intent model error: "
            f"{type(exc).__name__}: {exc}"
        )

        raise HTTPException(
            status_code=503,
            detail="The local language model is unavailable"
        ) from exc


@app.post("/api/route-test")
async def api_route_test(request: IntentTestRequest):

    try:
        parsed = await extract_intent(request.message)

    except (IntentExtractionError, ValueError) as exc:
        raise HTTPException(
            status_code=502,
            detail="Unable to extract a valid intent"
        ) from exc

    except Exception as exc:
        print(
            f"Intent model error: "
            f"{type(exc).__name__}: {exc}"
        )

        raise HTTPException(
            status_code=503,
            detail="The local language model is unavailable"
        ) from exc

    try:
        routing = await run_in_threadpool(
            execute_intent,
            parsed
        )

    except Exception as exc:
        print(
            f"Database search error: "
            f"{type(exc).__name__}: {exc}"
        )

        raise HTTPException(
            status_code=500,
            detail="Database search failed"
        ) from exc

    return {
        "extracted_intent": parsed.model_dump(
            mode="json"
        ),
        "routing": routing
    }


# Keep this mount below ALL API endpoints.
frontend_path = Path(__file__).resolve().parent.parent / "frontend"

app.mount(
    "/",
    StaticFiles(directory=str(frontend_path), html=True),
    name="frontend"
)
