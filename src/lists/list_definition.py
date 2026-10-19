
from lists.list_column import ListColumn


class ListDefinition:

    __slots__ = (
        "_list_number",
        "_name",
        "_columns",
        "_minimum_similarity",
        "_locked",
    )

    def __init__(
        self,
        list_number,
        name,
        columns,
        minimum_similarity=80,
    ):
        if (
            not isinstance(list_number, int)
            or isinstance(list_number, bool)
        ):
            raise ValueError(
                "list_number must be an integer"
            )

        if list_number < 1:
            raise ValueError(
                "list_number must be greater than zero"
            )

        if not isinstance(name, str) or not name.strip():
            raise ValueError(
                "List name must be a non-empty string"
            )

        if not isinstance(columns, list) or not columns:
            raise ValueError(
                "A list must have at least one column"
            )

        if not all(
            isinstance(column, ListColumn)
            for column in columns
        ):
            raise TypeError(
                "columns must contain ListColumn objects"
            )

        column_names = [
            column.name for column in columns
        ]

        if len(column_names) != len(set(column_names)):
            raise ValueError(
                "Column names must be unique"
            )

        if (
            isinstance(minimum_similarity, bool)
            or not isinstance(
                minimum_similarity,
                (int, float),
            )
            or not 0 <= minimum_similarity <= 100
        ):
            raise ValueError(
                "minimum_similarity must be a number "
                "between 0 and 100"
            )

        object.__setattr__(
            self, "_list_number", list_number
        )
        object.__setattr__(
            self, "_name", name
        )
        object.__setattr__(
            self, "_columns", tuple(columns)
        )
        object.__setattr__(
            self,
            "_minimum_similarity",
            float(minimum_similarity),
        )
        object.__setattr__(self, "_locked", True)

    def __setattr__(self, name, value):
        if getattr(self, "_locked", False):
            raise AttributeError(
                "ListDefinition identity and schema are immutable"
            )

        object.__setattr__(self, name, value)

    @property
    def list_number(self):
        return self._list_number

    @property
    def name(self):
        return self._name

    @property
    def columns(self):
        return self._columns

    @property
    def minimum_similarity(self):
        return self._minimum_similarity

    @property
    def alias(self):
        return f"LMS_{self.list_number}_{self.name}"

    def get_column(self, name):
        for column in self.columns:
            if column.name == name:
                return column

        return None

    def to_dict(self):
        return {
            "list_number": self.list_number,
            "name": self.name,
            "alias": self.alias,
            "columns": [
                column.to_dict()
                for column in self.columns
            ],
            "minimum_similarity": self.minimum_similarity,
        }