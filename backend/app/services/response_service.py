from __future__ import annotations

import json

from groq import Groq

from app.config import GROQ_API_KEY, GROQ_MODEL
from app.schemas.ingestion import IngestionResult

RESPONSE_SYSTEM_PROMPT = (
    "You are an assistant helping the user with a summarized, actionable response. "
    "Provide clear markdown with concise guidance."
)


def generate_response(
    result: IngestionResult,
    history: list[dict[str, object]],
    current_message: str,
) -> str:
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is not configured.")

    client = Groq(api_key=GROQ_API_KEY)

    context = []
    for item in history:
        role = item.get("role")
        content = item.get("content")
        if isinstance(role, str) and isinstance(content, str):
            context.append({"role": role, "content": content})

    payload = {
        "intent": result.intent,
        "risk_profile": result.risk_profile,
        "priority": result.priority,
        "summary": result.summary,
        "requires_action": result.requires_action,
        "history": context,
        "current_message": current_message,
    }

    prompt = (
        "Use the summary and history below to craft a helpful assistant response in markdown. "
        f"\n\nAnalysis: {json.dumps(payload, ensure_ascii=False)}"
    )

    completion = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": RESPONSE_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
    )
    return completion.choices[0].message.content.strip()
