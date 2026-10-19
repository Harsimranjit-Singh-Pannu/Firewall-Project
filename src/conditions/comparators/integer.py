from conditions.enums import Operator

from .base import Comparator



class IntegerComparator(Comparator):


    def compare(

        self,

        left,

        right,

        operator

    ):


        left = int(left)

        right = int(right)


        if operator == Operator.EQUALS:

            return left == right


        if operator == Operator.NOT_EQUALS:

            return left != right


        if operator == Operator.GREATER_THAN:

            return left > right


        if operator == Operator.GREATER_THAN_EQUALS:

            return left >= right


        if operator == Operator.LESS_THAN:

            return left < right


        if operator == Operator.LESS_THAN_EQUALS:

            return left <= right


        raise ValueError(
            f"Unsupported operator {operator}"
        )