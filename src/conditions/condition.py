from dataclasses import dataclass

from .enums import (
    SourceType,
    RightSourceType,
    MatchMode,
    Operator
)



@dataclass
class Condition:


    left_type: SourceType

    left_name: str


    operator: Operator


    match_mode: MatchMode = MatchMode.ANY


    right_type: RightSourceType = None

    right_value: object = None