from .group import GroupOperator



class ConditionGroupEvaluator:


    def __init__(

        self,

        condition_evaluator

    ):

        self.condition_evaluator = condition_evaluator



    def evaluate(

        self,

        group,

        context,

        arguments=None

    ):


        results = []


        for condition in group.conditions:


            result = self.condition_evaluator.evaluate(

                condition,

                context,

                arguments

            )


            results.append(result)



        if group.operator == GroupOperator.AND:

            return all(results)



        if group.operator == GroupOperator.OR:

            return any(results)



        return False