class ArgumentStore:


    def __init__(self):

        self.arguments = {}



    def set(

        self,

        name,

        value

    ):

        self.arguments[name] = value



    def get(

        self,

        name

    ):

        return self.arguments.get(

            name

        )



    def exists(

        self,

        name

    ):

        return name in self.arguments



    def all(

        self

    ):

        return self.arguments