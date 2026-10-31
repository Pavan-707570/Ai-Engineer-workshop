from __future__ import annotations

from pydantic import BaseModel, Field


class AssistantResult(BaseModel):
    session_id: str = Field(..., description="Conversation session identifier.")
    response_markdown: str = Field(..., description="Assistant response content.")
    intent: str = Field(default="analysis")
    risk_profile: str = Field(default="medium")
    priority: str = Field(default="normal")
    summary: str = Field(default="")
    requires_action: bool = Field(default=False)
    token_metadata: dict[str, int | str] = Field(default_factory=dict)
