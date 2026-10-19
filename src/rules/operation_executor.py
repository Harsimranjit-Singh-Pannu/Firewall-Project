
from operations.parameter.set_parameter import (
    SetParameterOperation,
)

from operations.manipulation.arithmetic import (
    ArithmeticOperator,
    execute as arithmetic_execute,
)

from operations.manipulation.concatenate import (
    execute as concatenate_execute,
)

from operations.manipulation.convert_integer import (
    execute as convert_integer_execute,
)

from operations.manipulation.convert_string import (
    execute as convert_string_execute,
)

from operations.manipulation.regex_replace import (
    match as regex_match,
    replace as regex_replace,
)

from operations.decode.base64_decode import (
    execute as base64_decode_execute,
)

from operations.decode.hex_decode import (
    execute as hex_decode_execute,
)

from operations.encode.base64_encode import (
    execute as base64_encode_execute,
)

from operations.lookup.list_lookup import (
    execute as list_lookup_execute,
)

from operations.parameter.extract_metadata import (
    ExtractMetadataOperation,
)


class OperationExecutor:
    """Dispatch and execute firewall operations."""

    def __init__(self, list_manager=None):
        self.list_manager = list_manager

        self.operations = {
            "set-parameter": self._execute_set_parameter,
            "arithmetic": self._execute_arithmetic,
            "concatenate": self._execute_concatenate,
            "convert-integer": self._execute_convert_integer,
            "convert-string": self._execute_convert_string,
            "regex-match": self._execute_regex_match,
            "regex-replace": self._execute_regex_replace,
            "base64-decode": self._execute_base64_decode,
            "hex-decode": self._execute_hex_decode,
            "base64-encode": self._execute_base64_encode,
            "list-lookup": self._execute_list_lookup,
            "extract-message-metadata": self._execute_extract_metadata,
        }

    # ---------------------------------------------------------
    # Operation dispatch
    # ---------------------------------------------------------

    def execute(self, operation, context, arguments=None):
        if operation is None:
            return False

        operation_name = getattr(operation, "name", None)

        handler = self.operations.get(operation_name)

        if handler is None:
            raise ValueError(
                f"Unsupported operation: {operation_name}"
            )

        parameters = getattr(operation, "parameters", None)

        return handler(
            context,
            parameters,
            arguments=arguments,
        )

    # ---------------------------------------------------------
    # Extract Message Metadata
    # ---------------------------------------------------------

    def _execute_extract_metadata(
        self,
        context,
        parameters,
        arguments=None,
    ):
        if context is None:
            raise ValueError(
                "extract-message-metadata requires an execution context"
            )

        return ExtractMetadataOperation().execute(
            context,
            parameters,
        )

    # ---------------------------------------------------------
    # Set Parameter
    # ---------------------------------------------------------

    def _execute_set_parameter(
        self,
        context,
        parameters,
        arguments=None,
    ):
        if context is None:
            raise ValueError(
                "set-parameter requires an execution context"
            )

        return SetParameterOperation().execute(
            context,
            parameters,
            arguments=arguments,
        )

    # ---------------------------------------------------------
    # Arithmetic
    # ---------------------------------------------------------

    def _execute_arithmetic(
        self,
        context,
        parameters,
        arguments=None,
    ):
        self._require_parameters(
            parameters,
            ["operands", "operator", "result_parameter"],
            "arithmetic",
        )

        if context is None:
            raise ValueError(
                "arithmetic requires an execution context"
            )

        operands = parameters["operands"]
        operator = parameters["operator"]

        if not isinstance(operands, list) or len(operands) < 2:
            raise ValueError(
                "arithmetic requires at least two operands"
            )

        if isinstance(operator, str):
            try:
                operator = ArithmeticOperator(operator)
            except ValueError as exc:
                raise ValueError(
                    "Unsupported arithmetic operator: "
                    f"{parameters['operator']}"
                ) from exc

        elif not isinstance(operator, ArithmeticOperator):
            raise ValueError(
                f"Unsupported arithmetic operator: {operator}"
            )

        result = arithmetic_execute(operands, operator)

        if isinstance(result, float):
            if not result.is_integer():
                raise ValueError(
                    "Arithmetic result must be an integer"
                )

            result = int(result)

        context.set_parameter(
            name=parameters["result_parameter"],
            value=result,
            datatype="Integer",
            scope=parameters.get("scope", "Local"),
        )

        return result

    # ---------------------------------------------------------
    # Concatenate
    # ---------------------------------------------------------

    def _execute_concatenate(
        self,
        context,
        parameters,
        arguments=None,
    ):
        self._require_parameters(
            parameters,
            ["values"],
            "concatenate",
        )

        return concatenate_execute(
            parameters["values"],
            parameters.get("separator", ""),
        )

    # ---------------------------------------------------------
    # Convert Integer
    # ---------------------------------------------------------

    def _execute_convert_integer(
        self,
        context,
        parameters,
        arguments=None,
    ):
        self._require_parameters(
            parameters,
            ["value"],
            "convert-integer",
        )

        return convert_integer_execute(
            parameters["value"]
        )

    # ---------------------------------------------------------
    # Convert String
    # ---------------------------------------------------------

    def _execute_convert_string(
        self,
        context,
        parameters,
        arguments=None,
    ):
        self._require_parameters(
            parameters,
            ["value"],
            "convert-string",
        )

        return convert_string_execute(
            parameters["value"]
        )

    # ---------------------------------------------------------
    # Regex Match
    # ---------------------------------------------------------

    def _execute_regex_match(
        self,
        context,
        parameters,
        arguments=None,
    ):
        self._require_parameters(
            parameters,
            ["value", "pattern"],
            "regex-match",
        )

        return regex_match(
            parameters["value"],
            parameters["pattern"],
        )

    # ---------------------------------------------------------
    # Regex Replace
    # ---------------------------------------------------------

    def _execute_regex_replace(
        self,
        context,
        parameters,
        arguments=None,
    ):
        self._require_parameters(
            parameters,
            ["value", "pattern", "replacement"],
            "regex-replace",
        )

        return regex_replace(
            parameters["value"],
            parameters["pattern"],
            parameters["replacement"],
        )

    # ---------------------------------------------------------
    # Base64 Decode
    # ---------------------------------------------------------

    def _execute_base64_decode(
        self,
        context,
        parameters,
        arguments=None,
    ):
        self._require_parameters(
            parameters,
            ["value"],
            "base64-decode",
        )

        return base64_decode_execute(
            parameters["value"]
        )

    # ---------------------------------------------------------
    # Hex Decode
    # ---------------------------------------------------------

    def _execute_hex_decode(
        self,
        context,
        parameters,
        arguments=None,
    ):
        self._require_parameters(
            parameters,
            ["value"],
            "hex-decode",
        )

        return hex_decode_execute(
            parameters["value"]
        )

    # ---------------------------------------------------------
    # Base64 Encode
    # ---------------------------------------------------------

    def _execute_base64_encode(
        self,
        context,
        parameters,
        arguments=None,
    ):
        self._require_parameters(
            parameters,
            ["value"],
            "base64-encode",
        )

        return base64_encode_execute(
            parameters["value"]
        )

    # ---------------------------------------------------------
    # List Lookup
    # ---------------------------------------------------------

    def _execute_list_lookup(
        self,
        context,
        parameters,
        arguments=None,
    ):
        self._require_parameters(
            parameters,
            [
                "list_alias",
                "conditions",
                "result_parameter",
            ],
            "list-lookup",
        )

        if context is None:
            raise ValueError(
                "list-lookup requires an execution context"
            )

        # Prefer the manager explicitly supplied to this executor.
        # Otherwise, use the manager belonging to the context.
        list_manager = self.list_manager

        if list_manager is None:
            list_manager = getattr(
                context,
                "list_manager",
                None,
            )

        if list_manager is None:
            raise ValueError(
                "list-lookup requires a ListManager"
            )

        # The lookup implementation reads context.list_manager.
        context.list_manager = list_manager

        return list_lookup_execute(
            context,
            parameters,
        )

    # ---------------------------------------------------------
    # Parameter Validation
    # ---------------------------------------------------------

    @staticmethod
    def _require_parameters(
        parameters,
        required,
        operation_name,
    ):
        if not isinstance(parameters, dict):
            raise ValueError(
                f"{operation_name} parameters must be a dictionary"
            )

        missing = [
            name
            for name in required
            if name not in parameters
        ]

        if missing:
            raise ValueError(
                f"{operation_name} requires: "
                + ", ".join(missing)
            )