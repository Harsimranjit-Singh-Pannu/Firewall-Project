import copy

from configuration.models.ruleset_config import RulesetConfig

from rulesets.ruleset import Ruleset
from rules.rule import Rule

from actions.action_executor import ActionExecutor

from conditions.group import (
    ConditionGroup,
    GroupOperator
)

from conditions.enums import (
    SourceType,
    RightSourceType,
    MatchMode,
    Operator
)


class RuntimeBuilder:

    def __init__(
        self
    ):

        self.action_executor = ActionExecutor()

    def build_ruleset(
        self,
        ruleset_config: RulesetConfig
    ):

        ruleset = Ruleset(

            name=ruleset_config.name

        )

        for rule_config in ruleset_config.rules:

            rule = self.build_rule(

                rule_config

            )

            ruleset.add_rule(

                rule

            )

        return ruleset

    def build_rulesets(
        self,
        firewall_configuration
    ):

        runtime_rulesets = []

        for ruleset_config in firewall_configuration.rulesets:

            runtime_rulesets.append(

                self.build_ruleset(

                    ruleset_config

                )

            )

        return runtime_rulesets

    def build_rule(
        self,
        rule_config
    ):

        rule = Rule(

            name=rule_config.name

        )

        #
        # Conditions
        #

        condition_group = self.build_condition_group(

            rule_config.condition_group

        )

        rule.set_condition_group(

            condition_group

        )

        #
        # Operations
        #

        for operation in rule_config.operations:

            rule.add_operation(

                operation

            )

        #
        # Action
        #

        runtime_action = self.action_executor.build(

            rule_config.action

        )

        rule.set_action(

            runtime_action

        )

        return rule

    def build_condition_group(
        self,
        group_config
    ):

        if group_config is None:

            return None

        try:

            group_operator = GroupOperator(
                group_config.operator
            )

        except ValueError:

            raise ValueError(
                f"Invalid condition group operator: "
                f"{group_config.operator}"
            )

        conditions = []

        for condition_config in group_config.conditions:

            conditions.append(

                self.build_condition(

                    condition_config

                )

            )

        return ConditionGroup(

            operator=group_operator,

            conditions=conditions

        )

    def build_condition(
        self,
        condition_config
    ):

        condition = copy.deepcopy(
            condition_config
        )

        try:

            condition.left_type = SourceType(
                condition.left_type
            )

        except ValueError:

            raise ValueError(
                f"Invalid condition left_type: "
                f"{condition.left_type}"
            )

        try:

            condition.operator = Operator(
                condition.operator
            )

        except ValueError:

            raise ValueError(
                f"Invalid condition operator: "
                f"{condition.operator}"
            )

        try:

            condition.match_mode = MatchMode(
                condition.match_mode
            )

        except ValueError:

            raise ValueError(
                f"Invalid condition match_mode: "
                f"{condition.match_mode}"
            )

        if condition.right_type is not None:

            try:

                condition.right_type = RightSourceType(
                    condition.right_type
                )

            except ValueError:

                raise ValueError(
                    f"Invalid condition right_type: "
                    f"{condition.right_type}"
                )

        return condition