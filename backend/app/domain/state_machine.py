"""Deterministic state machine for AIO-1.1 domain objects.

Design rules (Blueprint P-01, P-02):
  - Transitions are data (tables), not scattered if-statements.
  - Every status change goes through assert_transition().
  - Terminal states have no outgoing transitions.
  - Retry of a failed unit creates a NEW record, it does not
    resurrect a terminal one.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Mapping, TypeVar

from app.domain.enums import (
    AgentDefinitionStatus,
    AgentRunStatus,
    ApprovalStatus,
    ArtifactStatus,
    ProjectStatus,
    TaskStatus,
)

S = TypeVar("S", bound=StrEnum)


class InvalidTransitionError(ValueError):
    """Raised when a status change is rejected by the state machine."""

    def __init__(self, current: StrEnum, target: StrEnum, entity: str | None = None):
        self.current = current
        self.target = target
        self.entity = entity
        label = entity or type(current).__name__
        super().__init__(
            f"{label}: transition {current.value!r} -> {target.value!r} is not allowed"
        )


PROJECT_TRANSITIONS: Mapping[ProjectStatus, frozenset[ProjectStatus]] = {
    ProjectStatus.DRAFT: frozenset({ProjectStatus.PLANNED, ProjectStatus.CANCELLED}),
    ProjectStatus.PLANNED: frozenset({ProjectStatus.ACTIVE, ProjectStatus.CANCELLED}),
    ProjectStatus.ACTIVE: frozenset(
        {
            ProjectStatus.REVIEW,
            ProjectStatus.COMPLETED,
            ProjectStatus.FAILED,
            ProjectStatus.CANCELLED,
        }
    ),
    ProjectStatus.REVIEW: frozenset(
        {
            ProjectStatus.ACTIVE,
            ProjectStatus.COMPLETED,
            ProjectStatus.FAILED,
            ProjectStatus.CANCELLED,
        }
    ),
    ProjectStatus.COMPLETED: frozenset(),
    ProjectStatus.CANCELLED: frozenset(),
    ProjectStatus.FAILED: frozenset(),
}

TASK_TRANSITIONS: Mapping[TaskStatus, frozenset[TaskStatus]] = {
    TaskStatus.PENDING: frozenset({TaskStatus.READY, TaskStatus.CANCELLED}),
    TaskStatus.READY: frozenset(
        {TaskStatus.IN_PROGRESS, TaskStatus.BLOCKED, TaskStatus.CANCELLED}
    ),
    TaskStatus.IN_PROGRESS: frozenset(
        {
            TaskStatus.BLOCKED,
            TaskStatus.REVIEW,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
        }
    ),
    TaskStatus.BLOCKED: frozenset(
        {
            TaskStatus.READY,
            TaskStatus.IN_PROGRESS,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
        }
    ),
    # review -> in_progress is the "changes requested" path
    TaskStatus.REVIEW: frozenset(
        {
            TaskStatus.APPROVED,
            TaskStatus.IN_PROGRESS,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
        }
    ),
    TaskStatus.APPROVED: frozenset({TaskStatus.COMPLETED, TaskStatus.FAILED}),
    TaskStatus.COMPLETED: frozenset(),
    TaskStatus.FAILED: frozenset(),
    TaskStatus.CANCELLED: frozenset(),
}

AGENT_RUN_TRANSITIONS: Mapping[AgentRunStatus, frozenset[AgentRunStatus]] = {
    AgentRunStatus.QUEUED: frozenset(
        {AgentRunStatus.RUNNING, AgentRunStatus.CANCELLED}
    ),
    AgentRunStatus.RUNNING: frozenset(
        {
            AgentRunStatus.WAITING_APPROVAL,
            AgentRunStatus.RETRYING,
            AgentRunStatus.SUCCEEDED,
            AgentRunStatus.FAILED,
            AgentRunStatus.CANCELLED,
        }
    ),
    AgentRunStatus.WAITING_APPROVAL: frozenset(
        {
            AgentRunStatus.RUNNING,
            AgentRunStatus.FAILED,
            AgentRunStatus.CANCELLED,
        }
    ),
    AgentRunStatus.RETRYING: frozenset(
        {
            AgentRunStatus.RUNNING,
            AgentRunStatus.FAILED,
            AgentRunStatus.CANCELLED,
        }
    ),
    AgentRunStatus.SUCCEEDED: frozenset(),
    AgentRunStatus.FAILED: frozenset(),
    AgentRunStatus.CANCELLED: frozenset(),
}

# Blueprint ch.11: silence is NOT approval -> requested may expire.
# granted -> revoked supports the kill switch requirement.
APPROVAL_TRANSITIONS: Mapping[ApprovalStatus, frozenset[ApprovalStatus]] = {
    ApprovalStatus.REQUESTED: frozenset(
        {
            ApprovalStatus.GRANTED,
            ApprovalStatus.REJECTED,
            ApprovalStatus.EXPIRED,
        }
    ),
    ApprovalStatus.GRANTED: frozenset({ApprovalStatus.REVOKED}),
    ApprovalStatus.REJECTED: frozenset(),
    ApprovalStatus.EXPIRED: frozenset(),
    ApprovalStatus.REVOKED: frozenset(),
}

ARTIFACT_TRANSITIONS: Mapping[ArtifactStatus, frozenset[ArtifactStatus]] = {
    ArtifactStatus.DRAFT: frozenset(
        {ArtifactStatus.GENERATED, ArtifactStatus.ARCHIVED}
    ),
    ArtifactStatus.GENERATED: frozenset(
        {ArtifactStatus.VALIDATED, ArtifactStatus.DRAFT, ArtifactStatus.ARCHIVED}
    ),
    ArtifactStatus.VALIDATED: frozenset(
        {
            ArtifactStatus.PENDING_APPROVAL,
            ArtifactStatus.GENERATED,
            ArtifactStatus.ARCHIVED,
        }
    ),
    ArtifactStatus.PENDING_APPROVAL: frozenset(
        {
            ArtifactStatus.APPROVED,
            ArtifactStatus.REJECTED,
            ArtifactStatus.ARCHIVED,
        }
    ),
    ArtifactStatus.APPROVED: frozenset(
        {ArtifactStatus.PUBLISHED, ArtifactStatus.ARCHIVED}
    ),
    ArtifactStatus.REJECTED: frozenset(
        {ArtifactStatus.DRAFT, ArtifactStatus.ARCHIVED}
    ),
    ArtifactStatus.PUBLISHED: frozenset({ArtifactStatus.ARCHIVED}),
    ArtifactStatus.ARCHIVED: frozenset(),
}

AGENT_DEFINITION_TRANSITIONS: Mapping[
    AgentDefinitionStatus, frozenset[AgentDefinitionStatus]
] = {
    AgentDefinitionStatus.PROVISIONAL: frozenset(
        {AgentDefinitionStatus.ACTIVE, AgentDefinitionStatus.RETIRED}
    ),
    AgentDefinitionStatus.ACTIVE: frozenset({AgentDefinitionStatus.RETIRED}),
    AgentDefinitionStatus.RETIRED: frozenset(),
}

REGISTRY: Mapping[type[StrEnum], Mapping[StrEnum, frozenset[StrEnum]]] = {
    ProjectStatus: PROJECT_TRANSITIONS,
    TaskStatus: TASK_TRANSITIONS,
    AgentRunStatus: AGENT_RUN_TRANSITIONS,
    ApprovalStatus: APPROVAL_TRANSITIONS,
    ArtifactStatus: ARTIFACT_TRANSITIONS,
    AgentDefinitionStatus: AGENT_DEFINITION_TRANSITIONS,
}


def transition_table(status_type: type[S]) -> Mapping[S, frozenset[S]]:
    """Return the transition table for a status enum type."""
    try:
        return REGISTRY[status_type]
    except KeyError:
        raise KeyError(
            f"No transition table registered for {status_type!r}"
        ) from None


def allowed_transitions(current: S) -> frozenset[S]:
    """Return the set of statuses reachable in one step from `current`."""
    return transition_table(type(current))[current]


def terminal_statuses(status_type: type[S]) -> frozenset[S]:
    """Return every status of this type that has no outgoing transition."""
    table = transition_table(status_type)
    return frozenset(status for status, targets in table.items() if not targets)


def is_terminal(status: S) -> bool:
    """True if no further transition is allowed from `status`."""
    return not allowed_transitions(status)


def can_transition(current: S, target: S) -> bool:
    """Check a transition without raising. Cross-type checks are an error."""
    if type(current) is not type(target):
        raise TypeError(
            "cannot compare statuses of different types: "
            f"{type(current).__name__} vs {type(target).__name__}"
        )
    return target in allowed_transitions(current)


def assert_transition(current: S, target: S, *, entity: str | None = None) -> None:
    """Raise InvalidTransitionError if the transition is not allowed."""
    if not can_transition(current, target):
        raise InvalidTransitionError(current, target, entity)
