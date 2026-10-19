
class ListColumn:

    SUPPORTED_DATATYPES = frozenset({
        "String",
        "Integer",
        "Boolean",
        "Regex",
        "IPAddress",
    })

    __slots__ = (
        "_name",
        "_datatype",
        "_unique",
        "_optional",
        "_locked",
    )

    def __init__(
        self,
        name,
        datatype,
        unique=False,
        optional=False,
    ):
        if not isinstance(name, str) or not name.strip():
            raise ValueError(
                "Column name must be a non-empty string"
            )

        if datatype not in self.SUPPORTED_DATATYPES:
            raise ValueError(
                f"Unsupported column datatype: {datatype}"
            )

        object.__setattr__(self, "_name", name)
        object.__setattr__(self, "_datatype", datatype)
        object.__setattr__(self, "_unique", bool(unique))
        object.__setattr__(self, "_optional", bool(optional))
        object.__setattr__(self, "_locked", True)

    def __setattr__(self, name, value):
        if getattr(self, "_locked", False):
            raise AttributeError(
                "ListColumn metadata is immutable"
            )

        object.__setattr__(self, name, value)

    @property
    def name(self):
        return self._name

    @property
    def datatype(self):
        return self._datatype

    @property
    def unique(self):
        return self._unique

    @property
    def optional(self):
        return self._optional

    def to_dict(self):
        return {
            "name": self.name,
            "datatype": self.datatype,
            "unique": self.unique,
            "optional": self.optional,
        }