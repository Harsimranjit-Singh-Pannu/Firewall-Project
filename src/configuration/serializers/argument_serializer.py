from rulesets.argument import (
    Argument,
    DataType,
    CollectionType
)


class ArgumentSerializer:

    def serialize(
        self,
        argument: Argument
    ):

        if argument is None:

            return None

        if not isinstance(
            argument,
            Argument
        ):

            raise ValueError(
                f"Unsupported argument type: {type(argument)}"
            )

        return {

            "name": argument.name,

            "datatype": argument.datatype.value,

            "collection_type": (
                argument.collection_type.value
            ),

            "default_value": argument.default_value

        }


    def serialize_many(
        self,
        arguments
    ):

        return [

            self.serialize(
                argument
            )

            for argument in arguments

        ]


    def deserialize(
        self,
        data
    ):

        if data is None:

            return None

        return Argument(

            name=data["name"],

            datatype=DataType(
                data["datatype"]
            ),

            collection_type=CollectionType(
                data.get(
                    "collection_type",
                    CollectionType.SCALAR.value
                )
            ),

            default_value=data.get(
                "default_value"
            )

        )


    def deserialize_many(
        self,
        data
    ):

        return [

            self.deserialize(
                argument
            )

            for argument in data

        ]