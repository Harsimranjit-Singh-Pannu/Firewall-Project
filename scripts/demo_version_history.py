from versions.version_repository import VersionRepository
from versions.version_service import VersionService

from configuration.models.firewall_config import FirewallConfiguration
from configuration.models.ruleset_config import RulesetConfig
from configuration.models.rule_config import RuleConfig


repository = VersionRepository()

service = VersionService(
    repository=repository
)


# ==========================================================
# VERSION 1
# ==========================================================

configuration = FirewallConfiguration()

configuration.add_ruleset(
    RulesetConfig(
        name="Base Security"
    )
)

version1 = service.create_version(
    configuration=configuration,
    name="Base Version",
    description="Initial firewall configuration"
)

print("Created Version 1")


# ==========================================================
# VERSION 2 FROM VERSION 1
# ==========================================================

version2 = service.create_version_from_version(
    version1.id,
    name="Web Traffic Update",
    description="Allow web traffic"
)

ruleset2 = version2.configuration.rulesets[0]

ruleset2.add_rule(
    RuleConfig(
        name="Allow Web Traffic",
        order=1
    )
)

service._save_version(
    version2
)

print("Created Version 2")


# ==========================================================
# VERSION 3 FROM VERSION 2
# ==========================================================

version3 = service.create_version_from_version(
    version2.id,
    name="Version 3",
    description="Further web configuration"
)

print("Created Version 3")


# ==========================================================
# SWITCH BACK TO VERSION 1
# ==========================================================

service.switch_version(
    version1.id
)

print("Switched back to Version 1")


# ==========================================================
# VERSION 4 FROM VERSION 1
# ==========================================================

version4 = service.create_version_from_version(
    version1.id,
    name="Version 4",
    description="New configuration after rollback"
)

print("Created Version 4")


# ==========================================================
# DISPLAY HISTORY
# ==========================================================

print()
print("=" * 60)
print("VERSION HISTORY")
print("=" * 60)

for version in service.list_versions():

    print()
    print("Version :", version.number)
    print("Name    :", version.name)
    print("ID      :", version.id)
    print("Parent  :", version.parent_version_id)
    print("Status  :", version.status)

    for ruleset in version.configuration.rulesets:

        print("Ruleset :", ruleset.name)
        print("Rules   :", len(ruleset.rules))

print()
print("Version files should now exist in:")
print("storage/versions/")