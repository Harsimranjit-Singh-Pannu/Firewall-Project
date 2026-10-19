from enum import Enum


class SourceType(Enum):

    PARAMETER = "Parameter"

    ARGUMENT = "Argument"



class RightSourceType(Enum):

    PARAMETER = "Parameter"

    ARGUMENT = "Argument"

    USER_VALUE = "User_Value"



class MatchMode(Enum):

    ANY = "Any"

    ALL = "All"

    NONE = "None"



class Operator(Enum):

    EXISTS = "Exists"

    DOES_NOT_EXIST = "Does_Not_Exist"

    EQUALS = "Equals"

    NOT_EQUALS = "Not_Equals"

    CONTAINS = "Contains"

    NOT_CONTAINS = "Not_Contains"

    STARTS_WITH = "Starts_With"

    ENDS_WITH = "Ends_With"

    REGEX_MATCH = "Regex_Match"

    REGEX_NOT_MATCH = "Regex_Not_Match"

    GREATER_THAN = "Greater_Than"

    GREATER_THAN_EQUALS = "Greater_Than_Equals"

    LESS_THAN = "Less_Than"

    LESS_THAN_EQUALS = "Less_Than_Equals"