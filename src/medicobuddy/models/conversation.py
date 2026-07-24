"""Conversation state and turn models."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field

from medicobuddy.models.response import MedicoBuddyResponse
from medicobuddy.models.symptom import SymptomReport, TriageResult
from medicobuddy.models.user_context import UserContext


class ConversationPhase(StrEnum):
    """Current phase of the conversation."""

    INTAKE = "intake"
    CLARIFICATION = "clarification"
    PROCESSING = "processing"
    RESPONSE = "response"
    ESCALATED = "escalated"
    ENDED = "ended"


class MessageRole(StrEnum):
    """Role in a conversation turn."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ConversationTurn(BaseModel):
    """A single turn in the conversation."""

    turn_id: str = Field(default_factory=lambda: uuid4().hex[:12])
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ConversationState(BaseModel):
    """Full conversation state tracked across turns."""

    conversation_id: str = Field(default_factory=lambda: uuid4().hex)
    phase: ConversationPhase = ConversationPhase.INTAKE
    turns: list[ConversationTurn] = Field(default_factory=list)
    user_context: UserContext = Field(default_factory=UserContext)
    symptom_report: SymptomReport | None = None
    triage_result: TriageResult | None = None
    pending_questions: list[str] = Field(default_factory=list)
    response: MedicoBuddyResponse | None = None
    consent_given: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
