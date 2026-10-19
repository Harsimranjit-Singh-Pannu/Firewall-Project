
import ipaddress
import re

from lists.list_column import ListColumn
from lists.list_definition import ListDefinition
from lists.list_repository import ListRepository


class ListManager:
    """
    Manages permanent lists and their row values.

    List schemas are immutable after creation.
    Cell values may be updated, rows may be added,
    and entire rows may be deleted.

    Lists are persisted in storage/lists.
    List versioning is not supported.
    """

    def __init__(self, repository=None):
        self.repository = (
            repository
            if repository is not None
            else ListRepository()
        )

        self._definitions = {}

        self._load_definitions()

        existing_numbers = [
            definition.list_number
            for definition in self._definitions.values()
        ]

        self._next_list_number = (
            max(existing_numbers, default=0) + 1
        )

    # ============================================================
    # Load Saved Definitions
    # ============================================================

    def _load_definitions(self):
        """
        Reconstruct immutable list definitions from saved JSON data.
        """

        for alias in self.repository._lists:
            entry = self.repository.get(alias)

            if entry is None:
                continue

            definition_data = entry["definition_data"]

            if not isinstance(definition_data, dict):
                raise ValueError(
                    f"Invalid definition for list: {alias}"
                )

            columns_data = definition_data.get("columns")

            if not isinstance(columns_data, list):
                raise ValueError(
                    f"Invalid columns for list: {alias}"
                )

            columns = [
                ListColumn(
                    name=column_data["name"],
                    datatype=column_data["datatype"],
                    unique=column_data.get("unique", False),
                    optional=column_data.get("optional", False),
                )
                for column_data in columns_data
            ]

            definition = ListDefinition(
                list_number=definition_data["list_number"],
                name=definition_data["name"],
                columns=columns,
                minimum_similarity=definition_data.get(
                    "minimum_similarity",
                    80,
                ),
)

            if definition.alias != alias:
                raise ValueError(
                    f"Stored list alias does not match "
                    f"its definition: {alias}"
                )

            self._definitions[alias] = definition

    # ============================================================
    # Create List
    # ============================================================

    def create_list(self, name, columns, rows=None, minimum_similarity=80):
        """
        Create a list with a permanent LMS identifier.

        Example:
            LMS_1_sender_rules
        """

        if rows is None:
            rows = []

        list_definition = ListDefinition(
            list_number=self._next_list_number,
            name=name,
            columns=columns,
            minimum_similarity=minimum_similarity,
        )

        alias = list_definition.alias

        if self.repository.exists(alias):
            raise ValueError(
                f"List already exists: {alias}"
            )

        self._validate_rows(
            list_definition,
            rows,
        )

        self.repository.save(
            list_definition,
            rows,
        )

        self._definitions[alias] = list_definition
        self._next_list_number += 1

        return list_definition

    # ============================================================
    # Get List
    # ============================================================

    def get_list(self, alias):
        """Return a list definition by its permanent alias."""

        definition = self._definitions.get(alias)

        if definition is None:
            raise ValueError(
                f"List not found: {alias}"
            )

        return definition

    # ============================================================
    # Get Rows
    # ============================================================

    def get_rows(self, alias):
        """Return independent copies of a list's rows."""

        rows = self.repository.get_rows(alias)

        if rows is None:
            raise ValueError(
                f"List not found: {alias}"
            )

        return rows

    # ============================================================
    # Update Cell
    # ============================================================

    def update_cell(
        self,
        alias,
        row_index,
        column_name,
        value,
    ):
        """
        Update one cell without changing the list schema.

        Validation happens before persistent storage is updated.
        """

        definition = self.get_list(alias)
        rows = self.get_rows(alias)

        self._validate_row_index(
            row_index,
            len(rows),
        )

        column = definition.get_column(column_name)

        if column is None:
            raise ValueError(
                f"Unknown column: {column_name}"
            )

        updated_rows = [
            dict(row)
            for row in rows
        ]

        updated_rows[row_index][column_name] = value

        self._validate_rows(
            definition,
            updated_rows,
        )

        self.repository.save(
            definition,
            updated_rows,
        )

    # ============================================================
    # Add Row
    # ============================================================

    def add_row(self, alias, row):
        """
        Add a row using the existing schema.

        Unknown columns, missing required values, invalid datatypes,
        and duplicate unique values are rejected.
        """

        definition = self.get_list(alias)
        rows = self.get_rows(alias)

        updated_rows = rows + [row]

        self._validate_rows(
            definition,
            updated_rows,
        )

        self.repository.save(
            definition,
            updated_rows,
        )

    # ============================================================
    # Delete Row
    # ============================================================

    def delete_row(self, alias, row_index):
        """Delete a row without changing the list schema."""

        definition = self.get_list(alias)
        rows = self.get_rows(alias)

        self._validate_row_index(
            row_index,
            len(rows),
        )

        updated_rows = [
            dict(row)
            for index, row in enumerate(rows)
            if index != row_index
        ]

        self._validate_rows(
            definition,
            updated_rows,
        )

        self.repository.save(
            definition,
            updated_rows,
        )

    # ============================================================
    # Validate Row Index
    # ============================================================

    @staticmethod
    def _validate_row_index(row_index, row_count):
        """Validate that a row index is an in-range integer."""

        if (
            not isinstance(row_index, int)
            or isinstance(row_index, bool)
        ):
            raise ValueError(
                "row_index must be an integer"
            )

        if row_index < 0 or row_index >= row_count:
            raise IndexError(
                "Row index out of range"
            )

    # ============================================================
    # Validate Rows
    # ============================================================

    def _validate_rows(
        self,
        list_definition,
        rows,
    ):
        """Validate rows against the permanent list schema."""

        if not isinstance(rows, list):
            raise ValueError(
                "rows must be a list"
            )

        column_names = {
            column.name
            for column in list_definition.columns
        }

        for row in rows:
            if not isinstance(row, dict):
                raise TypeError(
                    "Each row must be a dictionary"
                )

            unknown_columns = set(row.keys()) - column_names

            if unknown_columns:
                raise ValueError(
                    "Row contains unknown columns: "
                    + ", ".join(sorted(unknown_columns))
                )

            for column in list_definition.columns:
                if (
                    not column.optional
                    and column.name not in row
                ):
                    raise ValueError(
                        f"Missing required column: {column.name}"
                    )

                if column.name in row:
                    self._validate_cell_value(
                        column,
                        row[column.name],
                    )

        self._validate_unique_columns(
            list_definition,
            rows,
        )

    # ============================================================
    # Validate Cell Datatype
    # ============================================================

    @staticmethod
    def _validate_cell_value(column, value):
        """Validate a cell value against its column datatype."""

        datatype = column.datatype

        if datatype == "String":
            valid = isinstance(value, str)

        elif datatype == "Integer":
            valid = (
                isinstance(value, int)
                and not isinstance(value, bool)
            )

        elif datatype == "Boolean":
            valid = isinstance(value, bool)

        elif datatype == "Regex":
            valid = isinstance(value, str)

            if valid:
                try:
                    re.compile(value)
                except re.error:
                    valid = False

        elif datatype == "IPAddress":
            valid = isinstance(value, str)

            if valid:
                try:
                    ipaddress.ip_address(value)
                except ValueError:
                    valid = False

        else:
            valid = False

        if not valid:
            raise ValueError(
                f"Invalid value for column '{column.name}' "
                f"with datatype '{datatype}': {value!r}"
            )

    # ============================================================
    # Validate Unique Columns
    # ============================================================

    @staticmethod
    def _validate_unique_columns(
        list_definition,
        rows,
    ):
        """Reject duplicate values in columns marked unique."""

        for column in list_definition.columns:
            if not column.unique:
                continue

            seen = set()

            for row in rows:
                if column.name not in row:
                    continue

                value = row[column.name]

                if value in seen:
                    raise ValueError(
                        f"Duplicate value for unique "
                        f"column: {column.name}"
                    )

                seen.add(value)