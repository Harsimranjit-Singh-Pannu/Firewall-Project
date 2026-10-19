from uuid import UUID, uuid4

from configuration.models.firewall_config import FirewallConfiguration
from configuration.models.ruleset_config import RulesetConfig
from configuration.models.rule_config import RuleConfig

from configuration.serializers.action_serializer import (
    ActionSerializer
)

from configuration.serializers.operation_serializer import (
    OperationSerializer
)

from configuration.serializers.condition_serializer import (
    ConditionSerializer
)


class FirewallConfigurationDeserializer:

    def __init__(self):

        self.action_serializer = ActionSerializer()

        self.operation_serializer = OperationSerializer()

        self.condition_serializer = ConditionSerializer()

    def deserialize(
        self,
        data: dict
    ):

        configuration = FirewallConfiguration()

        for ruleset_data in data.get(
            "rulesets",
            []
        ):

            ruleset_id = ruleset_data.get(
                "id"
            )

            ruleset = RulesetConfig(

                name=ruleset_data["name"],

                id=(
                    UUID(ruleset_id)
                    if ruleset_id
                    else uuid4()
                )

            )

            for rule_data in ruleset_data.get(
                "rules",
                []
            ):

                rule_id = rule_data.get(
                    "id"
                )

                rule = RuleConfig(

                    name=rule_data["name"],

                    id=(
                        UUID(rule_id)
                        if rule_id
                        else uuid4()
                    ),

                    order=rule_data.get(
                        "order",
                        0
                    ),

                    condition_group=(
                        self.condition_serializer.deserialize_group(
                            rule_data.get(
                                "condition_group"
                            )
                        )
                    ),

                    operations=(
                        self.operation_serializer.deserialize_many(
                            rule_data.get(
                                "operations",
                                []
                            )
                        )
                    ),

                    action=(

                        self.action_serializer.deserialize(
                            rule_data["action"]
                        )

                        if rule_data.get(
                            "action"
                        )

                        else None

                    )

                )

                ruleset.add_rule(
                    rule
                )

            configuration.add_ruleset(
                ruleset
            )

        return configuration