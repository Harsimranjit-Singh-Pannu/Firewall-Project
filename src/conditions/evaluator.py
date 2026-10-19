from .resolver import ConditionResolver

from .comparators import ComparatorFactory

from .enums import (
    SourceType,
    Operator
)



class ConditionEvaluator:


    def __init__(

        self

    ):

        self.resolver = ConditionResolver()



    def evaluate(

        self,

        condition,

        context,

        arguments=None

    ):


        left = self.resolver.resolve_left(

            condition,

            context,

            arguments

        )


        right = self.resolver.resolve_right(

            condition,

            context,

            arguments

        )


        #
        # Exists / Does Not Exist
        #

        if condition.operator == Operator.EXISTS:

            return left is not None



        if condition.operator == Operator.DOES_NOT_EXIST:

            return left is None



        if left is None:

            return False



        #
        # Handle scalar and collections
        #

        values = (

            left

            if isinstance(left, list)

            else [left]

        )



        #
        # Determine datatype
        #

        datatype = "String"



        if condition.left_type == SourceType.PARAMETER:


            parameter = context.get_parameter(

                condition.left_name

            )


            if parameter is not None:

                datatype = parameter.datatype



        elif condition.left_type == SourceType.ARGUMENT:


            if arguments is not None:


                value = arguments.get(

                    condition.left_name

                )


                if isinstance(value, bool):

                    datatype = "Boolean"


                elif isinstance(value, int):

                    datatype = "Integer"


                elif isinstance(value, str):

                    datatype = "String"



        #
        # Comparator
        #

        comparator = ComparatorFactory.get(

            datatype

        )



        results = []


        for value in values:


            results.append(

                comparator.compare(

                    value,

                    right,

                    condition.operator

                )

            )



        #
        # Match mode
        #

        if condition.match_mode.value == "Any":

            return any(results)



        if condition.match_mode.value == "All":

            return all(results)



        if condition.match_mode.value == "None":

            return not any(results)



        return False