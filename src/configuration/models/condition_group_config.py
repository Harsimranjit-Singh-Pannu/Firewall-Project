from dataclasses import dataclass, field
from uuid import UUID, uuid4

from .condition_config import ConditionConfig


@dataclass
class ConditionGroupConfig:

    operator: str = "AND"

    id: UUID = field(
        default_factory=uuid4
    )

    conditions: list[ConditionConfig] = field(
        default_factory=list
    )


    def add_condition(
        self,
        condition: ConditionConfig
    ):

        self.conditions.append(
            condition
        )