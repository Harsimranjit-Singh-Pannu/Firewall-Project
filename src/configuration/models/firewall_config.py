from dataclasses import dataclass, field

from .ruleset_config import RulesetConfig


@dataclass
class FirewallConfiguration:


    rulesets: list[RulesetConfig] = field(
        default_factory=list
    )


    def add_ruleset(
        self,
        ruleset: RulesetConfig
    ):

        self.rulesets.append(
            ruleset
        )


    def remove_ruleset(
        self,
        ruleset_id
    ):

        self.rulesets = [

            ruleset

            for ruleset in self.rulesets

            if ruleset.id != ruleset_id

        ]


    def get_ruleset(
        self,
        ruleset_id
    ):

        for ruleset in self.rulesets:

            if ruleset.id == ruleset_id:

                return ruleset


        return None