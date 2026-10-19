from dataclasses import dataclass, field
from uuid import UUID, uuid4


@dataclass
class OperationConfig:

    name: str

    parameters: dict = field(
        default_factory=dict
    )

    id: UUID = field(
        default_factory=uuid4
    )