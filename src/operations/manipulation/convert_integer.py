def execute(value):

    try:

        result = int(value)


    except ValueError:

        raise ValueError(
            f"Cannot convert {value} to integer"
        )


    return {

        "success": True,

        "operation": "ConvertToInteger",

        "result": result

    }