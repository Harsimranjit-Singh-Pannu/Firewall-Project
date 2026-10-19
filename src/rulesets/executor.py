from actions import (
    ContinueAction,
    JumpToRuleset
)

from conditions.enums import (
    SourceType,
    RightSourceType
)


class RulesetExecutor:

    MAX_JUMP_DEPTH = 50

    def __init__(
        self,
        rule_evaluator,
        registry
    ):

        self.rule_evaluator = rule_evaluator

        self.registry = registry

    def resolve_arguments(
        self,
        bindings,
        context
    ):

        if not bindings:

            return None

        arguments = {}

        for binding in bindings:

            binding.validate()

            if binding.source_type == SourceType.PARAMETER:

                parameter = context.get_parameter(
                    binding.source_name
                )

                if parameter is None:

                    raise ValueError(
                        f"Missing parameter: {binding.source_name}"
                    )

                arguments[
                    binding.argument_name
                ] = parameter.value

            elif binding.source_type == RightSourceType.USER_VALUE:

                arguments[
                    binding.argument_name
                ] = binding.value

            else:

                raise ValueError(
                    f"Unsupported argument source: "
                    f"{binding.source_type}"
                )

        return arguments

    def execute(
        self,
        ruleset,
        context,
        arguments=None,
        depth=0
    ):

        if depth > self.MAX_JUMP_DEPTH:

            raise RuntimeError(
                "Maximum ruleset jump depth exceeded"
            )

        ruleset.validate()

        arguments = ruleset.validate_arguments(
            arguments
        )

        context.enter_ruleset(
            ruleset.name
        )

        last_action = None

        try:

            for rule in ruleset.rules:

                result = self.rule_evaluator.evaluate(
                    rule,
                    context,
                    arguments
                )

                if result is None:

                    continue

                if isinstance(
                    result,
                    ContinueAction
                ):

                    last_action = result

                    continue

                if isinstance(
                    result,
                    JumpToRuleset
                ):

                    target = self.registry.get(
                        result.ruleset_name
                    )

                    target_arguments = self.resolve_arguments(
                        result.argument_bindings,
                        context
                    )

                    child_result = self.execute(
                        target,
                        context,
                        target_arguments,
                        depth + 1
                    )

                    if child_result is not None:

                        return child_result

                    continue

                return result

        finally:

            context.exit_ruleset()

        return last_action