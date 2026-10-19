import base64


def execute(value):

    if not isinstance(value, str):

        raise TypeError(
            "Base64 decode accepts string input"
        )


    try:

        decoded = base64.b64decode(
            value
        ).decode("utf-8")


    except Exception as error:

        raise ValueError(
            f"Invalid Base64 value: {error}"
        )


    return {

        "success": True,

        "operation": "Base64Decode",

        "result": decoded

    }