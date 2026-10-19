import re



def match(
    value,
    pattern
):

    result = re.search(
        pattern,
        value
    )


    return {

        "success": True,

        "operation": "RegexMatch",

        "result": result is not None

    }



def replace(
    value,
    pattern,
    replacement
):

    result = re.sub(
        pattern,
        replacement,
        value
    )


    return {

        "success": True,

        "operation": "RegexReplace",

        "result": result

    }