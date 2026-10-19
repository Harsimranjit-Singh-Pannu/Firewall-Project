import json

from pathlib import Path
from uuid import UUID

import pytest

from versions.version import Version
from versions.version_repository import VersionRepository
from versions.version_service import VersionService

from configuration.models.firewall_config import (
    FirewallConfiguration
)

from configuration.models.ruleset_config import (
    RulesetConfig
)

from storage.json_storage import JsonStorage


def test_failed_save_preserves_existing_file(tmp_path):
    storage = JsonStorage(folder=tmp_path)

    storage.save(
        "version_1",
        {"version": 1, "name": "Original"}
    )

    with pytest.raises(TypeError):
        storage.save(
            "version_1",
            {"version": 1, "invalid": object()}
        )

    saved = storage.load("version_1")

    assert saved == {
        "version": 1,
        "name": "Original"
    }

    assert not list(tmp_path.glob("*.tmp"))

class TestVersion:

    def test_version_has_default_id(self):

        configuration = FirewallConfiguration()

        version = Version(
            number=1,
            configuration=configuration,
            name="Test Version"
        )

        assert version.id is not None
        assert isinstance(
            version.id,
            UUID
        )


    def test_version_has_created_at(self):

        configuration = FirewallConfiguration()

        version = Version(
            number=1,
            configuration=configuration,
            name="Test Version"
        )

        assert version.created_at is not None


    def test_version_defaults_to_available(self):

        configuration = FirewallConfiguration()

        version = Version(
            number=1,
            configuration=configuration,
            name="Test Version"
        )

        assert version.status == "AVAILABLE"


    def test_version_stores_name(self):

        configuration = FirewallConfiguration()

        version = Version(
            number=1,
            configuration=configuration,
            name="My Version"
        )

        assert version.name == "My Version"


    def test_version_stores_description(self):

        configuration = FirewallConfiguration()

        version = Version(
            number=1,
            configuration=configuration,
            name="My Version",
            description="Test description"
        )

        assert version.description == "Test description"


    def test_version_description_can_be_none(self):

        configuration = FirewallConfiguration()

        version = Version(
            number=1,
            configuration=configuration,
            name="My Version"
        )

        assert version.description is None


    def test_version_parent_is_optional(self):

        configuration = FirewallConfiguration()

        version = Version(
            number=1,
            configuration=configuration,
            name="My Version"
        )

        assert version.parent_version_id is None


class TestVersionRepository:

    def setup_method(self):

        self.repository = VersionRepository()


    def build_version(
        self,
        number=1,
        name="Test Version"
    ):

        return Version(
            number=number,
            configuration=FirewallConfiguration(),
            name=name
        )


    def test_save_and_get_version(self):

        version = self.build_version()

        self.repository.save(
            version
        )

        result = self.repository.get(
            version.id
        )

        assert result is version


    def test_get_version_by_string_id(self):

        version = self.build_version()

        self.repository.save(
            version
        )

        result = self.repository.get(
            str(version.id)
        )

        assert result is version


    def test_get_missing_version_returns_none(self):

        result = self.repository.get(
            UUID(
                "00000000-0000-0000-0000-000000000000"
            )
        )

        assert result is None


    def test_list_versions(self):

        first = self.build_version(
            number=1
        )

        second = self.build_version(
            number=2
        )

        self.repository.save(
            first
        )

        self.repository.save(
            second
        )

        versions = self.repository.list()

        assert len(versions) == 2
        assert versions[0] is first
        assert versions[1] is second


    def test_clear_versions(self):

        version = self.build_version()

        self.repository.save(
            version
        )

        self.repository.clear()

        assert self.repository.list() == []
    

class TestVersionService:

    def setup_method(self):

        self.repository = VersionRepository()

        self.storage = JsonStorage(
            folder="storage/test_versions"
        )

        for path in self.storage.list():

            path.unlink()

        self.service = VersionService(
            repository=self.repository,
            storage=self.storage
        )


    def teardown_method(self):

        for path in self.storage.list():

            path.unlink()

        folder = Path(
            "storage/test_versions"
        )

        if folder.exists():

            try:
                folder.rmdir()

            except OSError:
                pass


    def build_service(self):

        return self.service


    def build_configuration(
        self,
        ruleset_name="Security"
    ):

        configuration = FirewallConfiguration()

        configuration.add_ruleset(
            RulesetConfig(
                name=ruleset_name
            )
        )

        return configuration
    
    def test_switch_version_restores_statuses_when_save_fails(
        self,
        monkeypatch,
    ):
        service = self.build_service()

        first = service.create_version(
            self.build_configuration(),
            name="Initial",
        )

        second = service.create_version(
            self.build_configuration("Updated"),
            name="Updated",
        )

        service.switch_version(first.id)

        original_save = service.storage.save
        calls = 0

        def fail_once(name, data):
            nonlocal calls
            calls += 1

            if calls == 2:
                raise OSError(
                    "Simulated storage failure"
                )

            return original_save(name, data)

        monkeypatch.setattr(
            service.storage,
            "save",
            fail_once,
        )

        with pytest.raises(
            OSError,
            match="Simulated storage failure",
        ):
            service.switch_version(second.id)

        assert first.status == "WORKING"
        assert second.status == "AVAILABLE"

    def test_create_version(self):

        service = self.build_service()

        version = service.create_version(
            self.build_configuration(),
            name="Initial"
        )

        assert version.number == 1
        assert version.name == "Initial"
        assert version.status == "AVAILABLE"


    def test_first_version_is_number_one(self):

        service = self.build_service()

        version = service.create_version(
            self.build_configuration(),
            name="Initial"
        )

        assert version.number == 1


    def test_second_version_increments_number(self):

        service = self.build_service()

        first = service.create_version(
            self.build_configuration(),
            name="Initial"
        )

        second = service.create_version(
            self.build_configuration("Updated"),
            name="Updated Configuration"
        )

        assert first.number == 1
        assert second.number == 2


    def test_version_name_is_required(self):

        service = self.build_service()

        with pytest.raises(
            ValueError,
            match="Version name is required"
        ):

            service.create_version(
                self.build_configuration(),
                name=""
            )


    def test_description_is_optional(self):

        service = self.build_service()

        version = service.create_version(
            self.build_configuration(),
            name="Initial"
        )

        assert version.description is None


    def test_create_version_copies_configuration(self):

        service = self.build_service()

        configuration = self.build_configuration()

        version = service.create_version(
            configuration,
            name="Initial"
        )

        assert version.configuration is not configuration


    def test_create_version_deep_copies_configuration(self):

        service = self.build_service()

        configuration = self.build_configuration()

        version = service.create_version(
            configuration,
            name="Initial"
        )

        original_ruleset = (
            configuration.rulesets[0]
        )

        version_ruleset = (
            version.configuration.rulesets[0]
        )

        assert version_ruleset is not original_ruleset


    def test_creating_new_version_does_not_modify_previous_version(self):

        service = self.build_service()

        configuration = self.build_configuration()

        first = service.create_version(
            configuration,
            name="Initial"
        )

        second = service.create_version(
            self.build_configuration("Updated"),
            name="Updated"
        )

        assert first.number == 1
        assert second.number == 2

        assert (
            first.configuration.rulesets[0].name
            == "Security"
        )


    def test_create_new_version_from_previous_configuration(self):

        service = self.build_service()

        first = service.create_version(
            self.build_configuration(),
            name="Initial"
        )

        second = service.create_version_from_version(
            first.id,
            name="Updated"
        )

        assert second.number == 2

        assert (
            second.configuration
            == first.configuration
        )


    def test_create_version_from_previous_version_sets_parent(self):

        service = self.build_service()

        first = service.create_version(
            self.build_configuration(),
            name="Base Version"
        )

        second = service.create_version_from_version(
            first.id,
            name="Web Traffic Update"
        )

        assert second.parent_version_id == first.id


    def test_version_parent_chain(self):

        service = self.build_service()

        version1 = service.create_version(
            self.build_configuration(),
            name="Base Version"
        )

        version2 = service.create_version_from_version(
            version1.id,
            name="Web Traffic Update"
        )

        version3 = service.create_version_from_version(
            version2.id,
            name="Security Update"
        )

        version4 = service.create_version_from_version(
            version3.id,
            name="Final Configuration"
        )

        assert version1.parent_version_id is None

        assert (
            version2.parent_version_id
            == version1.id
        )

        assert (
            version3.parent_version_id
            == version2.id
        )

        assert (
            version4.parent_version_id
            == version3.id
        )


    def test_list_versions(self):

        service = self.build_service()

        service.create_version(
            self.build_configuration(),
            name="Initial"
        )

        service.create_version(
            self.build_configuration("Updated"),
            name="Updated"
        )

        versions = service.list_versions()

        assert len(versions) == 2

        assert versions[0].number == 1
        assert versions[1].number == 2


    def test_get_version(self):

        service = self.build_service()

        version = service.create_version(
            self.build_configuration(),
            name="Initial"
        )

        result = service.get_version(
            version.id
        )

        assert result is not None
        assert result.id == version.id


    def test_switch_version_makes_version_working(self):

        service = self.build_service()

        first = service.create_version(
            self.build_configuration(),
            name="Initial"
        )

        second = service.create_version(
            self.build_configuration("Updated"),
            name="Updated"
        )

        service.switch_version(
            first.id
        )

        assert first.status == "WORKING"
        assert second.status == "AVAILABLE"


    def test_switch_version_can_change_working_version(self):

        service = self.build_service()

        first = service.create_version(
            self.build_configuration(),
            name="Initial"
        )

        second = service.create_version(
            self.build_configuration("Updated"),
            name="Updated"
        )

        service.switch_version(
            first.id
        )

        service.switch_version(
            second.id
        )

        assert first.status == "AVAILABLE"
        assert second.status == "WORKING"


    def test_switch_missing_version_fails(self):

        service = self.build_service()

        with pytest.raises(
            ValueError,
            match="Version not found"
        ):

            service.switch_version(
                UUID(
                    "00000000-0000-0000-0000-000000000000"
                )
            )


    def test_push_version(self):

        service = self.build_service()

        first = service.create_version(
            self.build_configuration(),
            name="Initial"
        )

        service.push_version(
            first.id
        )

        assert first.status == "ACTIVE"


    def test_push_missing_version_fails(self):

        service = self.build_service()

        with pytest.raises(
            ValueError,
            match="Version not found"
        ):

            service.push_version(
                UUID(
                    "00000000-0000-0000-0000-000000000000"
                )
            )


    def test_push_last_known_good_version(self):

        service = self.build_service()

        first = service.create_version(
            self.build_configuration(),
            name="Initial"
        )

        second = service.create_version(
            self.build_configuration("Updated"),
            name="Updated"
        )

        service.push_version(
            first.id
        )

        assert first.status == "ACTIVE"

        service.push_version(
            second.id
        )

        assert first.status == "AVAILABLE"
        assert second.status == "ACTIVE"


    def test_switch_does_not_delete_old_versions(self):

        service = self.build_service()

        first = service.create_version(
            self.build_configuration(),
            name="Initial"
        )

        second = service.create_version(
            self.build_configuration("Updated"),
            name="Updated"
        )

        service.switch_version(
            first.id
        )

        service.switch_version(
            second.id
        )

        versions = service.list_versions()

        assert len(versions) == 2


    def test_push_does_not_delete_old_versions(self):

        service = self.build_service()

        first = service.create_version(
            self.build_configuration(),
            name="Initial"
        )

        second = service.create_version(
            self.build_configuration("Updated"),
            name="Updated"
        )

        service.push_version(
            second.id
        )

        versions = service.list_versions()

        assert len(versions) == 2


    def test_export_version(self):

        service = self.build_service()

        version = service.create_version(
            self.build_configuration(),
            name="Initial"
        )

        result = service.export_version(
            version.id
        )

        assert result is not None


    def test_export_missing_version_fails(self):

        service = self.build_service()

        with pytest.raises(
            ValueError,
            match="Version not found"
        ):

            service.export_version(
                UUID(
                    "00000000-0000-0000-0000-000000000000"
                )
            )


class TestVersionImmutability:

    def setup_method(self):

        self.repository = VersionRepository()

        self.storage = JsonStorage(
            folder="storage/test_versions"
        )

        for path in self.storage.list():

            path.unlink()

        self.service = VersionService(
            repository=self.repository,
            storage=self.storage
        )


    def teardown_method(self):

        for path in self.storage.list():

            path.unlink()

        folder = Path(
            "storage/test_versions"
        )

        if folder.exists():

            try:
                folder.rmdir()

            except OSError:
                pass


    def test_creating_new_version_preserves_old_version(self):

        configuration = FirewallConfiguration()

        first = self.service.create_version(
            configuration,
            name="Version One"
        )

        second = self.service.create_version(
            configuration,
            name="Version Two"
        )

        assert first.id != second.id
        assert first.number == 1
        assert second.number == 2


    def test_versions_have_different_ids(self):

        first = self.service.create_version(
            FirewallConfiguration(),
            name="Version One"
        )

        second = self.service.create_version(
            FirewallConfiguration(),
            name="Version Two"
        )

        assert first.id != second.id


    def test_version_numbers_are_never_reused(self):

        first = self.service.create_version(
            FirewallConfiguration(),
            name="Version One"
        )

        second = self.service.create_version(
            FirewallConfiguration(),
            name="Version Two"
        )

        assert first.number == 1
        assert second.number == 2

        self.service.repository.clear()

        third = self.service.create_version(
            FirewallConfiguration(),
            name="Version Three"
        )

        assert third.number == 1


    def test_creating_version_does_not_change_previous_version_id(self):

        first = self.service.create_version(
            FirewallConfiguration(),
            name="Version One"
        )

        original_id = first.id

        self.service.create_version(
            FirewallConfiguration(),
            name="Version Two"
        )

        assert first.id == original_id


class TestVersionPersistence:

    def setup_method(self):

        self.repository = VersionRepository()

        self.storage = JsonStorage(
            folder="storage/test_versions"
        )

        for path in self.storage.list():

            path.unlink()

        self.service = VersionService(
            repository=self.repository,
            storage=self.storage
        )


    def teardown_method(self):

        for path in self.storage.list():

            path.unlink()

        folder = Path(
            "storage/test_versions"
        )

        if folder.exists():

            try:
                folder.rmdir()

            except OSError:
                pass


    def test_version_name_and_description_survive_reload(self):

        version = self.service.create_version(
            FirewallConfiguration(),
            name="Base Version",
            description="Initial configuration"
        )

        repository = VersionRepository()

        reloaded_service = VersionService(
            repository=repository,
            storage=self.storage
        )

        loaded = reloaded_service.get_version(
            version.id
        )

        assert loaded.name == "Base Version"

        assert (
            loaded.description
            == "Initial configuration"
        )


    def test_versions_survive_reload(self):

        first = self.service.create_version(
            FirewallConfiguration(),
            name="Version One"
        )

        second = self.service.create_version(
            FirewallConfiguration(),
            name="Version Two"
        )

        repository = VersionRepository()

        reloaded_service = VersionService(
            repository=repository,
            storage=self.storage
        )

        versions = (
            reloaded_service.list_versions()
        )

        assert len(versions) == 2

        assert versions[0].id == first.id
        assert versions[1].id == second.id


    def test_version_configuration_survives_reload(self):

        configuration = FirewallConfiguration()

        configuration.add_ruleset(
            RulesetConfig(
                name="Security"
            )
        )

        version = self.service.create_version(
            configuration,
            name="Base Version"
        )

        repository = VersionRepository()

        reloaded_service = VersionService(
            repository=repository,
            storage=self.storage
        )

        loaded = reloaded_service.get_version(
            version.id
        )

        assert len(
            loaded.configuration.rulesets
        ) == 1

        assert (
            loaded.configuration.rulesets[0].name
            == "Security"
        )


    def test_version_parent_survives_reload(self):

        first = self.service.create_version(
            FirewallConfiguration(),
            name="Base Version"
        )

        second = (
            self.service.create_version_from_version(
                first.id,
                name="Web Traffic Update"
            )
        )

        repository = VersionRepository()

        reloaded_service = VersionService(
            repository=repository,
            storage=self.storage
        )

        loaded_first = (
            reloaded_service.get_version(
                first.id
            )
        )

        loaded_second = (
            reloaded_service.get_version(
                second.id
            )
        )

        assert loaded_first.parent_version_id is None

        assert (
            loaded_second.parent_version_id
            == loaded_first.id
        )


    def test_version_parent_chain_survives_reload(self):

        first = self.service.create_version(
            FirewallConfiguration(),
            name="Base Version"
        )

        second = (
            self.service.create_version_from_version(
                first.id,
                name="Web Traffic Update"
            )
        )

        third = (
            self.service.create_version_from_version(
                second.id,
                name="Security Update"
            )
        )

        repository = VersionRepository()

        reloaded_service = VersionService(
            repository=repository,
            storage=self.storage
        )

        loaded_first = (
            reloaded_service.get_version(
                first.id
            )
        )

        loaded_second = (
            reloaded_service.get_version(
                second.id
            )
        )

        loaded_third = (
            reloaded_service.get_version(
                third.id
            )
        )

        assert (
            loaded_first.parent_version_id
            is None
        )

        assert (
            loaded_second.parent_version_id
            == loaded_first.id
        )

        assert (
            loaded_third.parent_version_id
            == loaded_second.id
        )


    def test_parent_version_id_is_saved_to_json(self):

        first = self.service.create_version(
            FirewallConfiguration(),
            name="Base Version"
        )

        second = (
            self.service.create_version_from_version(
                first.id,
                name="Web Traffic Update"
            )
        )

        data = self.storage.load(
            f"version_{second.number}"
        )

        assert (
            data["parent_version_id"]
            == str(first.id)
        )

