from abc import ABC, abstractmethod



class Action(ABC):


    type = None


    @abstractmethod
    def execute(
        self,
        context
    ):

        pass