"""Domain status enums for AI Office 1.1 (AIO-1.1).

Values MUST match CHECK constraints in backend/migrations/*.sql.
Alignment status as of WB-B.1:
  tasks      -> 0001 (match)
  approvals  -> 0002 (match)
  projects   -> 0001 has no CHECK  -> added by 0006
  artifacts  -> 0002 has no column -> added by 0006
  agent_runs -> 0003 has 4 values  -> expanded by 0006
"""

from enum import StrEnum


class ProjectStatus(StrEnum):
    DRAFT = "draft"
    PLANNED = "planned"
    ACTIVE = "active"
    REVIEW = "review"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class TaskStatus(StrEnum):
    PENDING = "pending"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    REVIEW = "review"
    APPROVED = "approved"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentRunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    WAITING_APPROVAL = "waiting_approval"
    RETRYING = "retrying"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ApprovalStatus(StrEnum):
    REQUESTED = "requested"
    GRANTED = "granted"
    REJECTED = "rejected"
    EXPIRED = "expired"
    REVOKED = "revoked"


class ArtifactStatus(StrEnum):
    DRAFT = "draft"
    GENERATED = "generated"
    VALIDATED = "validated"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class AgentDefinitionStatus(StrEnum):
    PROVISIONAL = "provisional"
    ACTIVE = "active"
    RETIRED = "retired"
