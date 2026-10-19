from configuration.models.ruleset_config import RulesetConfig
from configuration.models.rule_config import RuleConfig

from configuration.serializers.ruleset_serializer import (
    RulesetSerializer
)


class RulesetService:

    def __init__(
        self,
        draft_service
    ):

        self.draft_service = draft_service

        self.serializer = RulesetSerializer()

    def get_draft(
        self,
        draft_id
    ):

        draft = self.draft_service.get_draft(
            draft_id
        )

        if draft is None:

            raise ValueError(
                "Draft not found"
            )

        return draft

    def create_ruleset(
        self,
        draft_id,
        name: str
    ):

        draft = self.get_draft(
            draft_id
        )

        ruleset = RulesetConfig(
            name=name
        )

        draft.configuration.add_ruleset(
            ruleset
        )

        return ruleset

    def list_rulesets(
        self,
        draft_id
    ):

        draft = self.get_draft(
            draft_id
        )

        return draft.configuration.rulesets

    def get_ruleset(
        self,
        draft_id,
        ruleset_id
    ):

        draft = self.get_draft(
            draft_id
        )

        return draft.configuration.get_ruleset(
            ruleset_id
        )

    def delete_ruleset(
        self,
        draft_id,
        ruleset_id
    ):

        draft = self.get_draft(
            draft_id
        )

        ruleset = draft.configuration.get_ruleset(
            ruleset_id
        )

        if ruleset is None:

            raise ValueError(
                "Ruleset not found"
            )

        draft.configuration.remove_ruleset(
            ruleset_id
        )

        return ruleset

    def add_rule(
        self,
        draft_id,
        ruleset_id,
        rule_name
    ):

        ruleset = self.get_ruleset(
            draft_id,
            ruleset_id
        )

        if ruleset is None:

            raise ValueError(
                "Ruleset not found"
            )

        rule = RuleConfig(
            name=rule_name
        )

        ruleset.add_rule(
            rule
        )

        return rule

    def delete_rule(
        self,
        draft_id,
        ruleset_id,
        rule_id
    ):

        ruleset = self.get_ruleset(
            draft_id,
            ruleset_id
        )

        if ruleset is None:

            raise ValueError(
                "Ruleset not found"
            )

        rule = None

        for item in ruleset.rules:

            if item.id == rule_id:

                rule = item

                break

        if rule is None:

            raise ValueError(
                "Rule not found"
            )

        ruleset.remove_rule(
            rule_id
        )

        return rule

    def export_ruleset(
        self,
        draft_id,
        ruleset_id
    ):

        ruleset = self.get_ruleset(
            draft_id,
            ruleset_id
        )

        if ruleset is None:

            raise ValueError(
                "Ruleset not found"
            )

        return self.serializer.export(
            ruleset
        )

    def import_ruleset(
        self,
        draft_id,
        data
    ):

        draft = self.get_draft(
            draft_id
        )

        ruleset = self.serializer.import_ruleset(
            data
        )

        draft.configuration.add_ruleset(
            ruleset
        )

        return ruleset