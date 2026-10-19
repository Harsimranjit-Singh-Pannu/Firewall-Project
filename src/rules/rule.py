from .operation_definition import Operation
from actions import Action



class Rule:


    def __init__(

        self,

        name,

        description=None

    ):

        self.name = name

        self.description = description

        self.condition_group = None

        self.operations = []

        self.action = None



    def set_condition_group(

        self,

        condition_group

    ):

        self.condition_group = condition_group



    def add_operation(

        self,

        operation: Operation

    ):

        self.operations.append(operation)



    def set_action(

        self,

        action: Action

    ):

        self.action = action



    def validate(self):

        if self.condition_group is None:

            raise ValueError(

                "Rule requires condition group"

            )


        if self.action is None:

            raise ValueError(

                "Rule requires action"

            )


        return True