from .action import Action



class ContinueAction(Action):


    type = "CONTINUE"



    def execute(
        self,
        context
    ):

        return self