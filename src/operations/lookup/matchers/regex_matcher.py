import re



def match(
    input_value,
    pattern
):

    if not isinstance(input_value, str):

        input_value = str(input_value)


    result = re.match(
        pattern,
        input_value
    )


    return result is not None