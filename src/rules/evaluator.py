from .rule import Rule
from conditions import ConditionGroupEvaluator
from .operation_executor import OperationExecutor



class RuleEvaluator:


    def __init__(

        self,

        condition_group_evaluator: ConditionGroupEvaluator,

        operation_executor: OperationExecutor

    ):

        self.condition_group_evaluator = condition_group_evaluator

        self.operation_executor = operation_executor



    def evaluate(

        self,

        rule: Rule,

        context,

        arguments=None

    ):


        rule.validate()


        matched = self.condition_group_evaluator.evaluate(

            rule.condition_group,

            context,

            arguments

        )


        if not matched:

            return None



        for operation in rule.operations:


            self.operation_executor.execute(

                operation,

                context,
                arguments=arguments

            )



        return rule.action.execute(
            context
        )