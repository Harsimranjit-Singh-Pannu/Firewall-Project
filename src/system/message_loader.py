from parameters import (
    Parameter,
    ParameterScope
)



class MessageParameterLoader:



    def load(

        self,

        context,

        message

    ):


        for name, value in message.items():


            datatype = self.detect_type(value)


            parameter = Parameter(

                name=name,

                value=value,

                datatype=datatype,

                scope=ParameterScope.SYSTEM

            )


            context.parameters.set(

                parameter

            )



    def detect_type(

        self,

        value

    ):


        if isinstance(value, int):

            return "Integer"


        if isinstance(value, list):

            return "Set"


        return "String"