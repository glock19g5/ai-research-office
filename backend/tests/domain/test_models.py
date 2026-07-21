"""Tests for AIO-1.1 domain models (WB-B.1)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from app.domain.enums import (
    AgentRunStatus,
    ApprovalStatus,
    ArtifactStatus,
    ProjectStatus,
    TaskStatus,
)
from app.domain.models import (
    AgentRun,
    Approval,
    Artifact,
    Event,
    Project,
    Source,
    Task,
)
from app.domain.state_machine import InvalidTransitionError

WS = uuid.uuid4()


def make_task(**kw) -> Task:
    base = {"workspace_id": WS, "project_id": uuid.uuid4(), "title": "t"}
    return Task(**{**base, **kw})


def make_approval(**kw) -> Approval:
    base = {"workspace_id": WS, "entity_type": "artifact", "entity_id": uuid.uuid4()}
    return Approval(**{**base, **kw})


def make_artifact(**kw) -> Artifact:
    base = {"workspace_id": WS, "project_id": uuid.uuid4(), "type": "report"}
    return Artifact(**{**base, **kw})


def make_run(**kw) -> AgentRun:
    base = {"workspace_id": WS, "task_id": uuid.uuid4(), "agent_version": "v1"}
    return AgentRun(**{**base, **kw})


def make_event(**kw) -> Event:
    base = {
        "workspace_id": WS,
        "event_type": "task.started",
        "aggregate_type": "task",
        "aggregate_id": uuid.uuid4(),
        "actor_type": "system",
    }
    return Event(**{**base, **kw})


# --------------------------------------------------------------------------
# Base fields (ch.6 data rules)
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    "factory",
    [
        lambda: Project(workspace_id=WS, name="p"),
        make_task,
        make_run,
        make_artifact,
        make_approval,
        lambda: Source(workspace_id=WS, uri="https://example.org"),
        make_event,
    ],
)
def test_every_model_carries_base_fields(factory):
    obj = factory()
    assert isinstance(obj.id, uuid.UUID)
    assert obj.workspace_id == WS
    assert obj.version == 1
    assert obj.created_at.tzinfo is not None
    assert obj.updated_at.tzinfo is not None


def test_workspace_id_is_required():
    with pytest.raises(ValidationError):
        Project(name="no workspace")


def test_unknown_field_is_rejected():
    with pytest.raises(ValidationError):
        make_task(statuz=TaskStatus.READY)


def test_touch_bumps_version_and_timestamp():
    task = make_task()
    before = task.updated_at
    task.touch()
    assert task.version == 2
    assert task.updated_at >= before


def test_version_cannot_be_below_one():
    with pytest.raises(ValidationError):
        make_task(version=0)


# --------------------------------------------------------------------------
# transition_to must go through the state machine
# --------------------------------------------------------------------------

def test_transition_to_applies_and_bumps_version():
    task = make_task()
    task.transition_to(TaskStatus.READY)
    assert task.status is TaskStatus.READY
    assert task.version == 2


def test_transition_to_rejects_illegal_move():
    task = make_task()
    with pytest.raises(InvalidTransitionError):
        task.transition_to(TaskStatus.COMPLETED)


def test_rejected_transition_leaves_object_untouched():
    task = make_task()
    with pytest.raises(InvalidTransitionError):
        task.transition_to(TaskStatus.COMPLETED)
    assert task.status is TaskStatus.PENDING
    assert task.version == 1


def test_error_message_identifies_the_record():
    task = make_task()
    with pytest.raises(InvalidTransitionError) as exc:
        task.transition_to(TaskStatus.COMPLETED)
    assert f"task:{task.id}" in str(exc.value)


def test_full_task_lifecycle():
    task = make_task()
    for target in (
        TaskStatus.READY,
        TaskStatus.IN_PROGRESS,
        TaskStatus.REVIEW,
        TaskStatus.APPROVED,
        TaskStatus.COMPLETED,
    ):
        task.transition_to(target)
    assert task.status is TaskStatus.COMPLETED
    assert task.version == 6


def test_artifact_cannot_publish_without_approval():
    art = make_artifact(status=ArtifactStatus.VALIDATED)
    with pytest.raises(InvalidTransitionError):
        art.transition_to(ArtifactStatus.PUBLISHED)


def test_agent_run_starts_queued():
    run = make_run()
    assert run.status is AgentRunStatus.QUEUED
    run.transition_to(AgentRunStatus.RUNNING)
    assert run.status is AgentRunStatus.RUNNING


def test_project_defaults_to_draft():
    assert Project(workspace_id=WS, name="p").status is ProjectStatus.DRAFT


# --------------------------------------------------------------------------
# Approval expiry (ch.11: silence is not approval)
# --------------------------------------------------------------------------

def test_approval_without_expiry_never_expires():
    assert make_approval().is_expired() is False


def test_approval_past_expiry_is_expired():
    past = datetime.now(UTC) - timedelta(hours=1)
    assert make_approval(expires_at=past).is_expired() is True


def test_approval_future_expiry_is_not_expired():
    future = datetime.now(UTC) + timedelta(hours=1)
    assert make_approval(expires_at=future).is_expired() is False


def test_approval_expiry_accepts_reference_time():
    at = datetime(2026, 1, 1, tzinfo=UTC)
    appr = make_approval(expires_at=datetime(2026, 1, 2, tzinfo=UTC))
    assert appr.is_expired(at=at) is False
    assert appr.is_expired(at=at + timedelta(days=2)) is True


def test_expired_approval_cannot_become_granted():
    appr = make_approval(status=ApprovalStatus.EXPIRED)
    with pytest.raises(InvalidTransitionError):
        appr.transition_to(ApprovalStatus.GRANTED)


def test_granted_approval_can_be_revoked():
    appr = make_approval(status=ApprovalStatus.GRANTED)
    appr.transition_to(ApprovalStatus.REVOKED)
    assert appr.status is ApprovalStatus.REVOKED


def test_risk_level_must_be_a_b_or_c():
    with pytest.raises(ValidationError):
        make_approval(risk_level="D")


# --------------------------------------------------------------------------
# Append-only records must be immutable
# --------------------------------------------------------------------------

def test_event_is_frozen():
    event = make_event()
    with pytest.raises(ValidationError):
        event.event_type = "task.completed"


def test_source_is_frozen():
    src = Source(workspace_id=WS, uri="https://example.org")
    with pytest.raises(ValidationError):
        src.uri = "https://evil.example"


# --------------------------------------------------------------------------
# Field constraints
# --------------------------------------------------------------------------

def test_task_title_cannot_be_empty():
    with pytest.raises(ValidationError):
        make_task(title="")


def test_task_priority_pattern():
    assert make_task(priority="P0").priority == "P0"
    with pytest.raises(ValidationError):
        make_task(priority="P9")


def test_token_and_cost_cannot_be_negative():
    with pytest.raises(ValidationError):
        make_run(input_tokens=-1)
    with pytest.raises(ValidationError):
        make_run(cost=-0.5)


def test_status_values_serialize_as_plain_strings():
    """StrEnum keeps DB writes aligned with the CHECK constraints."""
    dumped = make_task().model_dump(mode="json")
    assert dumped["status"] == "pending"
    assert isinstance(dumped["status"], str)