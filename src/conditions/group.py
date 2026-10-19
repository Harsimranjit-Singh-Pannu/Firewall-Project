from enum import Enum



class GroupOperator(Enum):

    AND = "AND"

    OR = "OR"



class ConditionGroup:


    def __init__(

        self,

        operator,

        conditions

    ):


        if not conditions:

            raise ValueError(

                "ConditionGroup requires at least one condition"

            )


        self.operator = operator

        self.conditions = conditions