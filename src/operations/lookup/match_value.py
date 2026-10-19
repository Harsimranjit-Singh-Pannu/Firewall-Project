from .matchers.regex_matcher import match as regex_match



def execute(

    input_value,

    rows,

    conditions,

    context=None,

    save_parameter_name=None

):

    for row in rows:


        matched = True


        for condition in conditions:


            column_value = row.get(
                condition.column
            )


            if condition.match_type == "Regex":


                if not regex_match(

                    input_value,

                    column_value

                ):

                    matched = False

                    break



        if matched:


            if context and save_parameter_name:


                context.set_parameter(

                    save_parameter_name,

                    row

                )


            return {

                "success": True,

                "match": True,

                "row": row

            }



    return {

        "success": True,

        "match": False,

        "row": None

    }