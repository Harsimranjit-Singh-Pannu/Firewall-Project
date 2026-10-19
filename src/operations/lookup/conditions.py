from dataclasses import dataclass



class MatchType:

    REGEX = "Regex"

    STRING = "String"

    STRING_SIMILARITY = "String_Similarity"



@dataclass
class MatchCondition:

    column: str

    match_type: str

    value: str