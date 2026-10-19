from dataclasses import dataclass, field
from uuid import UUID, uuid4


@dataclass
class ConditionConfig:

    left_type: str

    left_name: str

    operator: str

    match_mode: str = "Any"

    right_type: str | None = None

    right_value: object = None

    id: UUID = field(
        default_factory=uuid4
    )