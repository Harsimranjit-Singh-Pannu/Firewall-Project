
import json
from pathlib import Path

from storage.json_storage import JsonStorage

from versions.version_repository import VersionRepository
from versions.version_service import VersionService

from lists.list_manager import ListManager
from lists.list_repository import ListRepository

from engine.context import ExecutionContext

from conditions.condition import Condition
from conditions.enums import (
    SourceType,
    RightSourceType,
    MatchMode,
    Operator,
)
from conditions.group import ConditionGroup, GroupOperator
from conditions.evaluator import ConditionEvaluator
from conditions.group_evaluator import ConditionGroupEvaluator

from rules.operation_executor import OperationExecutor
from rules.evaluator import RuleEvaluator

from runtime.runtime import FirewallRuntime
from actions import ContinueAction
from configuration.models.action_config import ActionConfig


def test_saved_version_executes_real_list_lookup():
    # --------------------------------------------------
    # 1. Load the actual persisted version
    # --------------------------------------------------
    version_path = Path("storage/versions/version_3.json")

    assert version_path.is_file(), (
        f"Saved version does not exist: {version_path}"
    )

    version_data = json.loads(
        version_path.read_text(encoding="utf-8")
    )

    version_service = VersionService(
        repository=VersionRepository(),
        storage=JsonStorage("storage/versions"),
    )

    version = next(
        item
        for item in version_service.list_versions()
        if item.number == version_data["version"]
    )

    configuration = version.configuration

    assert configuration.rulesets, "Version has no rulesets"

    print(f"\n[PASS] Loaded version {version.number}: {version.name}")

    # --------------------------------------------------
    # 2. Find the persisted list-lookup operation
    # --------------------------------------------------
    saved_operations = [
        operation
        for ruleset in version_data["configuration"]["rulesets"]
        for rule in ruleset["rules"]
        for operation in rule.get("operations", [])
        if operation["name"] == "list-lookup"
    ]

    assert saved_operations, (
        "Saved version contains no list-lookup operation"
    )

    lookup_parameters = saved_operations[0]["parameters"]
    alias = lookup_parameters["list_alias"]
    result_name = lookup_parameters["result_parameter"]

    print(f"[PASS] Saved operation references list: {alias}")

    # --------------------------------------------------
    # 3. Reload the actual persistent list
    # --------------------------------------------------
    list_manager = ListManager(
        repository=ListRepository(
            storage=JsonStorage("storage/lists")
        )
    )

    definition = list_manager.get_list(alias)
    rows = list_manager.get_rows(alias)

    assert rows, f"Persisted list {alias} contains no rows"

    expected_row = next(
        (
            row
            for row in rows
            if row.get("sender") == "integration-test@example.com"
        ),
        None,
    )

    assert expected_row is not None, (
        "Expected integration-test sender was not found "
        "in the persisted list"
    )

    assert expected_row["action"] == "BLOCK"

    print(f"[PASS] Reloaded list definition: {definition.name}")
    print(f"[PASS] Reloaded {len(rows)} persisted row(s)")
    print(f"[PASS] Expected row: {expected_row}")

    # --------------------------------------------------
    # 4. Add a valid runtime condition to the lookup rule
    # --------------------------------------------------
    # The saved configuration has condition_group=None.
    # Runtime validation requires every rule to have one.
    #
    # This condition checks a supplied runtime argument.
    # It does not replace or bypass the list-lookup operation.

    lookup_rules = [
        rule
        for ruleset in configuration.rulesets
        for rule in ruleset.rules
        if any(
            operation.name == "list-lookup"
            for operation in rule.operations
        )
    ]

    assert lookup_rules, "No runtime list-lookup rule was found"

    condition = Condition(
    left_type=SourceType.PARAMETER,
    left_name="integration_enabled",
    operator=Operator.EXISTS,
    match_mode=MatchMode.ANY,
)

    for rule in lookup_rules:
        rule.set_condition_group(
            ConditionGroup(
                operator=GroupOperator.AND,
                conditions=[condition],
            )
        )
        # The persisted rule has no action.
        # Add the real action required by Rule.validate().
        rule.set_action(
            ActionConfig(
                type="CONTINUE",
                parameters={},
            )
        )

    print("[PASS] Added valid runtime condition and continueAction")

    # --------------------------------------------------
    # 5. Build the real execution pipeline
    # --------------------------------------------------
    operation_executor = OperationExecutor(
        list_manager=list_manager
    )

    condition_evaluator = ConditionEvaluator()

    condition_group_evaluator = ConditionGroupEvaluator(
        condition_evaluator=condition_evaluator
    )

    rule_evaluator = RuleEvaluator(
        condition_group_evaluator=condition_group_evaluator,
        operation_executor=operation_executor,
    )

    runtime = FirewallRuntime(
        configuration=configuration,
        rule_evaluator=rule_evaluator,
    )

    context = ExecutionContext(
        list_manager=list_manager
    )
    context.set_parameter(
    name="integration_enabled",
    value=True,
    datatype="Boolean",
)

    print("[PASS] Runtime built")

    # --------------------------------------------------
    # 6. Execute the saved ruleset
    # --------------------------------------------------
    ruleset_name = next(
        ruleset.name
        for ruleset in configuration.rulesets
        if any(
            rule in lookup_rules
            for rule in ruleset.rules
        )
    )

    result = runtime.execute(
        ruleset_name=ruleset_name,
        context=context,
    )

    print(f"[PASS] Ruleset executed: {ruleset_name}")
    print(f"[INFO] Runtime result: {result!r}")

    # --------------------------------------------------
    # 7. Verify the actual list-lookup result
    # --------------------------------------------------
    parameter = context.get_parameter(result_name)

    assert parameter is not None, (
        f"Lookup did not create parameter {result_name!r}"
    )

    assert parameter.value["sender"] == (
        "integration-test@example.com"
    )

    assert parameter.value["action"] == "BLOCK"

    assert parameter.value == expected_row

    print(f"[PASS] Result parameter created: {result_name}")
    print(f"[PASS] Lookup returned the expected row: {parameter.value}")
    print("\nEND-TO-END LIST LOOKUP VERIFICATION PASSED")