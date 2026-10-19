from .string import StringComparator
from .integer import IntegerComparator
from .boolean import BooleanComparator
from .ipv4 import IPv4Comparator


class ComparatorFactory:

    @staticmethod
    def get(
        datatype
    ):

        if hasattr(
            datatype,
            "value"
        ):

            datatype = datatype.value

        datatype = str(
            datatype
        ).lower()

        if datatype == "integer":

            return IntegerComparator()

        if datatype == "boolean":

            return BooleanComparator()

        if datatype == "ipv4":

            return IPv4Comparator()

        return StringComparator()