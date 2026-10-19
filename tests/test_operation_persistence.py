import json
from storage.json_storage import JsonStorage
from configuration.models.firewall_config import FirewallConfiguration
from configuration.services.ruleset_service import RulesetService
from configuration.services.rule_service import RuleService

from drafts.draft_repository import DraftRepository
from drafts.draft_service import DraftService

from versions.version_service import VersionService
from versions.version_repository import VersionRepository


def test_operation_survives_version_commit_and_reload(
    tmp_path
):

    version_repository = VersionRepository()

    version_service = VersionService(
    repository=version_repository,
    storage=JsonStorage(
        folder=tmp_path / "versions"
    )
)

    configuration = FirewallConfiguration()

    base_version = version_service.create_version(
        configuration=configuration,
        name="Base Version"
    )

    draft_repository = DraftRepository()

    draft_service = DraftService(
        repository=draft_repository,
        version_service=version_service
    )

    draft = draft_service.create_draft(

        version_id=base_version.id,

        configuration=base_version.configuration

    )

    ruleset_service = RulesetService(
        draft_service
    )

    ruleset = ruleset_service.create_ruleset(
        draft.id,
        "Web Security"
    )

    rule = ruleset_service.add_rule(
        draft.id,
        ruleset.id,
        "Allow Web Traffic"
    )

    rule_service = RuleService(
        draft_service
    )

    operation = rule_service.create_operation(

        draft.id,

        ruleset.id,

        rule.id,

        "set-parameter",

        {
            "name": "risk",
            "value": 10,
            "scope": "REQUEST"
        }

    )

    committed_version = version_service.create_version(

        configuration=draft.configuration,

        name="Web Traffic Version"

    )

    assert (
        len(
            committed_version.configuration.rulesets
        )
        == 1
    )

    committed_ruleset = (
        committed_version.configuration.rulesets[0]
    )

    assert len(
        committed_ruleset.rules
    ) == 1

    committed_rule = (
        committed_ruleset.rules[0]
    )

    assert len(
        committed_rule.operations
    ) == 1

    committed_operation = (
        committed_rule.operations[0]
    )

    assert (
        committed_operation.name
        == "set-parameter"
    )

    assert (
        committed_operation.id
        == operation.id
    )

    assert (
        committed_operation.parameters
        == {
            "name": "risk",
            "value": 10,
            "scope": "REQUEST"
        }
    )