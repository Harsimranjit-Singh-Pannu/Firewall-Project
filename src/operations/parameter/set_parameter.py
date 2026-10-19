
from parameters import ParameterScope


class SetParameterOperation:
    """Create or update a parameter in the execution context."""

    name = "set-parameter"

    def execute(self, context, parameters, arguments=None):
        # Validate inputs.
        if not isinstance(parameters, dict):
            raise ValueError(
                "set-parameter parameters must be a dictionary"
            )

        if context is None:
            raise ValueError(
                "set-parameter requires an execution context"
            )

        if "name" not in parameters or not parameters["name"]:
            raise ValueError(
                "set-parameter requires 'name'"
            )

        has_value = "value" in parameters
        has_argument = "argument_name" in parameters

        # Exactly one value source must be provided.
        if not has_value and not has_argument:
            raise ValueError(
                "set-parameter requires 'value' or 'argument_name'"
            )

        if has_value and has_argument:
            raise ValueError(
                "set-parameter accepts either 'value' or "
                "'argument_name', but not both"
            )

        name = parameters["name"]

        # Resolve the value from runtime arguments or configuration.
        if has_argument:
            argument_name = parameters["argument_name"]

            if not isinstance(argument_name, str) or not argument_name:
                raise ValueError(
                    "set-parameter requires a valid 'argument_name'"
                )

            if not isinstance(arguments, dict):
                raise ValueError(
                    "set-parameter requires runtime arguments"
                )

            if argument_name not in arguments:
                raise ValueError(
                    f"Missing runtime argument: {argument_name}"
                )

            value = arguments[argument_name]
        else:
            value = parameters["value"]

        # Validate datatype.
        datatype = parameters.get("datatype", "String")

        if not isinstance(datatype, str) or not datatype:
            raise ValueError(
                "datatype must be a non-empty string"
            )

        if datatype == "String" and not isinstance(value, str):
            raise ValueError(
                f"Parameter {name} requires a String value"
            )

        # Resolve and validate parameter scope.
        scope = parameters.get("scope", ParameterScope.LOCAL)

        if isinstance(scope, str):
            try:
                scope = ParameterScope(scope)
            except ValueError as exc:
                raise ValueError(
                    f"Invalid parameter scope: {scope}"
                ) from exc

        if not isinstance(scope, ParameterScope):
            raise ValueError(
                "scope must be a ParameterScope or valid scope string"
            )

        # Store the parameter in the execution context.
        context.set_parameter(
            name=name,
            value=value,
            datatype=datatype,
            scope=scope,
        )

        return True