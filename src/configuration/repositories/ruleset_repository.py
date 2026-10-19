from uuid import UUID


class RulesetRepository:

    def __init__(self):

        self._rulesets = {}


    def save(self, ruleset):

        self._rulesets[ruleset.id] = ruleset

        return ruleset


    def get(self, ruleset_id: UUID):

        return self._rulesets.get(ruleset_id)


    def list(self):

        return list(self._rulesets.values())


    def delete(self, ruleset_id: UUID):

        self._rulesets.pop(
            ruleset_id,
            None
        )