from parameters import ParameterScope


class SetParameterOperation:

    name = "set-parameter"

    def execute(
        self,
        context,
        parameters
    ):

        if not isinstance(
            parameters,
            dict
        ):

            raise ValueError(
                "set-parameter parameters must be a dictionary"
            )

        if "name" not in parameters:

            raise ValueError(
                "set-parameter requires 'name'"
            )

        if "value" not in parameters:

            raise ValueError(
                "set-parameter requires 'value'"
            )

        name = parameters["name"]

        value = parameters["value"]

        datatype = parameters.get(
            "datatype",
            "String"
        )

        scope = parameters.get(
            "scope",
            ParameterScope.LOCAL
        )

        if isinstance(
            scope,
            str
        ):

            try:

                scope = ParameterScope(
                    scope
                )

            except ValueError:

                raise ValueError(
                    f"Invalid parameter scope: {scope}"
                )

        if not isinstance(
            scope,
            ParameterScope
        ):

            raise ValueError(
                "scope must be a ParameterScope or valid scope string"
            )

        context.set_parameter(

            name=name,

            value=value,

            datatype=datatype,

            scope=scope

        )

        return True