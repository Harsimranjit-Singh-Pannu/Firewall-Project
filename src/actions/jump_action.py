from .action import Action



class JumpToRuleset(Action):


    type = "JUMP"



    def __init__(
        self,
        ruleset_name,
        argument_bindings=None
    ):

        self.ruleset_name = ruleset_name

        self.argument_bindings = argument_bindings or []



    def execute(
        self,
        context
    ):

        return self