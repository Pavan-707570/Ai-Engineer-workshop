from __future__ import annotations

import instructor
from groq import Groq

from app.config import GROQ_API_KEY, GROQ_MODEL
from app.schemas.ingestion import IngestionResult

SYSTEM_PROMPT = (
    "You are an Enterprise Ingestion Firewall analyst. "
    "Classify the user's intent, assess risk, prioritize actions, "
    "summarize the request, and return structured JSON only."
)


def analyze_message(message: str) -> IngestionResult:
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is not configured.")

    client = Groq(api_key=GROQ_API_KEY)
    client = instructor.from_groq(client, mode=instructor.Mode.JSON)

    return client.chat.completions.create(
        model=GROQ_MODEL,
        response_model=IngestionResult,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": message},
        ],
    )
