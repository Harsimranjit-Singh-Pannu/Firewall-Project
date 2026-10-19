from uuid import UUID, uuid4

from configuration.models.ruleset_config import RulesetConfig
from configuration.models.rule_config import RuleConfig

from rulesets.argument import (
    Argument,
    DataType,
    CollectionType
)

from configuration.serializers.action_serializer import (
    ActionSerializer
)

from configuration.serializers.operation_serializer import (
    OperationSerializer
)

from configuration.serializers.condition_serializer import (
    ConditionSerializer
)


class RulesetSerializer:

    def __init__(self):

        self.action_serializer = ActionSerializer()

        self.operation_serializer = OperationSerializer()

        self.condition_serializer = ConditionSerializer()


    def serialize_argument(
        self,
        argument: Argument
    ):

        return {

            "name": argument.name,

            "datatype": argument.datatype.value,

            "collection_type": argument.collection_type.value,

            "default_value": argument.default_value

        }


    def deserialize_argument(
        self,
        data: dict
    ):

        return Argument(

            name=data["name"],

            datatype=DataType(
                data["datatype"]
            ),

            collection_type=CollectionType(
                data.get(
                    "collection_type",
                    CollectionType.SCALAR.value
                )
            ),

            default_value=data.get(
                "default_value"
            )

        )


    def export(
        self,
        ruleset: RulesetConfig
    ):

        return {

            "id": str(ruleset.id),

            "name": ruleset.name,

            "arguments": [

                self.serialize_argument(
                    argument
                )

                for argument in ruleset.arguments

            ],

            "rules": [

                {

                    "id": str(rule.id),

                    "name": rule.name,

                    "order": rule.order,

                    "condition_group": (

                        self.condition_serializer.serialize_group(
                            rule.condition_group
                        )

                        if rule.condition_group is not None

                        else None

                    ),

                    "operations": (

                        self.operation_serializer.serialize_many(
                            rule.operations
                        )

                    ),

                    "action": (

                        self.action_serializer.serialize(
                            rule.action
                        )

                        if rule.action is not None

                        else None

                    )

                }

                for rule in ruleset.rules

            ]

        }


    def import_ruleset(
        self,
        data: dict
    ):

        ruleset_id = data.get(
            "id"
        )

        ruleset = RulesetConfig(

            name=data["name"],

            id=(

                UUID(ruleset_id)

                if ruleset_id

                else uuid4()

            )

        )


        for argument_data in data.get(
            "arguments",
            []
        ):

            ruleset.add_argument(

                self.deserialize_argument(
                    argument_data
                )

            )


        for rule_data in data.get(
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


        return ruleset