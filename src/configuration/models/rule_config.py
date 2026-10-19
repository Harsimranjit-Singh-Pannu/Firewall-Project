from dataclasses import dataclass, field
from uuid import UUID, uuid4

from .condition_group_config import ConditionGroupConfig
from .operation_config import OperationConfig
from .action_config import ActionConfig


@dataclass
class RuleConfig:

    name: str

    id: UUID = field(default_factory=uuid4)

    order: int = 0

    condition_group: ConditionGroupConfig | None = None

    operations: list[OperationConfig] = field(
        default_factory=list
    )

    action: ActionConfig | None = None


    def set_condition_group(
        self,
        condition_group: ConditionGroupConfig
    ):
        self.condition_group = condition_group


    def add_operation(
        self,
        operation: OperationConfig
    ):
        self.operations.append(operation)


    def set_action(
        self,
        action: ActionConfig
    ):
        self.action = action