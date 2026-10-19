from uuid import UUID, uuid4

from configuration.models.operation_config import OperationConfig


class OperationSerializer:

    def serialize(
        self,
        operation: OperationConfig
    ):

        if operation is None:

            return None

        if not isinstance(
            operation,
            OperationConfig
        ):

            raise ValueError(
                f"Unsupported operation type: {type(operation)}"
            )

        return {

            "id": str(operation.id),

            "name": operation.name,

            "parameters": dict(
                operation.parameters
            )

        }

    def serialize_many(
        self,
        operations
    ):

        return [

            self.serialize(
                operation
            )

            for operation in operations

        ]

    def deserialize(
        self,
        data
    ):

        if data is None:

            return None

        operation_id = data.get(
            "id"
        )

        return OperationConfig(

            name=data["name"],

            parameters=dict(
                data.get(
                    "parameters",
                    {}
                )
            ),

            id=(

                UUID(operation_id)

                if operation_id

                else uuid4()

            )

        )

    def deserialize_many(
        self,
        data
    ):

        return [

            self.deserialize(
                operation
            )

            for operation in data

        ]