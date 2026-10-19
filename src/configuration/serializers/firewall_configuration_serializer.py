import json

from configuration.models.firewall_config import FirewallConfiguration

from configuration.serializers.ruleset_serializer import (
    RulesetSerializer
)


class FirewallConfigurationSerializer:

    def __init__(self):

        self.ruleset_serializer = RulesetSerializer()

    def serialize(
        self,
        configuration: FirewallConfiguration
    ):

        return self.export(
            configuration
        )

    def export(
        self,
        configuration: FirewallConfiguration
    ):

        if configuration is None:

            raise ValueError(
                "Configuration cannot be None"
            )

        return {

            "rulesets": [

                self.ruleset_serializer.export(
                    ruleset
                )

                for ruleset in configuration.rulesets

            ]

        }

    def export_json(
        self,
        configuration: FirewallConfiguration
    ):

        return json.dumps(

            self.export(
                configuration
            ),

            indent=4

        )