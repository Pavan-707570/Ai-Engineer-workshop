from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Intent(str):
    pass


Intent = Literal["triage", "analysis", "follow_up", "summary"]


class RiskProfile(str):
    pass


RiskProfile = Literal["low", "medium", "high", "critical"]


class Priority(str):
    pass


Priority = Literal["low", "normal", "high", "urgent"]


class IngestionRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    session_id: str | None = Field(default=None, description="Optional conversation session id.")
    message: str = Field(..., description="User input to analyze.")

    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Message cannot be empty.")
        return value


class TokenMetadata(BaseModel):
    estimated_input_tokens: int = Field(default=0, ge=0)
    note: str = Field(default="Token estimate for the incoming message.")


class IngestionResult(BaseModel):
    model_config = ConfigDict(extra="ignore")

    intent: Intent = Field(default="analysis")
    risk_profile: RiskProfile = Field(default="medium")
    priority: Priority = Field(default="normal")
    summary: str = Field(default="")
    requires_action: bool = Field(default=False)
    token_metadata: TokenMetadata = Field(default_factory=TokenMetadata)
