from rulesets.registry import RulesetRegistry

from rulesets.executor import RulesetExecutor

from runtime.builder import RuntimeBuilder



class FirewallRuntime:


    def __init__(
        self,
        configuration,
        rule_evaluator
    ):

        self.configuration = configuration

        self.builder = RuntimeBuilder()


        self.registry = RulesetRegistry()


        runtime_rulesets = self.builder.build_rulesets(

            configuration

        )


        for ruleset in runtime_rulesets:

            self.registry.register(

                ruleset

            )


        self.executor = RulesetExecutor(

            rule_evaluator,

            self.registry

        )



    def execute(
        self,
        ruleset_name,
        context,
        arguments=None
    ):


        ruleset = self.registry.get(

            ruleset_name

        )


        return self.executor.execute(

            ruleset,

            context,

            arguments

        )