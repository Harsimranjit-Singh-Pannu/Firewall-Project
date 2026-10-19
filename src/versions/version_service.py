import copy

from uuid import UUID
from datetime import datetime, timezone

from versions.version import Version

from configuration.serializers.firewall_configuration_serializer import (
    FirewallConfigurationSerializer
)

from configuration.serializers.firewall_configuration_deserializer import (
    FirewallConfigurationDeserializer
)

from storage.json_storage import JsonStorage


class VersionService:

    def __init__(
        self,
        repository,
        serializer=None,
        deserializer=None,
        storage=None
    ):

        self.repository = repository

        self.serializer = (
            serializer
            or FirewallConfigurationSerializer()
        )

        self.deserializer = (
            deserializer
            or FirewallConfigurationDeserializer()
        )

        self.storage = (
            storage
            or JsonStorage()
        )

        self._load_versions()


    def _load_versions(
        self
    ):

        self.repository.clear()

        for file_path in self.storage.list():

            file_name = file_path.stem

            try:

                data = self.storage.load(
                    file_name
                )

            except ValueError:

                continue

            configuration_data = data.get(
                "configuration",
                {
                    "rulesets": []
                }
            )

            configuration = (
                self.deserializer.deserialize(
                    configuration_data
                )
            )

            version_id = data.get(
                "id"
            )

            if version_id:

                version_uuid = UUID(
                    version_id
                )

            else:

                version_uuid = None

            parent_version_id = data.get(
                "parent_version_id"
            )

            if parent_version_id:

                parent_uuid = UUID(
                    parent_version_id
                )

            else:

                parent_uuid = None

            created_at_value = data.get(
                "created_at"
            )

            if created_at_value:

                created_at = datetime.fromisoformat(
                    created_at_value
                )

            else:

                created_at = datetime.now(
                    timezone.utc
                )

            version = Version(

                number=data["version"],

                name=data.get(
                    "name",
                    f"Version {data['version']}"
                ),

                configuration=configuration,

                description=data.get(
                    "description"
                ),

                parent_version_id=parent_uuid,

                **(
                    {
                        "id": version_uuid
                    }
                    if version_uuid
                    else {}
                ),

                created_at=created_at,

                status=data.get(
                    "status",
                    "AVAILABLE"
                )
            )

            self.repository.save(
                version
            )


    def _next_version_number(
        self
    ):

        versions = self.repository.list()

        return (
            max(
                (
                    version.number
                    for version in versions
                ),
                default=0
            )
            + 1
        )


    def create_version(
        self,
        configuration,
        name,
        description=None,
        parent_version_id=None
    ):

        if not name:

            raise ValueError(
                "Version name is required"
            )

        version = Version(

            number=self._next_version_number(),

            name=name,

            description=description,

            parent_version_id=parent_version_id,

            configuration=copy.deepcopy(
                configuration
            )

        )

        self._save_version(
            version
        )

        return version


    def create_version_from_version(
        self,
        version_id,
        name,
        description=None
    ):

        source_version = self.repository.get(
            version_id
        )

        if source_version is None:

            raise ValueError(
                "Version not found"
            )

        return self.create_version(

            configuration=source_version.configuration,

            name=name,

            description=description,

            parent_version_id=source_version.id

        )


    def list_versions(
        self
    ):

        return sorted(
            self.repository.list(),
            key=lambda version: version.number
        )


    def get_version(
        self,
        version_id
    ):

        return self.repository.get(
            version_id
        )


    def get_working_version(
        self
    ):

        for version in self.repository.list():

            if version.status == "WORKING":

                return version

        return None


    
    def switch_version(self, version_id):
        version = self.repository.get(version_id)

        if version is None:
            raise ValueError("Version not found")

        versions = self.repository.list()

        original_statuses = {
            item.id: item.status
            for item in versions
        }

        try:
            for item in versions:
                if item.id == version.id:
                    item.status = "WORKING"
                elif item.status == "WORKING":
                    item.status = "AVAILABLE"

            for item in versions:
                self._save_version(item)

        except Exception:
            for item in versions:
                item.status = original_statuses[item.id]

            raise

        return version


    def push_version(
        self,
        version_id
    ):

        version = self.repository.get(
            version_id
        )

        if version is None:

            raise ValueError(
                "Version not found"
            )

        for item in self.repository.list():

            if item.id == version.id:

                item.status = "ACTIVE"

            elif item.status == "ACTIVE":

                item.status = "AVAILABLE"

            self._save_version(
                item
            )

        return version


    def export_version(
        self,
        version_id
    ):

        version = self.repository.get(
            version_id
        )

        if version is None:

            raise ValueError(
                "Version not found"
            )

        return self.serializer.export(
            version.configuration
        )


    def _save_version(
        self,
        version
    ):

        self.storage.save(

            f"version_{version.number}",

            {

                "id": str(
                    version.id
                ),

                "version": version.number,

                "name": version.name,

                "description": version.description,

                "parent_version_id": (
                    str(version.parent_version_id)
                    if version.parent_version_id
                    else None
                ),

                "created_at": (
                    version.created_at.isoformat()
                ),

                "status": version.status,

                "configuration": (
                    self.serializer.serialize(
                        version.configuration
                    )
                )

            }
        )

        self.repository.save(
            version
        )