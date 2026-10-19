from enum import Enum


class ArithmeticOperator(Enum):

    ADD = "Add"

    SUBTRACT = "Subtract"

    MULTIPLY = "Multiply"

    DIVIDE = "Divide"


def execute(
    operands,
    operator
):

    if not isinstance(
        operands,
        list
    ):

        raise TypeError(
            "Operands must be a list"
        )

    if len(operands) < 2:

        raise ValueError(
            "At least two operands are required"
        )

    if isinstance(
        operator,
        str
    ):

        try:

            operator = ArithmeticOperator(
                operator
            )

        except ValueError:

            raise ValueError(
                f"Unsupported arithmetic operator: {operator}"
            )

    if operator == ArithmeticOperator.ADD:

        return sum(
            operands
        )

    if operator == ArithmeticOperator.SUBTRACT:

        result = operands[0]

        for operand in operands[1:]:

            result -= operand

        return result

    if operator == ArithmeticOperator.MULTIPLY:

        result = operands[0]

        for operand in operands[1:]:

            result *= operand

        return result

    if operator == ArithmeticOperator.DIVIDE:

        result = operands[0]

        for operand in operands[1:]:

            if operand == 0:

                raise ValueError(
                    "Division by zero"
                )

            result /= operand

        return result

    raise ValueError(
        f"Unsupported arithmetic operator: {operator}"
    )