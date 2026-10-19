import pytest
from types import SimpleNamespace

from rules.operation_executor import OperationExecutor
from engine.context import ExecutionContext


def operation(name, parameters):
    return SimpleNamespace(
        name=name,
        parameters=parameters
    )


class TestOperationExecutor:

    def setup_method(self):
        self.executor = OperationExecutor()

    # ============================================================
    # General
    # ============================================================

    def test_none_operation_returns_false(self):
        context = ExecutionContext()

        result = self.executor.execute(
            None,
            context
        )

        assert result is False

    def test_unsupported_operation_raises_error(self):
        context = ExecutionContext()

        op = operation(
            "unknown-operation",
            {}
        )

        with pytest.raises(
            ValueError,
            match="Unsupported operation"
        ):
            self.executor.execute(
                op,
                context
            )

    # ============================================================
    # Set Parameter
    # ============================================================

    def test_set_parameter(self):
        context = ExecutionContext()

        op = operation(
            "set-parameter",
            {
                "name": "username",
                "value": "Simran",
                "datatype": "String"
            }
        )

        self.executor.execute(
            op,
            context
        )

        parameter = context.get_parameter(
            "username"
        )

        assert parameter is not None
        assert parameter.value == "Simran"
        assert parameter.datatype == "String"

    def test_set_parameter_requires_context(self):
        op = operation(
            "set-parameter",
            {
                "name": "x",
                "value": 10,
                "datatype": "Integer"
            }
        )

        with pytest.raises(
            ValueError,
            match="execution context"
        ):
            self.executor.execute(
                op,
                None
            )

    # ============================================================
    # Arithmetic
    # ============================================================

    def test_arithmetic_add(self):
        context = ExecutionContext()

        op = operation(
            "arithmetic",
            {
                "operands": [10, 20],
                "operator": "Add",
                "result_parameter": "total"
            }
        )

        result = self.executor.execute(
            op,
            context
        )

        assert result == 30

        parameter = context.get_parameter(
            "total"
        )

        assert parameter.value == 30
        assert parameter.datatype == "Integer"

    def test_arithmetic_add_multiple_operands(self):
        context = ExecutionContext()

        op = operation(
            "arithmetic",
            {
                "operands": [10, 20, 30],
                "operator": "Add",
                "result_parameter": "total"
            }
        )

        result = self.executor.execute(
            op,
            context
        )

        assert result == 60

    def test_arithmetic_subtract(self):
        context = ExecutionContext()

        op = operation(
            "arithmetic",
            {
                "operands": [100, 20, 10],
                "operator": "Subtract",
                "result_parameter": "result"
            }
        )

        result = self.executor.execute(
            op,
            context
        )

        assert result == 70

    def test_arithmetic_multiply(self):
        context = ExecutionContext()

        op = operation(
            "arithmetic",
            {
                "operands": [2, 3, 4],
                "operator": "Multiply",
                "result_parameter": "result"
            }
        )

        result = self.executor.execute(
            op,
            context
        )

        assert result == 24

    def test_arithmetic_divide(self):
        context = ExecutionContext()

        op = operation(
            "arithmetic",
            {
                "operands": [100, 2, 5],
                "operator": "Divide",
                "result_parameter": "result"
            }
        )

        result = self.executor.execute(
            op,
            context
        )

        assert result == 10

    def test_arithmetic_saves_result(self):
        context = ExecutionContext()

        op = operation(
            "arithmetic",
            {
                "operands": [10, 20],
                "operator": "Add",
                "result_parameter": "total"
            }
        )

        self.executor.execute(
            op,
            context
        )

        parameter = context.get_parameter(
            "total"
        )

        assert parameter is not None
        assert parameter.value == 30
        assert parameter.datatype == "Integer"

    def test_arithmetic_result_can_be_used_later(self):
        context = ExecutionContext()

        first = operation(
            "arithmetic",
            {
                "operands": [10, 20],
                "operator": "Add",
                "result_parameter": "total"
            }
        )

        self.executor.execute(
            first,
            context
        )

        total = context.get_parameter(
            "total"
        )

        second = operation(
            "arithmetic",
            {
                "operands": [
                    total.value,
                    10
                ],
                "operator": "Multiply",
                "result_parameter": "final"
            }
        )

        result = self.executor.execute(
            second,
            context
        )

        assert result == 300

        final = context.get_parameter(
            "final"
        )

        assert final.value == 300

    def test_arithmetic_parameter_value_can_be_used_as_operand(self):
        context = ExecutionContext()

        context.set_parameter(
            name="amount",
            value=50,
            datatype="Integer"
        )

        amount = context.get_parameter(
            "amount"
        )

        op = operation(
            "arithmetic",
            {
                "operands": [
                    amount.value,
                    25
                ],
                "operator": "Add",
                "result_parameter": "total"
            }
        )

        result = self.executor.execute(
            op,
            context
        )

        assert result == 75

    def test_arithmetic_rejects_parameter_object(self):
        context = ExecutionContext()

        context.set_parameter(
            name="amount",
            value=50,
            datatype="Integer"
        )

        amount = context.get_parameter(
            "amount"
        )

        op = operation(
            "arithmetic",
            {
                "operands": [
                    amount,
                    25
                ],
                "operator": "Add",
                "result_parameter": "total"
            }
        )

        with pytest.raises(
            TypeError
        ):
            self.executor.execute(
                op,
                context
            )

    def test_arithmetic_division_by_zero(self):
        context = ExecutionContext()

        op = operation(
            "arithmetic",
            {
                "operands": [100, 0],
                "operator": "Divide",
                "result_parameter": "result"
            }
        )

        with pytest.raises(
            ValueError,
            match="Division by zero"
        ):
            self.executor.execute(
                op,
                context
            )

    def test_arithmetic_requires_two_operands(self):
        context = ExecutionContext()

        op = operation(
            "arithmetic",
            {
                "operands": [10],
                "operator": "Add",
                "result_parameter": "result"
            }
        )

        with pytest.raises(
            ValueError,
            match="at least two operands"
        ):
            self.executor.execute(
                op,
                context
            )

    def test_arithmetic_requires_list(self):
        context = ExecutionContext()

        op = operation(
            "arithmetic",
            {
                "operands": 10,
                "operator": "Add",
                "result_parameter": "result"
            }
        )

        with pytest.raises(
            ValueError,
            match="arithmetic requires at least two operands"
        ):
            self.executor.execute(
                op,
                context
            )

    def test_arithmetic_invalid_operator(self):
        context = ExecutionContext()

        op = operation(
            "arithmetic",
            {
                "operands": [10, 20],
                "operator": "Invalid",
                "result_parameter": "result"
            }
        )

        with pytest.raises(
            ValueError,
            match="Unsupported arithmetic operator"
        ):
            self.executor.execute(
                op,
                context
            )

    def test_arithmetic_requires_context(self):
        op = operation(
            "arithmetic",
            {
                "operands": [10, 20],
                "operator": "Add",
                "result_parameter": "result"
            }
        )

        with pytest.raises(
            ValueError,
            match="execution context"
        ):
            self.executor.execute(
                op,
                None
            )

    # ============================================================
    # Concatenate
    # ============================================================

    def test_concatenate(self):
        context = ExecutionContext()

        op = operation(
            "concatenate",
            {
                "values": [
                    "hello",
                    "world"
                ],
                "separator": " "
            }
        )

        result = self.executor.execute(
            op,
            context
        )

        assert result["result"] == "hello world"

    # ============================================================
    # Convert Integer
    # ============================================================

    def test_convert_integer(self):
        context = ExecutionContext()

        op = operation(
            "convert-integer",
            {
                "value": "123"
            }
        )

        result = self.executor.execute(
            op,
            context
        )

        assert result["result"] == 123

    # ============================================================
    # Convert String
    # ============================================================

    def test_convert_string(self):
        context = ExecutionContext()

        op = operation(
            "convert-string",
            {
                "value": 123
            }
        )

        result = self.executor.execute(
            op,
            context
        )

        assert result["result"] == "123"

    # ============================================================
    # Regex Match
    # ============================================================

    def test_regex_match(self):
        context = ExecutionContext()

        op = operation(
            "regex-match",
            {
                "value": "hello123",
                "pattern": r"\d+"
            }
        )

        result = self.executor.execute(
            op,
            context
        )

        assert result is not None

    # ============================================================
    # Regex Replace
    # ============================================================

    def test_regex_replace(self):
        context = ExecutionContext()

        op = operation(
            "regex-replace",
            {
                "value": "hello123",
                "pattern": r"\d+",
                "replacement": "456"
            }
        )

        result = self.executor.execute(
            op,
            context
        )

        assert result["result"] == "hello456"

    # ============================================================
    # Base64 Decode
    # ============================================================

    def test_base64_decode(self):
        context = ExecutionContext()

        op = operation(
            "base64-decode",
            {
                "value": "aGVsbG8="
            }
        )

        result = self.executor.execute(
            op,
            context
        )

        assert result["result"] == "hello"

    # ============================================================
    # Hex Decode
    # ============================================================

    def test_hex_decode(self):
        context = ExecutionContext()

        op = operation(
            "hex-decode",
            {
                "value": "68656c6c6f"
            }
        )

        result = self.executor.execute(
            op,
            context
        )

        assert result["result"] == "hello"

    # ============================================================
    # Base64 Encode
    # ============================================================

    def test_base64_encode(self):
        context = ExecutionContext()

        op = operation(
            "base64-encode",
            {
                "value": "hello"
            }
        )

        result = self.executor.execute(
            op,
            context
        )

        assert result["result"] == "aGVsbG8="