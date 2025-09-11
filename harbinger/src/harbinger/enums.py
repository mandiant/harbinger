# harbinger/src/harbinger/enums.py
from enum import StrEnum


class LlmStatus(StrEnum):
    """Defines the operational status of an LLM agent on an object."""

    INACTIVE = "INACTIVE"  # No agent is assigned or the task is stopped/unloaded.
    MONITORING = "MONITORING"  # An agent is assigned and monitoring the object, but not actively processing.
    PROCESSING = (
        "PROCESSING"  # The agent is actively updating or working on the object.
    )
    SUCCESS = "SUCCESS"  # The last operation completed successfully.
    ERROR = "ERROR"  # The last operation failed.


class PlanStepStatus(StrEnum):
    """Defines the execution status of a single step within a plan."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"


class PlanStatus(StrEnum):
    """Defines the overall status of a plan."""

    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
