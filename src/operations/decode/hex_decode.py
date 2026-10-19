def execute(value):

    if not isinstance(value, str):

        raise TypeError(
            "Hex decode accepts string input"
        )


    try:

        decoded = bytes.fromhex(
            value
        ).decode("utf-8")


    except Exception as error:

        raise ValueError(
            f"Invalid hex value: {error}"
        )


    return {

        "success": True,

        "operation": "HexDecode",

        "result": decoded

    }