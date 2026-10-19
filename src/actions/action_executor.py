from actions import (
    ContinueAction,
    JumpToRuleset
)

from rulesets.argument_binding import ArgumentBinding

from conditions.enums import (
    SourceType,
    RightSourceType
)


class ActionExecutor:

    def build(
        self,
        action_config
    ):

        if action_config is None:

            return None

        action_type = action_config.type

        parameters = (
            action_config.parameters
            or {}
        )

        if action_type == "CONTINUE":

            return ContinueAction()

        if action_type == "JUMP":

            ruleset_name = parameters.get(
                "ruleset_name"
            )

            if not ruleset_name:

                raise ValueError(
                    "JUMP action requires 'ruleset_name'"
                )

            argument_bindings = self.build_argument_bindings(
                parameters.get(
                    "argument_bindings",
                    []
                )
            )

            return JumpToRuleset(

                ruleset_name=ruleset_name,

                argument_bindings=argument_bindings

            )

        raise ValueError(
            f"Unsupported action type: {action_type}"
        )

    def build_argument_bindings(
        self,
        bindings
    ):

        result = []

        for binding in bindings:

            if isinstance(
                binding,
                ArgumentBinding
            ):

                binding.validate()

                result.append(
                    binding
                )

                continue

            if not isinstance(
                binding,
                dict
            ):

                raise ValueError(
                    "Argument binding must be a dictionary"
                )

            source_type = binding.get(
                "source_type"
            )

            if isinstance(
                source_type,
                str
            ):

                if source_type == "Parameter":

                    source_type = SourceType.PARAMETER

                elif source_type == "User_Value":

                    source_type = RightSourceType.USER_VALUE

                else:

                    raise ValueError(
                        f"Unsupported argument source type: {source_type}"
                    )

            argument_binding = ArgumentBinding(

                argument_name=binding[
                    "argument_name"
                ],

                source_type=source_type,

                source_name=binding.get(
                    "source_name"
                ),

                value=binding.get(
                    "value"
                )

            )

            argument_binding.validate()

            result.append(
                argument_binding
            )

        return result