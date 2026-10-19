from .argument import Argument



class Ruleset:


    def __init__(
        self,
        name,
        description=None
    ):

        self.name = name

        self.description = description

        self.arguments = []

        self.rules = []



    def add_argument(
        self,
        argument: Argument
    ):

        if self.get_argument(argument.name):

            raise ValueError(
                f"Argument already exists: {argument.name}"
            )


        self.arguments.append(argument)



    def add_rule(
        self,
        rule
    ):

        self.rules.append(rule)



    def get_argument(
        self,
        name
    ):

        for argument in self.arguments:

            if argument.name == name:

                return argument


        return None



    def get_rule(
        self,
        name
    ):

        for rule in self.rules:

            if rule.name == name:

                return rule


        return None



    def validate_arguments(
        self,
        arguments=None
    ):

        arguments = arguments or {}


        #
        # Ruleset accepts no arguments
        #

        if not self.arguments:


            if arguments:

                raise ValueError(

                    f"Ruleset {self.name} does not accept arguments"

                )


            return {}



        #
        # Check unknown arguments first
        #

        for name in arguments:


            if self.get_argument(name) is None:

                raise ValueError(

                    f"Unknown argument: {name}"

                )



        #
        # Resolve arguments and defaults
        #

        resolved = {}


        for argument in self.arguments:


            if argument.name in arguments:

                resolved[

                    argument.name

                ] = arguments[argument.name]


            elif argument.default_value is not None:

                resolved[

                    argument.name

                ] = argument.default_value


            else:

                raise ValueError(

                    f"Missing argument: {argument.name}"

                )



        #
        # Validate resolved arguments
        #

        self.validate_argument_types(

            resolved

        )


        return resolved



    def validate_argument_types(
        self,
        arguments
    ):

        if not arguments:

            return True



        for name, value in arguments.items():


            argument = self.get_argument(

                name

            )


            if argument is None:

                raise ValueError(

                    f"Unknown argument: {name}"

                )



            datatype = argument.datatype.value

            collection_type = argument.collection_type.value



            if collection_type in (

                "Set",

                "Node"

            ):


                if not isinstance(

                    value,

                    (list, set, tuple)

                ):

                    raise ValueError(

                        f"Argument {name} expects collection value"

                    )


                values = value



            else:

                values = [

                    value

                ]



            for item in values:


                if datatype == "String":

                    valid = isinstance(

                        item,

                        str

                    )


                elif datatype == "Integer":

                    valid = isinstance(

                        item,

                        int

                    ) and not isinstance(

                        item,

                        bool

                    )


                elif datatype == "Boolean":

                    valid = isinstance(

                        item,

                        bool

                    )


                elif datatype in (

                    "IPv4",

                    "IPv6"

                ):

                    valid = isinstance(

                        item,

                        str

                    )


                else:

                    valid = True



                if not valid:

                    raise ValueError(

                        f"Argument {name} expects {datatype}"

                    )


        return True



    def validate(self):

        if not self.rules:

            raise ValueError(

                "Ruleset requires at least one rule"

            )


        return True