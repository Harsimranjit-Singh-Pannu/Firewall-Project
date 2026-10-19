
from configuration.models.firewall_config import FirewallConfiguration
from configuration.models.ruleset_config import RulesetConfig
from configuration.models.rule_config import RuleConfig
from configuration.models.condition_group_config import ConditionGroupConfig
from configuration.models.condition_config import ConditionConfig
from configuration.models.action_config import ActionConfig

from conditions.enums import SourceType, Operator, MatchMode
from conditions.evaluator import ConditionEvaluator
from conditions.group_evaluator import ConditionGroupEvaluator

from engine.context import ExecutionContext
from rules.evaluator import RuleEvaluator
from rules.operation_executor import OperationExecutor
from runtime.runtime import FirewallRuntime


def build_configuration():
    rule = RuleConfig(name="Check sender")

    rule.set_condition_group(
        ConditionGroupConfig(
            operator="AND",
            conditions=[
                ConditionConfig(
                    left_type=SourceType.PARAMETER.value,
                    left_name="sender",
                    operator=Operator.EXISTS.value,
                    match_mode=MatchMode.ANY.value,
                )
            ],
        )
    )

    rule.set_action(
        ActionConfig(type="CONTINUE")
    )

    ruleset = RulesetConfig(name="Sender rules")
    ruleset.add_rule(rule)

    configuration = FirewallConfiguration()
    configuration.add_ruleset(ruleset)

    return configuration


def build_runtime(configuration):
    evaluator = RuleEvaluator(
        condition_group_evaluator=ConditionGroupEvaluator(
            ConditionEvaluator()
        ),
        operation_executor=OperationExecutor(),
    )

    return FirewallRuntime(
        configuration=configuration,
        rule_evaluator=evaluator,
    )


def test_runtime_executes_matching_rule():
    runtime = build_runtime(build_configuration())
    context = ExecutionContext()

    context.set_parameter(
        name="sender",
        value="alice@example.com",
        datatype="String",
    )

    result = runtime.execute(
        "Sender rules",
        context,
    )

    assert result is not None
    assert result.__class__.__name__ == "ContinueAction"
    assert context.get_ruleset_path() == []


def test_runtime_skips_rule_when_condition_does_not_match():
    runtime = build_runtime(build_configuration())
    context = ExecutionContext()

    result = runtime.execute(
        "Sender rules",
        context,
    )

    assert result is None
    assert context.get_ruleset_path() == []