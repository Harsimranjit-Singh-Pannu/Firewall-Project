import ipaddress

from conditions.enums import Operator

from .base import Comparator



class IPv4Comparator(Comparator):


    def compare(

        self,

        left,

        right,

        operator

    ):


        left = ipaddress.ip_address(left)

        right = ipaddress.ip_address(right)


        if operator == Operator.EQUALS:

            return left == right


        if operator == Operator.NOT_EQUALS:

            return left != right


        raise ValueError(
            f"Unsupported operator {operator}"
        )