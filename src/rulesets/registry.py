class RulesetRegistry:


    def __init__(self):

        self.rulesets = {}



    def register(
        self,
        ruleset
    ):

        if ruleset.name in self.rulesets:

            raise ValueError(
                f"Ruleset already exists: {ruleset.name}"
            )


        self.rulesets[ruleset.name] = ruleset



    def get(
        self,
        name
    ):

        ruleset = self.rulesets.get(name)


        if ruleset is None:

            raise ValueError(
                f"Ruleset not found: {name}"
            )


        return ruleset



    def exists(
        self,
        name
    ):

        return name in self.rulesets