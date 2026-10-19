import base64



def execute(value):

    if not isinstance(value, str):

        raise TypeError(
            "Base64 encode accepts string input"
        )


    encoded = base64.b64encode(

        value.encode("utf-8")

    ).decode("utf-8")


    return {

        "success": True,

        "operation": "Base64Encode",

        "result": encoded

    }