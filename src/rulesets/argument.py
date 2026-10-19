from dataclasses import dataclass
from enum import Enum



class DataType(Enum):

    STRING = "String"

    INTEGER = "Integer"

    BOOLEAN = "Boolean"

    IPV4 = "IPv4"

    IPV6 = "IPv6"



class CollectionType(Enum):

    SCALAR = "Scalar"

    SET = "Set"

    NODE = "Node"



@dataclass
class Argument:

    name: str

    datatype: DataType

    collection_type: CollectionType = CollectionType.SCALAR

    default_value: object = None