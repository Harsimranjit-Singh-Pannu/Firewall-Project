import re
from difflib import SequenceMatcher

from parameters.parameter import ParameterScope

def execute(context, parameters):
    if context is None:
        raise ValueError(
            "list-lookup requires an execution context"
        )

    if not isinstance(parameters, dict):
        raise ValueError(
            "list-lookup parameters must be a dictionary"
        )

    required = (
        "list_alias",
        "conditions",
        "result_parameter",
    )

    missing = [
        key for key in required
        if key not in parameters
    ]

    if missing:
        raise ValueError(
            "list-lookup requires: "
            + ", ".join(missing)
        )

    alias = parameters["list_alias"]
    conditions = parameters["conditions"]
    result_parameter = parameters["result_parameter"]

    # Return one row by default. Larger values return
    # multiple matching rows.
    max_rows = parameters.get("max_rows", 1)

    if not isinstance(alias, str) or not alias:
        raise ValueError(
            "list_alias must be a non-empty string"
        )

    if (
        not isinstance(result_parameter, str)
        or not result_parameter
    ):
        raise ValueError(
            "result_parameter must be a non-empty string"
        )

    if not isinstance(conditions, list) or not conditions:
        raise ValueError(
            "conditions must be a non-empty list"
        )

    if (
        not isinstance(max_rows, int)
        or isinstance(max_rows, bool)
        or max_rows < 1
    ):
        raise ValueError(
            "max_rows must be a positive integer"
        )

    definition = context.list_manager.get_list(alias)
    rows = context.list_manager.get_rows(alias)

    minimum_similarity = definition.minimum_similarity

    supported_operators = {
        "Equals",
        "Not_Equals",
        "Contains",
        "Not_Contains",
        "Starts_With",
        "Ends_With",
        "Regex_Match",
        "Regex_Not_Match",
        "String_Similarity",
    }

    column_names = {
        column.name for column in definition.columns
    }

    # Validate every condition before examining rows.
    for condition in conditions:
        if not isinstance(condition, dict):
            raise ValueError(
                "Each list condition must be a dictionary"
            )

        column = condition.get("column")
        operator = condition.get("operator")

        if column not in column_names:
            raise ValueError(
                f"Unknown list column: {column}"
            )

        if operator not in supported_operators:
            raise ValueError(
                f"Unsupported list operator: {operator}"
            )

        if "value" not in condition:
            raise ValueError(
                "Each condition requires a value"
            )

        if operator in (
            "Regex_Match",
            "Regex_Not_Match",
        ):
            expected = condition["value"]

            if isinstance(expected, dict):
                continue

            if not isinstance(expected, str):
                raise ValueError(
                    "Regex condition values must be strings"
                )

            try:
                re.compile(expected)
            except re.error as exc:
                raise ValueError(
                    f"Invalid regex pattern: {expected}"
                ) from exc

    def resolve_expected(condition):
        value = condition["value"]

        if isinstance(value, dict):
            if value.get("type") == "Parameter":
                parameter_name = value.get("name")

                if (
                    not isinstance(parameter_name, str)
                    or not parameter_name
                ):
                    raise ValueError(
                        "Parameter references require a name"
                    )

                parameter = context.get_parameter(
                    parameter_name
                )

                if parameter is None:
                    raise ValueError(
                        f"Parameter not found: {parameter_name}"
                    )

                return parameter.value

        return value

    resolved_conditions = [
        (
            condition["column"],
            condition["operator"],
            resolve_expected(condition),
        )
        for condition in conditions
    ]

    def matches(actual, expected, operator):
        if actual is None:
            return False

        if operator == "Equals":
            return actual == expected

        if operator == "Not_Equals":
            return actual != expected

        if operator == "Contains":
            return (
                isinstance(actual, str)
                and isinstance(expected, str)
                and expected in actual
            )

        if operator == "Not_Contains":
            return (
                isinstance(actual, str)
                and isinstance(expected, str)
                and expected not in actual
            )

        if operator == "Starts_With":
            return (
                isinstance(actual, str)
                and isinstance(expected, str)
                and actual.startswith(expected)
            )

        if operator == "Ends_With":
            return (
                isinstance(actual, str)
                and isinstance(expected, str)
                and actual.endswith(expected)
            )

        if operator in (
            "Regex_Match",
            "Regex_Not_Match",
        ):
            if (
                not isinstance(actual, str)
                or not isinstance(expected, str)
            ):
                return False

            matched = re.search(
                expected,
                actual,
            ) is not None

            return (
                matched
                if operator == "Regex_Match"
                else not matched
            )

        if operator == "String_Similarity":
            if (
                not isinstance(actual, str)
                or not isinstance(expected, str)
            ):
                return False

            similarity = SequenceMatcher(
                None,
                actual,
                expected,
                autojunk=False,
            ).ratio()*100

            return similarity >= minimum_similarity

        return False

    matched_rows = []

    # Every condition is evaluated against the same row.
    # Values from different rows are never combined.
    for row in rows:
        row_matches = all(
            matches(
                row.get(column),
                expected,
                operator,
            )
            for column, operator, expected
            in resolved_conditions
        )

        if not row_matches:
            continue

        matched_rows.append(dict(row))

        if len(matched_rows) >= max_rows:
            break

    # No match means no parameter update.
    if not matched_rows:
        return {
            "success": True,
            "match": False,
            "rows": [],
            "count": 0,
        }

    # One row is a dictionary; multiple rows are a list
    # of dictionaries.
    if len(matched_rows) == 1:
        result_value = matched_rows[0]
        datatype = "Row"
    else:
        result_value = matched_rows
        datatype = "List"

    context.set_parameter(
        name=result_parameter,
        value=result_value,
        datatype=datatype,
        scope=ParameterScope.LOCAL,
    )

    return {
        "success": True,
        "match": True,
        "row": (
            matched_rows[0]
            if len(matched_rows) == 1
            else None
        ),
        "rows": matched_rows,
        "count": len(matched_rows),
    }
