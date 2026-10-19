from versions.version_repository import VersionRepository
from versions.version_service import VersionService
from configuration.models.firewall_config import FirewallConfiguration
from configuration.models.ruleset_config import RulesetConfig


repository = VersionRepository()

service = VersionService(
    repository=repository
)


configuration = FirewallConfiguration()

configuration.add_ruleset(
    RulesetConfig(
        name="Base Security"
    )
)


version = service.create_version(
    configuration=configuration,
    name="Base Version",
    description="Initial firewall configuration"
)


print()
print("Created base version")
print("--------------------")
print("Version :", version.number)
print("Name    :", version.name)
print("ID      :", version.id)
print("Status  :", version.status)
print("Rulesets:", len(version.configuration.rulesets))
print()