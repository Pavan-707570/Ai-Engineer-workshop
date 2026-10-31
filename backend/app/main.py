from __future__ import annotations

from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from app.config import GROQ_API_KEY
from app.schemas.assistant import AssistantResult
from app.schemas.ingestion import IngestionRequest
from app.services.database_service import (
    add_chat_message,
    ensure_conversation,
    get_chat_history,
    get_conversation_messages,
    initialize_database,
    list_conversations,
)
from app.services.llm_service import analyze_message
from app.services.response_service import generate_response
from app.utils.token_counter import estimate_tokens

app = FastAPI(
    title="Enterprise Ingestion Firewall",
    version="4.0.0",
    description="AI-powered message analysis and contextual assistance.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    initialize_database()


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "message": "Ingestion Firewall API is running", "database": "sqlite"}


@app.get("/api/conversations")
def conversations() -> dict[str, list[dict[str, object]]]:
    return {"items": list_conversations()}


@app.get("/api/conversations/{session_id}/messages")
def conversation_messages(session_id: str) -> dict[str, object]:
    try:
        UUID(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid conversation ID.") from exc

    return {"session_id": session_id, "items": get_conversation_messages(session_id)}


@app.post("/api/analyze")
def analyze(request: IngestionRequest) -> AssistantResult:
    message = request.message.strip()
    if not message:
        raise HTTPException(status_code=422, detail="Message cannot be empty.")

    session_id = request.session_id or str(uuid4())

    try:
        UUID(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="session_id must be a valid UUID.") from exc

    ensure_conversation(session_id, message[:70])

    try:
        result = analyze_message(message)
        result.token_metadata.estimated_input_tokens = estimate_tokens(message)
        history = get_chat_history(session_id)
        response_markdown = generate_response(result, history, message)

        add_chat_message(session_id, "user", message)
        add_chat_message(session_id, "assistant", response_markdown)

        payload = result.model_dump()
        return AssistantResult(
            **payload,
            session_id=session_id,
            response_markdown=response_markdown,
        )
    except ValidationError as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "error": "The model response did not pass schema validation.",
                "validation_errors": exc.errors(),
            },
        ) from exc
    except Exception as exc:
        print(f"Request failed for session {session_id}: {exc}")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


__all__ = ["app"]
