from uuid import UUID


class VersionRepository:

    def __init__(
        self
    ):

        self.versions = []


    def save(
        self,
        version
    ):

        existing = self.get(
            version.id
        )

        if existing is not None:

            index = self.versions.index(
                existing
            )

            self.versions[index] = version

        else:

            self.versions.append(
                version
            )

        return version


    def list(
        self
    ):

        return list(
            self.versions
        )


    def get(
        self,
        version_id
    ):

        if isinstance(
            version_id,
            str
        ):

            try:

                version_id = UUID(
                    version_id
                )

            except ValueError:

                return None


        for version in self.versions:

            if version.id == version_id:

                return version


        return None


    def clear(
        self
    ):

        self.versions.clear()