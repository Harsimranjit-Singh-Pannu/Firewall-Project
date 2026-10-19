from uuid import UUID, uuid4

from configuration.models.condition_config import ConditionConfig
from configuration.models.condition_group_config import ConditionGroupConfig


class ConditionSerializer:

    def serialize(
        self,
        condition: ConditionConfig
    ):

        if condition is None:

            return None

        return {

            "id": str(condition.id),

            "left_type": condition.left_type,

            "left_name": condition.left_name,

            "operator": condition.operator,

            "match_mode": condition.match_mode,

            "right_type": condition.right_type,

            "right_value": condition.right_value

        }

    def deserialize(
        self,
        data
    ):

        if data is None:

            return None

        condition_id = data.get(
            "id"
        )

        return ConditionConfig(

            left_type=data["left_type"],

            left_name=data["left_name"],

            operator=data["operator"],

            match_mode=data.get(
                "match_mode",
                "Any"
            ),

            right_type=data.get(
                "right_type"
            ),

            right_value=data.get(
                "right_value"
            ),

            id=(
                UUID(condition_id)
                if condition_id
                else uuid4()
            )

        )

    def serialize_group(
        self,
        group: ConditionGroupConfig
    ):

        if group is None:

            return None

        return {

            "id": str(group.id),

            "operator": group.operator,

            "conditions": [

                self.serialize(
                    condition
                )

                for condition in group.conditions

            ]

        }

    def deserialize_group(
        self,
        data
    ):

        if data is None:

            return None

        group_id = data.get(
            "id"
        )

        conditions = [

            self.deserialize(
                condition
            )

            for condition in data.get(
                "conditions",
                []
            )

        ]

        return ConditionGroupConfig(

            operator=data.get(
                "operator",
                "AND"
            ),

            id=(
                UUID(group_id)
                if group_id
                else uuid4()
            ),

            conditions=conditions

        )