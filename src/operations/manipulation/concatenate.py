def execute(
    values,
    separator=""
):

    if not isinstance(values, list):

        raise TypeError(
            "Values must be a list"
        )


    result = separator.join(
        str(value)
        for value in values
    )


    return {

        "success": True,

        "operation": "ConcatenateStrings",

        "result": result

    }