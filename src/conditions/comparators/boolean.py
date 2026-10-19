from conditions.enums import Operator

from .base import Comparator



class BooleanComparator(Comparator):


    def to_bool(

        self,

        value

    ):


        if isinstance(

            value,

            bool

        ):

            return value


        return str(value).lower() in (

            "true",

            "1",

            "yes"

        )



    def compare(

        self,

        left,

        right,

        operator

    ):


        left = self.to_bool(left)

        right = self.to_bool(right)


        if operator == Operator.EQUALS:

            return left == right


        if operator == Operator.NOT_EQUALS:

            return left != right


        raise ValueError(
            f"Unsupported operator {operator}"
        )