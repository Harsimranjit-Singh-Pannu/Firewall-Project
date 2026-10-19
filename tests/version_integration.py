import shutil
from pathlib import Path

from configuration.models.firewall_config import (
    FirewallConfiguration
)

from configuration.models.ruleset_config import (
    RulesetConfig
)

from versions.version_repository import VersionRepository
from versions.version_service import VersionService

from configuration.models.firewall_config import FirewallConfiguration
from configuration.models.ruleset_config import RulesetConfig
from configuration.models.rule_config import RuleConfig

from storage.json_storage import JsonStorage


STORAGE_PATH = Path("storage/versions")


def build_configuration(
    ruleset_name="Security"
):
    configuration = FirewallConfiguration()

    configuration.add_ruleset(
        RulesetConfig(
            name=ruleset_name
        )
    )

    return configuration


def build_service():
    repository = VersionRepository()

    storage = JsonStorage(
        STORAGE_PATH
    )

    return VersionService(
        repository=repository,
        storage=storage
    )


class TestVersionRealStorage:

    def setup_method(self):

        STORAGE_PATH.mkdir(
            parents=True,
            exist_ok=True
        )

        for file in STORAGE_PATH.glob(
            "version_*.json"
        ):
            file.unlink()


    def teardown_method(self):

        for file in STORAGE_PATH.glob(
            "version_*.json"
        ):
            file.unlink()


    def test_create_versions_from_previous_version(self):

        service = build_service()

        # -------------------------------------------------
        # Version 1
        # -------------------------------------------------

        version_1 = service.create_version(
            build_configuration(
                "Original Rules"
            ),
            name="Version One",
            description="Original configuration"
        )

        assert version_1.number == 1

        assert (
            version_1.configuration.rulesets[0].name
            == "Original Rules"
        )


        # -------------------------------------------------
        # Version 2
        # -------------------------------------------------

        version_1_configuration = (
            version_1.configuration
        )

        version_2_configuration = (
            __import__("copy").deepcopy(
                version_1_configuration
            )
        )

        version_2_configuration.rulesets[0].name = (
            "Version Two Rules"
        )

        version_2 = service.create_version(
            version_2_configuration,
            name="Version Two",
            description="Changes based on Version One"
        )


        assert version_2.number == 2

        assert (
            version_2.configuration.rulesets[0].name
            == "Version Two Rules"
        )


        # -------------------------------------------------
        # Version 1 must remain unchanged
        # -------------------------------------------------

        assert (
            version_1.configuration.rulesets[0].name
            == "Original Rules"
        )


        # -------------------------------------------------
        # Both versions must exist
        # -------------------------------------------------

        versions = service.list_versions()

        assert len(versions) == 2

        assert versions[0].number == 1
        assert versions[1].number == 2


    def test_switch_back_to_old_version_and_create_new_version(
        self
    ):

        service = build_service()


        # -------------------------------------------------
        # Version 1
        # -------------------------------------------------

        version_1 = service.create_version(
            build_configuration(
                "Original"
            ),
            name="Version One"
        )


        # -------------------------------------------------
        # Version 2
        # -------------------------------------------------

        version_2_configuration = (
            __import__("copy").deepcopy(
                version_1.configuration
            )
        )

        version_2_configuration.rulesets[0].name = (
            "Version Two"
        )

        version_2 = service.create_version(
            version_2_configuration,
            name="Version Two"
        )


        # -------------------------------------------------
        # Switch back to Version 1
        # -------------------------------------------------

        result = service.switch_version(
            version_1.id
        )

        assert result is version_1

        assert version_1.status == "WORKING"

        assert version_2.status == "AVAILABLE"


        # -------------------------------------------------
        # Create Version 3 from Version 1
        # -------------------------------------------------

        version_3_configuration = (
            __import__("copy").deepcopy(
                version_1.configuration
            )
        )

        version_3_configuration.rulesets[0].name = (
            "Version Three"
        )

        version_3 = service.create_version(
            version_3_configuration,
            name="Version Three",
            description="New branch from Version One"
        )


        # -------------------------------------------------
        # Version numbers are never reused
        # -------------------------------------------------

        assert version_1.number == 1
        assert version_2.number == 2
        assert version_3.number == 3


        # -------------------------------------------------
        # Version 1 remains unchanged
        # -------------------------------------------------

        assert (
            version_1.configuration.rulesets[0].name
            == "Original"
        )


        # -------------------------------------------------
        # Version 2 remains unchanged
        # -------------------------------------------------

        assert (
            version_2.configuration.rulesets[0].name
            == "Version Two"
        )


        # -------------------------------------------------
        # Version 3 is based on Version 1
        # -------------------------------------------------

        assert (
            version_3.configuration.rulesets[0].name
            == "Version Three"
        )


        # -------------------------------------------------
        # All three versions still exist
        # -------------------------------------------------

        versions = service.list_versions()

        assert len(versions) == 3

        assert [
            version.number
            for version in versions
        ] == [1, 2, 3]


    def test_versions_survive_service_reload(self):

        service = build_service()


        # -------------------------------------------------
        # Create Version 1
        # -------------------------------------------------

        version_1 = service.create_version(
            build_configuration(
                "Production Rules"
            ),
            name="Production",
            description="Production baseline"
        )


        # -------------------------------------------------
        # Create Version 2
        # -------------------------------------------------

        version_2_configuration = (
            __import__("copy").deepcopy(
                version_1.configuration
            )
        )

        version_2_configuration.rulesets[0].name = (
            "Updated Production Rules"
        )

        version_2 = service.create_version(
            version_2_configuration,
            name="Updated Production"
        )


        # -------------------------------------------------
        # Create a new service.
        #
        # This simulates restarting the application.
        # -------------------------------------------------

        reloaded_service = build_service()


        # -------------------------------------------------
        # Verify both versions were loaded
        # -------------------------------------------------

        versions = reloaded_service.list_versions()

        assert len(versions) == 2


        # -------------------------------------------------
        # Verify Version 1
        # -------------------------------------------------

        reloaded_version_1 = (
            reloaded_service.get_version(
                version_1.id
            )
        )

        assert reloaded_version_1 is not None

        assert reloaded_version_1.number == 1

        assert reloaded_version_1.name == (
            "Production"
        )

        assert reloaded_version_1.description == (
            "Production baseline"
        )

        assert (
            reloaded_version_1
            .configuration
            .rulesets[0]
            .name
            == "Production Rules"
        )


        # -------------------------------------------------
        # Verify Version 2
        # -------------------------------------------------

        reloaded_version_2 = (
            reloaded_service.get_version(
                version_2.id
            )
        )

        assert reloaded_version_2 is not None

        assert reloaded_version_2.number == 2

        assert reloaded_version_2.name == (
            "Updated Production"
        )

        assert (
            reloaded_version_2
            .configuration
            .rulesets[0]
            .name
            == "Updated Production Rules"
        )


    def test_push_old_known_good_version(self):

        service = build_service()


        # -------------------------------------------------
        # Version 1 - known good
        # -------------------------------------------------

        version_1 = service.create_version(
            build_configuration(
                "Known Good"
            ),
            name="Known Good"
        )


        # -------------------------------------------------
        # Version 2 - broken
        # -------------------------------------------------

        version_2_configuration = (
            __import__("copy").deepcopy(
                version_1.configuration
            )
        )

        version_2_configuration.rulesets[0].name = (
            "Broken Configuration"
        )

        version_2 = service.create_version(
            version_2_configuration,
            name="Broken"
        )


        # -------------------------------------------------
        # Push Version 1
        # -------------------------------------------------

        result = service.push_version(
            version_1.id
        )

        assert result is version_1

        assert version_1.status == "ACTIVE"

        assert version_2.status == "AVAILABLE"


        # -------------------------------------------------
        # Version 2 must still exist
        # -------------------------------------------------

        assert (
            service.get_version(
                version_2.id
            )
            is version_2
        )


    def test_switch_does_not_delete_versions(self):

        service = build_service()


        version_1 = service.create_version(
            build_configuration(
                "Version One"
            ),
            name="Version One"
        )

        version_2 = service.create_version(
            build_configuration(
                "Version Two"
            ),
            name="Version Two"
        )

        version_3 = service.create_version(
            build_configuration(
                "Version Three"
            ),
            name="Version Three"
        )


        # Switch to Version 1

        service.switch_version(
            version_1.id
        )


        # All versions must still exist

        assert (
            service.get_version(
                version_1.id
            )
            is version_1
        )

        assert (
            service.get_version(
                version_2.id
            )
            is version_2
        )

        assert (
            service.get_version(
                version_3.id
            )
            is version_3
        )


        assert len(
            service.list_versions()
        ) == 3
    def test_full_version_branching_and_rollback(self):

        repository = VersionRepository()

        service = VersionService(
            repository=repository
        )

        # --------------------------------------------------
        # Version 1 - base configuration
        # --------------------------------------------------

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

        assert version1.number == 1
        assert version1.parent_version_id is None
        assert len(
            version1.configuration.rulesets
        ) == 1

        # --------------------------------------------------
        # Version 2 - created from Version 1
        # --------------------------------------------------

        version2 = service.create_version_from_version(
            version1.id,
            name="Web Traffic Update",
            description="Allow web traffic"
        )

        assert version2.number == 2
        assert version2.parent_version_id == version1.id

        # Version 2 starts with Version 1 configuration
        assert len(
            version2.configuration.rulesets
        ) == 1

        assert (
            version2.configuration.rulesets[0].name
            == "Base Security"
        )

        # --------------------------------------------------
        # Modify Version 2
        # --------------------------------------------------

        ruleset2 = (
            version2.configuration.rulesets[0]
        )

        ruleset2.add_rule(
            RuleConfig(
                name="Allow Web Traffic",
                order=1
            )
        )

        service._save_version(
            version2
        )

        # Version 2 has the new rule
        assert len(
            version2.configuration.rulesets[0].rules
        ) == 1

        # Version 1 must remain unchanged
        assert len(
            version1.configuration.rulesets[0].rules
        ) == 0

        # --------------------------------------------------
        # Version 3 - created from Version 2
        # --------------------------------------------------

        version3 = service.create_version_from_version(
            version2.id,
            name="Version 3",
            description="Further web configuration"
        )

        assert version3.number == 3
        assert version3.parent_version_id == version2.id

        # Version 3 inherits Version 2's rule
        assert len(
            version3.configuration.rulesets[0].rules
        ) == 1

        assert (
            version3.configuration.rulesets[0].rules[0].name
            == "Allow Web Traffic"
        )

        # --------------------------------------------------
        # Roll back to Version 1
        # --------------------------------------------------

        service.switch_version(
            version1.id
        )

        assert version1.status == "WORKING"

        assert version2.status == "AVAILABLE"
        assert version3.status == "AVAILABLE"

        # --------------------------------------------------
        # Version 4 - new branch from Version 1
        # --------------------------------------------------

        version4 = service.create_version_from_version(
            version1.id,
            name="Version 4",
            description="New configuration after rollback"
        )

        assert version4.number == 4

        # Version 4 branches from Version 1
        assert version4.parent_version_id == version1.id

        # Version 4 inherits Version 1's configuration,
        # NOT Version 2 or Version 3's configuration.
        assert len(
            version4.configuration.rulesets
        ) == 1

        assert len(
            version4.configuration.rulesets[0].rules
        ) == 0

        # --------------------------------------------------
        # All four versions must still exist
        # --------------------------------------------------

        versions = service.list_versions()

        assert len(versions) == 4

        assert [version.number for version in versions] == [
            1,
            2,
            3,
            4
        ]

        # --------------------------------------------------
        # Verify parent relationships
        # --------------------------------------------------

        assert version1.parent_version_id is None

        assert version2.parent_version_id == version1.id

        assert version3.parent_version_id == version2.id

        assert version4.parent_version_id == version1.id

        # --------------------------------------------------
        # Verify old configurations remain intact
        # --------------------------------------------------

        assert len(
            version1.configuration.rulesets[0].rules
        ) == 0

        assert len(
            version2.configuration.rulesets[0].rules
        ) == 1

        assert len(
            version3.configuration.rulesets[0].rules
        ) == 1

        assert len(
            version4.configuration.rulesets[0].rules
        ) == 0