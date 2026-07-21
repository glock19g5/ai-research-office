"""Domain models for AIO-1.1 (WB-B.1).

Blueprint ch.6 data rules enforced here:
  - every record carries id / workspace_id / created_at / updated_at
    / created_by / version
  - status changes go through the state machine, never by plain assignment
  - sources and events are append-only (frozen models)
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any, ClassVar, Self

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import (
    AgentRunStatus,
    ApprovalStatus,
    ArtifactStatus,
    ProjectStatus,
    TaskStatus,
)
from app.domain.state_machine import assert_transition


def _now() -> datetime:
    return datetime.now(UTC)


def _new_id() -> uuid.UUID:
    return uuid.uuid4()


class DomainModel(BaseModel):
    """Base for every persisted domain object."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    id: uuid.UUID = Field(default_factory=_new_id)
    workspace_id: uuid.UUID
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)
    created_by: uuid.UUID | None = None
    version: int = Field(default=1, ge=1)

    def touch(self) -> Self:
        """Bump version and updated_at (optimistic locking, ch.6)."""
        self.version += 1
        self.updated_at = _now()
        return self


class StatefulModel(DomainModel):
    """A domain object whose status is guarded by the state machine."""

    entity_label: ClassVar[str] = "entity"

    def transition_to(self, target: Any) -> Self:
        """Validate, then apply a status change.

        Raises InvalidTransitionError if the move is not allowed.
        """
        assert_transition(
            self.status, target, entity=f"{self.entity_label}:{self.id}"
        )
        self.status = target
        return self.touch()


class Project(StatefulModel):
    entity_label: ClassVar[str] = "project"

    name: str = Field(min_length=1, max_length=200)
    objective: str | None = None
    scope: str | None = None
    status: ProjectStatus = ProjectStatus.DRAFT
    owner_id: uuid.UUID | None = None
    brief: dict[str, Any] = Field(default_factory=dict)


class Task(StatefulModel):
    entity_label: ClassVar[str] = "task"

    project_id: uuid.UUID
    parent_id: uuid.UUID | None = None
    title: str = Field(min_length=1, max_length=300)
    description: str | None = None
    status: TaskStatus = TaskStatus.PENDING
    priority: str = Field(default="P2", pattern=r"^P[0-3]$")
    assigned_agent_id: uuid.UUID | None = None
    due_at: datetime | None = None
    approval_required: bool = False
    error: str | None = None


class AgentRun(StatefulModel):
    entity_label: ClassVar[str] = "agent_run"

    task_id: uuid.UUID
    agent_version: str
    prompt_version: str | None = None
    model: str | None = None
    provider: str | None = None
    status: AgentRunStatus = AgentRunStatus.QUEUED
    started_at: datetime | None = None
    ended_at: datetime | None = None
    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    cost: float = Field(default=0.0, ge=0.0)
    retry_count: int = Field(default=0, ge=0)
    correlation_id: uuid.UUID | None = None
    error_code: str | None = None


class Artifact(StatefulModel):
    entity_label: ClassVar[str] = "artifact"

    project_id: uuid.UUID
    task_id: uuid.UUID | None = None
    type: str
    uri: str | None = None
    status: ArtifactStatus = ArtifactStatus.DRAFT
    artifact_version: int = Field(default=1, ge=1)
    checksum: str | None = None
    source_manifest: list[uuid.UUID] = Field(default_factory=list)


class Approval(StatefulModel):
    entity_label: ClassVar[str] = "approval"

    entity_type: str
    entity_id: uuid.UUID
    risk_level: str = Field(default="C", pattern=r"^[ABC]$")
    status: ApprovalStatus = ApprovalStatus.REQUESTED
    requested_by: uuid.UUID | None = None
    approver_id: uuid.UUID | None = None
    reason: str | None = None
    decided_at: datetime | None = None
    expires_at: datetime | None = None

    def is_expired(self, *, at: datetime | None = None) -> bool:
        """Blueprint ch.11: silence is not approval."""
        if self.expires_at is None:
            return False
        return (at or _now()) >= self.expires_at


class Source(DomainModel):
    """Immutable evidence record (ch.9 provenance)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    uri: str
    title: str | None = None
    publisher: str | None = None
    published_at: datetime | None = None
    accessed_at: datetime = Field(default_factory=_now)
    checksum: str | None = None
    trust_tier: str = "unrated"


class Event(DomainModel):
    """Append-only fact (ch.8). Frozen: never edited, only superseded."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    event_type: str
    aggregate_type: str
    aggregate_id: uuid.UUID
    actor_type: str
    actor_id: uuid.UUID | None = None
    correlation_id: uuid.UUID | None = None
    causation_id: uuid.UUID | None = None
    schema_version: int = Field(default=1, ge=1)
    payload: dict[str, Any] = Field(default_factory=dict)
    occurred_at: datetime = Field(default_factory=_now)
