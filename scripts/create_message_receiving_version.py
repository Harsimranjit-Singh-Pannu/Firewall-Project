
from configuration.models.firewall_config import FirewallConfiguration
from configuration.models.ruleset_config import RulesetConfig
from configuration.models.rule_config import RuleConfig
from configuration.models.condition_group_config import ConditionGroupConfig
from configuration.models.condition_config import ConditionConfig
from configuration.models.action_config import ActionConfig

from conditions.enums import SourceType, Operator, MatchMode

from storage.json_storage import JsonStorage
from versions.version_repository import VersionRepository
from versions.version_service import VersionService


def main():
    storage = JsonStorage("storage/versions")

    service = VersionService(
        repository=VersionRepository(),
        storage=storage,
    )

    # Prevent accidental duplicate creation.
    existing = [
        version
        for version in service.list_versions()
        if version.name == "Message Receiving Foundation"
    ]

    if existing:
        version = existing[0]
        print(
            f"Version already exists: {version.number} "
            f"({version.name})"
        )
        return

    rule = RuleConfig(name="Check received message sender")

    rule.set_condition_group(
        ConditionGroupConfig(
            operator="AND",
            conditions=[
                ConditionConfig(
                    left_type=SourceType.PARAMETER.value,
                    left_name="Message-Sender",
                    operator=Operator.EXISTS.value,
                    match_mode=MatchMode.ANY.value,
                )
            ],
        )
    )

    rule.set_action(ActionConfig(type="CONTINUE"))

    ruleset = RulesetConfig(name="Message Receiving")
    ruleset.add_rule(rule)

    configuration = FirewallConfiguration()
    configuration.add_ruleset(ruleset)

    version = service.create_version(
        configuration=configuration,
        name="Message Receiving Foundation",
        description=(
            "Initial persistent ruleset for consuming "
            "message reception system parameters"
        ),
    )

    print(f"Created version: {version.number}")
    print(f"Name: {version.name}")
    print(f"ID: {version.id}")
    print(f"Status: {version.status}")


if __name__ == "__main__":
    main()