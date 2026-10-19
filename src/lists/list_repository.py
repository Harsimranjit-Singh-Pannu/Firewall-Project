
from storage.json_storage import JsonStorage


class ListRepository:
    STORAGE_NAME = "lists"

    def __init__(self, storage=None):
        self.storage = (
            storage
            if storage is not None
            else JsonStorage(folder="storage/lists")
        )

        self._lists = {}
        self._load()

    def _load(self):
        try:
            data = self.storage.load(self.STORAGE_NAME)
        except ValueError:
            return

        if not isinstance(data, dict):
            raise ValueError(
                "Stored lists data must be a dictionary"
            )

        for alias, entry in data.items():
            if not isinstance(entry, dict):
                raise ValueError(
                    f"Invalid stored entry for list: {alias}"
                )

            definition_data = entry.get("definition")
            rows = entry.get("rows")

            if not isinstance(definition_data, dict):
                raise ValueError(
                    f"Invalid definition for list: {alias}"
                )

            if not isinstance(rows, list):
                raise ValueError(
                    f"Invalid rows for list: {alias}"
                )

            if not all(isinstance(row, dict) for row in rows):
                raise ValueError(
                    f"Invalid row data for list: {alias}"
                )

            self._lists[alias] = {
                "definition_data": definition_data,
                "rows": [dict(row) for row in rows],
            }

    def _persist(self):
        data = {
            alias: {
                "definition": entry["definition_data"],
                "rows": [
                    dict(row)
                    for row in entry["rows"]
                ],
            }
            for alias, entry in self._lists.items()
        }

        self.storage.save(
            self.STORAGE_NAME,
            data,
        )

    def save(self, list_definition, rows):
        alias = list_definition.alias

        self._lists[alias] = {
            "definition_data": list_definition.to_dict(),
            "rows": [
                dict(row)
                for row in rows
            ],
        }

        self._persist()

    def get(self, alias):
        entry = self._lists.get(alias)

        if entry is None:
            return None

        return {
            "definition_data": dict(
                entry["definition_data"]
            ),
            "rows": [
                dict(row)
                for row in entry["rows"]
            ],
        }

    def exists(self, alias):
        return alias in self._lists

    def get_rows(self, alias):
        entry = self._lists.get(alias)

        if entry is None:
            return None

        return [
            dict(row)
            for row in entry["rows"]
        ]

    def get_list_numbers(self):
        """Return the numeric identifiers of all stored lists."""
        numbers = []

        for alias, entry in self._lists.items():
            definition = entry["definition_data"]
            number = definition.get("list_number")

            if (
                isinstance(number, int)
                and not isinstance(number, bool)
            ):
                numbers.append(number)

        return numbers