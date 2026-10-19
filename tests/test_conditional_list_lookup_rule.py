
from configuration.models.firewall_config import FirewallConfiguration
from configuration.models.ruleset_config import RulesetConfig
from configuration.models.rule_config import RuleConfig
from configuration.models.condition_group_config import ConditionGroupConfig
from configuration.models.condition_config import ConditionConfig
from configuration.models.operation_config import OperationConfig
from configuration.models.action_config import ActionConfig

from conditions.enums import SourceType, Operator, MatchMode
from conditions.evaluator import ConditionEvaluator
from conditions.group_evaluator import ConditionGroupEvaluator

from engine.context import ExecutionContext
from lists.list_column import ListColumn
from lists.list_manager import ListManager
from lists.list_repository import ListRepository
from storage.json_storage import JsonStorage

from rules.evaluator import RuleEvaluator
from rules.operation_executor import OperationExecutor
from rulesets.executor import RulesetExecutor
from rulesets.registry import RulesetRegistry
from runtime.builder import RuntimeBuilder


def build_test_runtime(list_manager):
    operation_executor = OperationExecutor(
        list_manager=list_manager
    )

    rule_evaluator = RuleEvaluator(
        condition_group_evaluator=ConditionGroupEvaluator(
            ConditionEvaluator()
        ),
        operation_executor=operation_executor,
    )

    registry = RulesetRegistry()

    return RulesetExecutor(
        rule_evaluator=rule_evaluator,
        registry=registry,
    ), registry


def test_list_lookup_runs_only_when_rule_conditions_match(tmp_path):
    list_manager = ListManager(
        repository=ListRepository(
            storage=JsonStorage(folder=tmp_path / "lists")
        )
    )

    definition = list_manager.create_list(
        name="sender_records",
        columns=[
            ListColumn(
                name="sender",
                datatype="String",
                unique=True,
            ),
            ListColumn(
                name="action",
                datatype="String",
            ),
        ],
        rows=[
            {
                "sender": "alice@example.com",
                "action": "REVIEW",
            }
        ],
    )

    # Create the rule configuration.
    rule_config = RuleConfig(name="Lookup sender")

    rule_config.set_condition_group(
        ConditionGroupConfig(
            operator="AND",
            conditions=[
                ConditionConfig(
                    left_type=SourceType.PARAMETER.value,
                    left_name="sender_address",
                    operator=Operator.EXISTS.value,
                    match_mode=MatchMode.ANY.value,
                )
            ],
        )
    )

    rule_config.add_operation(
        OperationConfig(
            name="list-lookup",
            parameters={
                "list_alias": definition.alias,
                "conditions": [
                    {
                        "column": "sender",
                        "operator": "Equals",
                        "value": {
                            "type": "Parameter",
                            "name": "sender_address",
                        },
                    }
                ],
                "result_parameter": "sender_lookup_result",
            },
        )
    )

    rule_config.set_action(
        ActionConfig(type="CONTINUE")
    )

    ruleset_config = RulesetConfig(name="Sender lookup")
    ruleset_config.add_rule(rule_config)

    firewall_configuration = FirewallConfiguration()
    firewall_configuration.add_ruleset(ruleset_config)

    # Build and register the runtime ruleset.
    runtime_builder = RuntimeBuilder()
    runtime_rulesets = runtime_builder.build_rulesets(
        firewall_configuration
    )

    executor, registry = build_test_runtime(list_manager)

    registry.register(runtime_rulesets[0])

    # Case 1: the required input parameter is missing.
    context = ExecutionContext(list_manager=list_manager)

    result = executor.execute(
        registry.get("Sender lookup"),
        context,
    )

    assert result is None
    assert context.get_parameter("sender_lookup_result") is None

    # Case 2: the condition matches, so lookup runs.
    context.set_parameter(
        name="sender_address",
        value="alice@example.com",
        datatype="String",
    )

    result = executor.execute(
        registry.get("Sender lookup"),
        context,
    )

    assert result is not None
    assert result.__class__.__name__ == "ContinueAction"

    lookup_result = context.get_parameter("sender_lookup_result")

    assert lookup_result is not None
    assert lookup_result.value["sender"] == "alice@example.com"
    assert lookup_result.value["action"] == "REVIEW"