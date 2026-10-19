from dataclasses import dataclass
from enum import Enum



class ParameterScope(Enum):

    SYSTEM = "System"

    GLOBAL = "Global"

    LOCAL = "Local"



SCOPE_PRIORITY = {

    ParameterScope.LOCAL: 1,

    ParameterScope.GLOBAL: 2,

    ParameterScope.SYSTEM: 3

}



@dataclass
class Parameter:

    name: str

    value: object

    datatype: str

    scope: ParameterScope = ParameterScope.LOCAL