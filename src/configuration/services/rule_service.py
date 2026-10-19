from configuration.models.rule_config import RuleConfig
from configuration.models.operation_config import OperationConfig


class RuleService:

    def __init__(
        self,
        draft_service
    ):

        self.draft_service = draft_service


    def get_ruleset(
        self,
        draft_id,
        ruleset_id
    ):

        draft = self.draft_service.get_draft(
            draft_id
        )

        if draft is None:

            raise ValueError(
                "Draft not found"
            )

        return draft.configuration.get_ruleset(
            ruleset_id
        )


    def add_rule(
        self,
        draft_id,
        ruleset_id,
        name
    ):

        ruleset = self.get_ruleset(
            draft_id,
            ruleset_id
        )

        if ruleset is None:

            raise ValueError(
                "Ruleset not found"
            )

        rule = RuleConfig(
            name=name
        )

        ruleset.add_rule(
            rule
        )

        return rule


    def get_rule(
        self,
        draft_id,
        ruleset_id,
        rule_id
    ):

        ruleset = self.get_ruleset(
            draft_id,
            ruleset_id
        )

        if ruleset is None:

            raise ValueError(
                "Ruleset not found"
            )

        for rule in ruleset.rules:

            if rule.id == rule_id:

                return rule

        return None


    def update_condition_group(
        self,
        draft_id,
        ruleset_id,
        rule_id,
        condition_group
    ):

        rule = self.get_rule(
            draft_id,
            ruleset_id,
            rule_id
        )

        if rule is None:

            raise ValueError(
                "Rule not found"
            )

        rule.condition_group = condition_group

        return rule


    def add_operation(
        self,
        draft_id,
        ruleset_id,
        rule_id,
        operation
    ):

        rule = self.get_rule(
            draft_id,
            ruleset_id,
            rule_id
        )

        if rule is None:

            raise ValueError(
                "Rule not found"
            )

        if not isinstance(
            operation,
            OperationConfig
        ):

            raise ValueError(
                "Operation must be an OperationConfig"
            )

        rule.add_operation(
            operation
        )

        return operation


    def create_operation(
        self,
        draft_id,
        ruleset_id,
        rule_id,
        name,
        parameters=None
    ):

        if not name:

            raise ValueError(
                "Operation name is required"
            )

        operation = OperationConfig(

            name=name,

            parameters=(
                dict(parameters)
                if parameters is not None
                else {}
            )

        )

        self.add_operation(

            draft_id,

            ruleset_id,

            rule_id,

            operation

        )

        return operation


    def get_operation(
        self,
        draft_id,
        ruleset_id,
        rule_id,
        operation_id
    ):

        rule = self.get_rule(
            draft_id,
            ruleset_id,
            rule_id
        )

        if rule is None:

            raise ValueError(
                "Rule not found"
            )

        for operation in rule.operations:

            if operation.id == operation_id:

                return operation

        return None


    def remove_operation(
        self,
        draft_id,
        ruleset_id,
        rule_id,
        operation_index
    ):

        rule = self.get_rule(
            draft_id,
            ruleset_id,
            rule_id
        )

        if rule is None:

            raise ValueError(
                "Rule not found"
            )

        if (
            operation_index < 0
            or operation_index >= len(rule.operations)
        ):

            raise IndexError(
                "Operation index out of range"
            )

        return rule.operations.pop(
            operation_index
        )


    def set_action(
        self,
        draft_id,
        ruleset_id,
        rule_id,
        action
    ):

        rule = self.get_rule(
            draft_id,
            ruleset_id,
            rule_id
        )

        if rule is None:

            raise ValueError(
                "Rule not found"
            )

        rule.action = action

        return rule
    
    def list_operations(
        self,
        draft_id,
        ruleset_id,
        rule_id,
    ):
        rule = self.get_rule(
            draft_id,
            ruleset_id,
            rule_id,
        )

        if rule is None:
            raise ValueError("Rule not found")

        return list(rule.operations)

    def update_operation(
        self,
        draft_id,
        ruleset_id,
        rule_id,
        operation_id,
        name=None,
        parameters=None,
    ):
        operation = self.get_operation(
            draft_id,
            ruleset_id,
            rule_id,
            operation_id,
        )

        if operation is None:
            raise ValueError("Operation not found")

        if name is not None:
            if not isinstance(name, str) or not name.strip():
                raise ValueError(
                    "Operation name must be a non-empty string"
                )

            operation.name = name

        if parameters is not None:
            if not isinstance(parameters, dict):
                raise ValueError(
                    "Operation parameters must be a dictionary"
                )

            operation.parameters = dict(parameters)

        return operation

    def reorder_operations(
        self,
        draft_id,
        ruleset_id,
        rule_id,
        operation_ids,
    ):
        rule = self.get_rule(
            draft_id,
            ruleset_id,
            rule_id,
        )

        if rule is None:
            raise ValueError("Rule not found")

        if not isinstance(operation_ids, list):
            raise ValueError(
                "operation_ids must be a list"
            )

        existing_ids = {
            operation.id for operation in rule.operations
        }

        requested_ids = set(operation_ids)

        if (
            len(operation_ids) != len(requested_ids)
            or requested_ids != existing_ids
        ):
            raise ValueError(
                "operation_ids must contain every operation ID "
                "exactly once"
            )

        operations_by_id = {
            operation.id: operation
            for operation in rule.operations
        }

        rule.operations = [
            operations_by_id[operation_id]
            for operation_id in operation_ids
        ]

        return list(rule.operations)  