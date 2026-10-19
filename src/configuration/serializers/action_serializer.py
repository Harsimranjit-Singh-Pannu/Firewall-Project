from uuid import UUID, uuid4

from configuration.models.action_config import ActionConfig

from rulesets.argument_binding import ArgumentBinding

from conditions.enums import (
    SourceType,
    RightSourceType
)


class ActionSerializer:

    def serialize(
        self,
        action: ActionConfig
    ):

        if action is None:

            return None

        if not isinstance(
            action,
            ActionConfig
        ):

            raise ValueError(
                f"Unsupported action type: {type(action)}"
            )

        parameters = dict(
            action.parameters
        )

        argument_bindings = parameters.get(
            "argument_bindings"
        )

        if argument_bindings is not None:

            parameters["argument_bindings"] = [

                self.serialize_argument_binding(
                    binding
                )

                for binding in argument_bindings

            ]

        return {

            "id": str(action.id),

            "type": action.type,

            "parameters": parameters

        }

    def serialize_argument_binding(
        self,
        binding
    ):

        if not isinstance(
            binding,
            ArgumentBinding
        ):

            raise ValueError(
                f"Unsupported argument binding type: "
                f"{type(binding)}"
            )

        return {

            "argument_name": binding.argument_name,

            "source_type": binding.source_type.value,

            "source_name": binding.source_name,

            "value": binding.value

        }

    def deserialize(
        self,
        data
    ):

        if data is None:

            return None

        action_id = data.get(
            "id"
        )

        parameters = dict(
            data.get(
                "parameters",
                {}
            )
        )

        argument_bindings = parameters.get(
            "argument_bindings"
        )

        if argument_bindings is not None:

            parameters["argument_bindings"] = [

                self.deserialize_argument_binding(
                    binding
                )

                for binding in argument_bindings

            ]

        return ActionConfig(

            type=data["type"],

            parameters=parameters,

            id=(

                UUID(action_id)

                if action_id

                else uuid4()

            )

        )

    def deserialize_argument_binding(
        self,
        data
    ):

        source_type = data.get(
            "source_type"
        )

        if source_type == SourceType.PARAMETER.value:

            resolved_source_type = SourceType.PARAMETER

        elif source_type == RightSourceType.USER_VALUE.value:

            resolved_source_type = RightSourceType.USER_VALUE

        else:

            raise ValueError(
                f"Unsupported argument binding source: "
                f"{source_type}"
            )

        return ArgumentBinding(

            argument_name=data["argument_name"],

            source_type=resolved_source_type,

            source_name=data.get(
                "source_name"
            ),

            value=data.get(
                "value"
            )

        )