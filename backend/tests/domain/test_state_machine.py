"""Tests for the AIO-1.1 domain state machine (WB-B.1)."""

from __future__ import annotations

import itertools

import pytest

from app.domain.enums import (
    AgentDefinitionStatus,
    AgentRunStatus,
    ApprovalStatus,
    ArtifactStatus,
    ProjectStatus,
    TaskStatus,
)
from app.domain.state_machine import (
    REGISTRY,
    InvalidTransitionError,
    allowed_transitions,
    assert_transition,
    can_transition,
    is_terminal,
    terminal_statuses,
    transition_table,
)

ALL_STATUS_TYPES = list(REGISTRY.keys())


# --------------------------------------------------------------------------
# Structural invariants: every table must be total and self-consistent.
# --------------------------------------------------------------------------

@pytest.mark.parametrize("status_type", ALL_STATUS_TYPES)
def test_table_covers_every_member(status_type):
    """Every enum member must appear as a key. No implicit dead ends."""
    table = transition_table(status_type)
    assert set(table.keys()) == set(status_type)


@pytest.mark.parametrize("status_type", ALL_STATUS_TYPES)
def test_targets_are_same_type(status_type):
    """A table must never point at a status of a different type."""
    for current, targets in transition_table(status_type).items():
        for target in targets:
            assert isinstance(target, status_type), (
                f"{current} -> {target} crosses status types"
            )


@pytest.mark.parametrize("status_type", ALL_STATUS_TYPES)
def test_no_self_transition(status_type):
    """current -> current is a no-op and must not be modelled as a move."""
    for current, targets in transition_table(status_type).items():
        assert current not in targets


@pytest.mark.parametrize("status_type", ALL_STATUS_TYPES)
def test_has_at_least_one_terminal(status_type):
    """A workflow with no terminal state can never finish."""
    assert terminal_statuses(status_type)


@pytest.mark.parametrize("status_type", ALL_STATUS_TYPES)
def test_terminal_states_have_no_exit(status_type):
    """Blueprint rule: terminal is terminal. Retry creates a NEW record."""
    for status in terminal_statuses(status_type):
        assert is_terminal(status)
        assert allowed_transitions(status) == frozenset()
        for target in status_type:
            assert can_transition(status, target) is False


@pytest.mark.parametrize("status_type", ALL_STATUS_TYPES)
def test_every_non_initial_status_is_reachable(status_type):
    """Guard against statuses that exist in the enum but can never be set."""
    table = transition_table(status_type)
    reachable = set(itertools.chain.from_iterable(table.values()))
    initial = next(iter(status_type))
    unreachable = set(status_type) - reachable - {initial}
    assert not unreachable, f"unreachable statuses: {sorted(unreachable)}"


# --------------------------------------------------------------------------
# Expected terminal sets (locked so a careless table edit fails loudly).
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("status_type", "expected"),
    [
        (
            ProjectStatus,
            {ProjectStatus.COMPLETED, ProjectStatus.CANCELLED, ProjectStatus.FAILED},
        ),
        (
            TaskStatus,
            {TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED},
        ),
        (
            AgentRunStatus,
            {
                AgentRunStatus.SUCCEEDED,
                AgentRunStatus.FAILED,
                AgentRunStatus.CANCELLED,
            },
        ),
        (
            ApprovalStatus,
            {
                ApprovalStatus.REJECTED,
                ApprovalStatus.EXPIRED,
                ApprovalStatus.REVOKED,
            },
        ),
        (ArtifactStatus, {ArtifactStatus.ARCHIVED}),
        (AgentDefinitionStatus, {AgentDefinitionStatus.RETIRED}),
    ],
)
def test_expected_terminal_statuses(status_type, expected):
    assert terminal_statuses(status_type) == frozenset(expected)


# --------------------------------------------------------------------------
# Happy paths.
# --------------------------------------------------------------------------

def _walk(path):
    for current, target in itertools.pairwise(path):
        assert can_transition(current, target), f"{current} -> {target} rejected"
        assert_transition(current, target)


def test_task_happy_path():
    _walk(
        [
            TaskStatus.PENDING,
            TaskStatus.READY,
            TaskStatus.IN_PROGRESS,
            TaskStatus.REVIEW,
            TaskStatus.APPROVED,
            TaskStatus.COMPLETED,
        ]
    )


def test_task_blocked_and_recovered():
    _walk(
        [
            TaskStatus.READY,
            TaskStatus.BLOCKED,
            TaskStatus.IN_PROGRESS,
            TaskStatus.REVIEW,
        ]
    )


def test_task_changes_requested_returns_to_in_progress():
    _walk([TaskStatus.REVIEW, TaskStatus.IN_PROGRESS, TaskStatus.REVIEW])


def test_agent_run_waits_for_approval_then_resumes():
    _walk(
        [
            AgentRunStatus.QUEUED,
            AgentRunStatus.RUNNING,
            AgentRunStatus.WAITING_APPROVAL,
            AgentRunStatus.RUNNING,
            AgentRunStatus.SUCCEEDED,
        ]
    )


def test_agent_run_retry_loop():
    _walk(
        [
            AgentRunStatus.RUNNING,
            AgentRunStatus.RETRYING,
            AgentRunStatus.RUNNING,
            AgentRunStatus.RETRYING,
            AgentRunStatus.RUNNING,
            AgentRunStatus.FAILED,
        ]
    )


def test_approval_granted_then_revoked_kill_switch():
    _walk([ApprovalStatus.REQUESTED, ApprovalStatus.GRANTED, ApprovalStatus.REVOKED])


def test_approval_can_expire():
    """Blueprint ch.11: no answer is not approval."""
    assert can_transition(ApprovalStatus.REQUESTED, ApprovalStatus.EXPIRED)


def test_artifact_full_publish_path():
    _walk(
        [
            ArtifactStatus.DRAFT,
            ArtifactStatus.GENERATED,
            ArtifactStatus.VALIDATED,
            ArtifactStatus.PENDING_APPROVAL,
            ArtifactStatus.APPROVED,
            ArtifactStatus.PUBLISHED,
            ArtifactStatus.ARCHIVED,
        ]
    )


def test_artifact_rejected_returns_to_draft():
    _walk(
        [
            ArtifactStatus.PENDING_APPROVAL,
            ArtifactStatus.REJECTED,
            ArtifactStatus.DRAFT,
        ]
    )


def test_project_happy_path():
    _walk(
        [
            ProjectStatus.DRAFT,
            ProjectStatus.PLANNED,
            ProjectStatus.ACTIVE,
            ProjectStatus.REVIEW,
            ProjectStatus.COMPLETED,
        ]
    )


# --------------------------------------------------------------------------
# Rejected paths that matter for governance.
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("current", "target"),
    [
        # cannot skip the review/approval gate
        (TaskStatus.PENDING, TaskStatus.COMPLETED),
        (TaskStatus.IN_PROGRESS, TaskStatus.APPROVED),
        (TaskStatus.READY, TaskStatus.REVIEW),
        # cannot resurrect terminal states
        (TaskStatus.COMPLETED, TaskStatus.IN_PROGRESS),
        (TaskStatus.CANCELLED, TaskStatus.READY),
        (TaskStatus.FAILED, TaskStatus.READY),
        # artifact must not be published without approval
        (ArtifactStatus.VALIDATED, ArtifactStatus.PUBLISHED),
        (ArtifactStatus.DRAFT, ArtifactStatus.APPROVED),
        (ArtifactStatus.PENDING_APPROVAL, ArtifactStatus.PUBLISHED),
        # a rejected/expired approval cannot silently become granted
        (ApprovalStatus.REJECTED, ApprovalStatus.GRANTED),
        (ApprovalStatus.EXPIRED, ApprovalStatus.GRANTED),
        (ApprovalStatus.REVOKED, ApprovalStatus.GRANTED),
        # a run cannot succeed straight from the queue
        (AgentRunStatus.QUEUED, AgentRunStatus.SUCCEEDED),
        (AgentRunStatus.WAITING_APPROVAL, AgentRunStatus.SUCCEEDED),
        (AgentRunStatus.SUCCEEDED, AgentRunStatus.RUNNING),
        # project cannot go live without planning
        (ProjectStatus.DRAFT, ProjectStatus.ACTIVE),
        (ProjectStatus.COMPLETED, ProjectStatus.ACTIVE),
    ],
)
def test_forbidden_transitions(current, target):
    assert can_transition(current, target) is False
    with pytest.raises(InvalidTransitionError):
        assert_transition(current, target)


def test_error_message_carries_context():
    with pytest.raises(InvalidTransitionError) as exc:
        assert_transition(TaskStatus.PENDING, TaskStatus.COMPLETED, entity="task:tsk_1")
    err = exc.value
    assert err.current is TaskStatus.PENDING
    assert err.target is TaskStatus.COMPLETED
    assert err.entity == "task:tsk_1"
    assert "task:tsk_1" in str(err)
    assert "pending" in str(err)
    assert "completed" in str(err)


def test_cross_type_comparison_is_rejected():
    """Passing a TaskStatus where an ApprovalStatus belongs must be loud."""
    with pytest.raises(TypeError):
        can_transition(TaskStatus.PENDING, ApprovalStatus.GRANTED)


def test_unregistered_status_type_raises():
    import enum

    class OtherStatus(enum.StrEnum):
        A = "a"

    with pytest.raises(KeyError):
        transition_table(OtherStatus)


# --------------------------------------------------------------------------
# Enum values must equal the strings stored in PostgreSQL.
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("status_type", "expected"),
    [
        (
            TaskStatus,
            {
                "pending", "ready", "in_progress", "blocked", "review",
                "approved", "completed", "failed", "cancelled",
            },
        ),
        (
            ApprovalStatus,
            {"requested", "granted", "rejected", "expired", "revoked"},
        ),
        (AgentDefinitionStatus, {"provisional", "active", "retired"}),
        (
            AgentRunStatus,
            {
                "queued", "running", "waiting_approval", "retrying",
                "succeeded", "failed", "cancelled",
            },
        ),
        (
            ProjectStatus,
            {
                "draft", "planned", "active", "review",
                "completed", "cancelled", "failed",
            },
        ),
        (
            ArtifactStatus,
            {
                "draft", "generated", "validated", "pending_approval",
                "approved", "rejected", "published", "archived",
            },
        ),
    ],
)
def test_enum_values_match_database_contract(status_type, expected):
    """tasks/approvals/agent_definitions match migrations 0001-0003 today.

    projects/artifacts/agent_runs are aligned by migration 0006 (WB-B.1).
    """
    assert {s.value for s in status_type} == expected
