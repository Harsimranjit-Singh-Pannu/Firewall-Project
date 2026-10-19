import re

from conditions.enums import Operator

from .base import Comparator



class StringComparator(Comparator):


    def compare(

        self,

        left,

        right,

        operator

    ):


        left = str(left)

        right = str(right)


        if operator == Operator.EQUALS:

            return left == right


        if operator == Operator.NOT_EQUALS:

            return left != right


        if operator == Operator.CONTAINS:

            return right in left


        if operator == Operator.NOT_CONTAINS:

            return right not in left


        if operator == Operator.STARTS_WITH:

            return left.startswith(right)


        if operator == Operator.ENDS_WITH:

            return left.endswith(right)


        if operator == Operator.REGEX_MATCH:

            return re.search(right, left) is not None


        if operator == Operator.REGEX_NOT_MATCH:

            return re.search(right, left) is None


        raise ValueError(

            f"Unsupported operator {operator}"

        )