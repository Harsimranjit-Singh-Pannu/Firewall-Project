from .parameter import (
    Parameter,
    SCOPE_PRIORITY
)



class ParameterStore:


    def __init__(self):

        self.parameters = {}



    def set(

        self,

        parameter: Parameter

    ):


        existing = self.parameters.get(

            parameter.name

        )


        if existing:


            existing_priority = SCOPE_PRIORITY[

                existing.scope

            ]


            new_priority = SCOPE_PRIORITY[

                parameter.scope

            ]


            if existing_priority > new_priority:


                raise ValueError(

                    f"Cannot overwrite {existing.scope.value} parameter: {parameter.name}"

                )



        self.parameters[parameter.name] = parameter



    def get(

        self,

        name

    ):

        parameter = self.parameters.get(name)


        if parameter:

            return parameter.value


        return None



    def get_parameter(

        self,

        name

    ):

        return self.parameters.get(name)



    def exists(

        self,

        name

    ):

        return name in self.parameters



    def remove(

        self,

        name

    ):


        if name in self.parameters:

            del self.parameters[name]



    def all(

        self

    ):

        return self.parameters.values()