from dataclasses import dataclass


@dataclass
class Condition:

    field: str

    operator: str

    value: object