
import copy

import pytest

from configuration.models.firewall_config import FirewallConfiguration
from configuration.models.ruleset_config import RulesetConfig
from configuration.models.rule_config import RuleConfig
from configuration.models.operation_config import OperationConfig

from engine.context import ExecutionContext

from lists.list_column import ListColumn
from lists.list_manager import ListManager
from lists.list_repository import ListRepository

from storage.json_storage import JsonStorage

from versions.version_repository import VersionRepository
from versions.version_service import VersionService

from operations.lookup.list_lookup import execute as list_lookup_execute


@pytest.fixture
def environment(tmp_path):
    """Create independent list and version storage for each test."""

    list_storage = JsonStorage(
        folder=tmp_path / "lists"
    )
    list_repository = ListRepository(
        storage=list_storage
    )
    list_manager = ListManager(
        repository=list_repository
    )

    version_storage = JsonStorage(
        folder=tmp_path / "versions"
    )
    version_repository = VersionRepository()
    version_service = VersionService(
        repository=version_repository,
        storage=version_storage,
    )

    definition = list_manager.create_list(
        name="sender_rules",
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
                "sender": "12344",
                "action": "BLOCK",
            },
        ],
    )

    operation_parameters = {
        "list_alias": definition.alias,
        "conditions": [
            {
                "column": "sender",
                "operator": "Equals",
                "value": "12344",
            },
        ],
        "result_parameter": "matched_sender",
    }

    rule = RuleConfig(
        name="Sender blocklist lookup",
        order=1,
    )

    # Preserve the exact lookup configuration independently
    # of the list's mutable row values.
    rule.add_operation(
        OperationConfig(
            name="list-lookup",
            parameters=copy.deepcopy(operation_parameters),
        )
    )

    configuration = FirewallConfiguration()
    ruleset = RulesetConfig(name="Security")
    ruleset.add_rule(rule)
    configuration.add_ruleset(ruleset)

    version = version_service.create_version(
        configuration,
        name="Initial configuration",
    )

    return {
        "list_manager": list_manager,
        "list_storage": list_storage,
        "version_service": version_service,
        "version_storage": version_storage,
        "version": version,
        "alias": definition.alias,
        "operation_parameters": operation_parameters,
    }


def execute_lookup(environment):
    context = ExecutionContext(
        list_manager=environment["list_manager"]
    )

    return list_lookup_execute(
        context,
        copy.deepcopy(environment["operation_parameters"]),
    )


def test_list_update_does_not_modify_firewall_version(environment):
    version = environment["version"]
    original_id = version.id
    original_number = version.number
    original_configuration = copy.deepcopy(
        version.configuration
    )

    environment["list_manager"].update_cell(
        environment["alias"],
        0,
        "action",
        "ALLOW",
    )

    assert version.id == original_id
    assert version.number == original_number
    assert version.configuration == original_configuration

    saved_version = environment["version_storage"].load(
        f"version_{version.number}"
    )

    assert saved_version["id"] == str(original_id)
    assert saved_version["configuration"] == (
        environment["version_service"].serializer.serialize(
            original_configuration
        )
    )


def test_existing_rule_uses_updated_list_values(environment):
    # The rule initially finds the original sender.
    first_result = execute_lookup(environment)

    assert first_result["match"] is True
    assert first_result["row"]["sender"] == "12344"

    # Change the list without changing the rule.
    environment["list_manager"].update_cell(
        environment["alias"],
        0,
        "sender",
        "99999",
    )

    # The existing lookup conditions no longer match.
    second_result = execute_lookup(environment)

    assert second_result["match"] is False
    assert second_result["count"] == 0

    # The firewall rule configuration remains unchanged.
    rule = (
        environment["version"]
        .configuration.rulesets[0]
        .rules[0]
    )

    assert (
        rule.operations[0].parameters
        == environment["operation_parameters"]
    )


def test_list_updates_survive_reloading_list_manager(environment):
    alias = environment["alias"]

    environment["list_manager"].add_row(
        alias,
        {
            "sender": "99999",
            "action": "ALLOW",
        },
    )

    reloaded_repository = ListRepository(
        storage=JsonStorage(
            folder=environment["list_storage"].folder
        )
    )
    reloaded_manager = ListManager(
        repository=reloaded_repository
    )

    rows = reloaded_manager.get_rows(alias)

    assert len(rows) == 2
    assert rows[1] == {
        "sender": "99999",
        "action": "ALLOW",
    }


def test_switching_firewall_versions_does_not_restore_old_list_data(
    environment,
):
    service = environment["version_service"]
    original_version = environment["version"]

    second_version = service.create_version(
        original_version.configuration,
        name="Second configuration",
    )

    environment["list_manager"].update_cell(
        environment["alias"],
        0,
        "sender",
        "99999",
    )

    service.switch_version(original_version.id)

    assert original_version.status == "WORKING"

    rows = environment["list_manager"].get_rows(
        environment["alias"]
    )

    assert rows[0]["sender"] == "99999"

    # Switching to another firewall version must not roll
    # back the independently stored list values.
    service.switch_version(second_version.id)

    assert second_version.status == "WORKING"
    assert (
        environment["list_manager"].get_rows(
            environment["alias"]
        )[0]["sender"]
        == "99999"
    )