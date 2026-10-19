from .enums import RightSourceType, SourceType



class ConditionResolver:


    def resolve_left(
        self,
        condition,
        context,
        arguments=None
    ):

        if condition.left_type == SourceType.PARAMETER:

            parameter = context.get_parameter(
                condition.left_name
            )


            if parameter is not None:

                return parameter.value



        if condition.left_type == SourceType.ARGUMENT:

            if arguments:

                return arguments.get(
                    condition.left_name
                )


        return None



    def resolve_right(
        self,
        condition,
        context,
        arguments=None
    ):


        if condition.right_type == RightSourceType.PARAMETER:

            parameter = context.get_parameter(
                condition.right_value
            )


            if parameter is not None:

                return parameter.value



        if condition.right_type == RightSourceType.ARGUMENT:

            if arguments:

                return arguments.get(
                    condition.right_value
                )


        return condition.right_value