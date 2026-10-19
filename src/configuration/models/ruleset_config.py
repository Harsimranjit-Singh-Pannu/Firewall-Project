from dataclasses import dataclass, field
from uuid import UUID, uuid4

from .rule_config import RuleConfig

from rulesets.argument import Argument


@dataclass
class RulesetConfig:

    name: str

    id: UUID = field(
        default_factory=uuid4
    )

    rules: list[RuleConfig] = field(
        default_factory=list
    )

    arguments: list[Argument] = field(
        default_factory=list
    )


    def add_rule(
        self,
        rule: RuleConfig
    ):

        rule.order = len(self.rules) + 1

        self.rules.append(
            rule
        )


    def remove_rule(
        self,
        rule_id: UUID
    ):

        self.rules = [

            rule

            for rule in self.rules

            if rule.id != rule_id

        ]

        for index, rule in enumerate(
            self.rules,
            start=1
        ):

            rule.order = index


    def add_argument(
        self,
        argument: Argument
    ):

        if any(
            existing.name == argument.name
            for existing in self.arguments
        ):

            raise ValueError(
                f"Argument already exists: {argument.name}"
            )

        self.arguments.append(
            argument
        )


    def get_argument(
        self,
        name: str
    ):

        for argument in self.arguments:

            if argument.name == name:

                return argument

        return None