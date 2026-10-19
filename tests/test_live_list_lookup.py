
from types import SimpleNamespace

from lists.list_column import ListColumn
from lists.list_manager import ListManager
from lists.list_repository import ListRepository
from storage.json_storage import JsonStorage
from engine.context import ExecutionContext
from rules.operation_executor import OperationExecutor

from configuration.models.firewall_config import FirewallConfiguration
from configuration.models.ruleset_config import RulesetConfig
from versions.version_repository import VersionRepository
from versions.version_service import VersionService


def test_live_list_update_does_not_require_new_configuration_version(
    tmp_path,
):
    # ---------------------------------------------------------
    # 1. Create an isolated list manager
    # ---------------------------------------------------------

    list_storage = JsonStorage(
        folder=tmp_path / "lists"
    )

    list_manager = ListManager(
        repository=ListRepository(
            storage=list_storage
        )
    )

    definition = list_manager.create_list(
        name="sender_blocklist",
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
                "action": "BLOCK",
            },
        ],
    )

    alias = definition.alias

    # ---------------------------------------------------------
    # 2. Create one firewall configuration version
    # ---------------------------------------------------------

    version_service = VersionService(
        repository=VersionRepository(),
        storage=JsonStorage(
            folder=tmp_path / "versions"
        ),
    )

    configuration = FirewallConfiguration()
    configuration.add_ruleset(
        RulesetConfig(name="Security")
    )

    version = version_service.create_version(
        configuration,
        name="Initial",
    )

    original_version_count = len(
        version_service.list_versions()
    )

    # ---------------------------------------------------------
    # 3. Build the lookup operation
    # ---------------------------------------------------------

    operation = SimpleNamespace(
        name="list-lookup",
        parameters={
            "list_alias": alias,
            "conditions": [
                {
                    "column": "sender",
                    "operator": "Equals",
                    "value": "alice@example.com",
                },
            ],
            "result_parameter": "sender_result",
        },
    )

    context = ExecutionContext(
        list_manager=list_manager
    )

    executor = OperationExecutor(
        list_manager=list_manager
    )

    # ---------------------------------------------------------
    # 4. First execution reads BLOCK
    # ---------------------------------------------------------

    first_result = executor.execute(
        operation,
        context,
    )

    assert first_result["success"] is True
    assert first_result["match"] is True
    assert first_result["row"]["action"] == "BLOCK"

    first_parameter = context.get_parameter(
        "sender_result"
    )

    assert first_parameter.value["action"] == "BLOCK"

    # ---------------------------------------------------------
    # 5. Update the list without changing the configuration
    # ---------------------------------------------------------

    list_manager.update_cell(
        alias,
        row_index=0,
        column_name="action",
        value="ALLOW",
    )

    # ---------------------------------------------------------
    # 6. Execute the same operation again
    # ---------------------------------------------------------

    second_result = executor.execute(
        operation,
        context,
    )

    assert second_result["success"] is True
    assert second_result["match"] is True
    assert second_result["row"]["action"] == "ALLOW"

    second_parameter = context.get_parameter(
        "sender_result"
    )

    assert second_parameter.value["action"] == "ALLOW"

    # ---------------------------------------------------------
    # 7. The firewall configuration version is unchanged
    # ---------------------------------------------------------

    assert version_service.get_version(version.id) is version

    assert len(
        version_service.list_versions()
    ) == original_version_count

    assert version.configuration.rulesets[0].name == "Security"