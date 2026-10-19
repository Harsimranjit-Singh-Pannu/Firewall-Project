import copy
from uuid import uuid4

import pytest

from actions import ContinueAction, JumpToRuleset
from actions.action_executor import ActionExecutor

from arguments import ArgumentStore

from conditions import (
    Condition,
    ConditionEvaluator,
    ConditionGroup,
    ConditionGroupEvaluator,
    GroupOperator,
    MatchMode,
    Operator,
    RightSourceType,
    SourceType,
)

from conditions.comparators import ComparatorFactory

from configuration.models.action_config import ActionConfig
from configuration.models.condition_config import ConditionConfig
from configuration.models.condition_group_config import ConditionGroupConfig
from configuration.models.firewall_config import FirewallConfiguration
from configuration.models.operation_config import OperationConfig
from configuration.models.rule_config import RuleConfig
from configuration.models.ruleset_config import RulesetConfig

from configuration.serializers.action_serializer import ActionSerializer
from configuration.serializers.condition_serializer import ConditionSerializer
from configuration.serializers.firewall_configuration_deserializer import (
    FirewallConfigurationDeserializer,
)
from configuration.serializers.firewall_configuration_serializer import (
    FirewallConfigurationSerializer,
)
from configuration.serializers.operation_serializer import OperationSerializer
from configuration.serializers.ruleset_serializer import RulesetSerializer

from drafts.draft_repository import DraftRepository
from drafts.draft_service import DraftService

from engine.context import ExecutionContext

from operations.manipulation.arithmetic import (
    ArithmeticOperator,
    execute as arithmetic_execute,
)
from operations.manipulation.concatenate import execute as concatenate_execute
from operations.manipulation.convert_integer import execute as convert_integer
from operations.manipulation.convert_string import execute as convert_string
from operations.manipulation.regex_replace import match as regex_match
from operations.manipulation.regex_replace import replace as regex_replace

from operations.parameter.set_parameter import SetParameterOperation

from parameters import Parameter, ParameterScope, ParameterStore

from rules.operation_definition import Operation
from rules.operation_executor import OperationExecutor
from rules.rule import Rule
from rules.evaluator import RuleEvaluator

from rulesets.argument_binding import ArgumentBinding
from rulesets.executor import RulesetExecutor
from rulesets.registry import RulesetRegistry
from rulesets.ruleset import Ruleset
from rulesets.argument import Argument, DataType, CollectionType

from configuration.services.rule_service import RuleService
from configuration.services.ruleset_service import RulesetService


# ============================================================
# Helpers / test doubles
# ============================================================



class FakeVersion:

    def __init__(
        self,
        configuration,
        name="Test Version",
        description=None,
        parent_version_id=None,
    ):
        self.id = uuid4()
        self.configuration = configuration
        self.name = name
        self.description = description
        self.parent_version_id = parent_version_id


class FakeVersionService:

    def __init__(self):
        self.versions = {}

    def add_version(self, version):
        self.versions[version.id] = version

    def get_version(self, version_id):
        return self.versions.get(version_id)

    def create_version(
        self,
        configuration,
        name="Test Version",
        description=None,
        parent_version_id=None,
    ):
        version = FakeVersion(
            copy.deepcopy(configuration),
            name=name,
            description=description,
            parent_version_id=parent_version_id,
        )
        self.versions[version.id] = version
        return version

class RuntimeRuleset:

    """
    Small runtime ruleset implementation matching what
    RulesetExecutor expects.
    """

    def __init__(
        self,
        name,
        rules,
        arguments=None,
    ):
        self.name = name
        self.rules = rules
        self.arguments = arguments or {}

    def validate(self):
        for rule in self.rules:
            rule.validate()

        return True

    def validate_arguments(self, arguments):
        arguments = arguments or {}

        for name, definition in self.arguments.items():

            if name not in arguments:

                if definition.default_value is not None:
                    arguments[name] = definition.default_value
                    continue

                raise ValueError(
                    f"Missing argument: {name}"
                )

        return arguments


def make_condition_group(*conditions, operator=GroupOperator.AND):

    return ConditionGroup(
        operator,
        list(conditions),
    )


def make_runtime_rule(
    condition_group,
    action=None,
    operations=None,
    name="rule",
):

    rule = Rule(name)

    rule.set_condition_group(
        condition_group
    )

    for operation in operations or []:
        rule.add_operation(operation)

    rule.set_action(
        action or ContinueAction()
    )

    return rule


def make_context():

    return ExecutionContext()


# ============================================================
# ExecutionContext
# ============================================================


class TestExecutionContext:

    def test_set_and_get_parameter(self):

        context = make_context()

        context.set_parameter(
            "username",
            "simran",
        )

        parameter = context.get_parameter(
            "username"
        )

        assert parameter is not None
        assert parameter.value == "simran"

    def test_set_and_get_argument(self):

        context = make_context()

        context.set_argument(
            "user_id",
            123,
        )

        assert context.get_argument(
            "user_id"
        ) == 123

    def test_ruleset_path(self):

        context = make_context()

        context.enter_ruleset("A")
        context.enter_ruleset("B")

        assert context.get_ruleset_path() == [
            "A",
            "B",
        ]

        assert context.exit_ruleset() == "B"
        assert context.get_ruleset_path() == ["A"]

        assert context.exit_ruleset() == "A"
        assert context.get_ruleset_path() == []

    def test_exit_empty_ruleset_path(self):

        context = make_context()

        assert context.exit_ruleset() is None


# ============================================================
# ParameterStore
# ============================================================


class TestParameterStore:

    def test_store_and_retrieve_parameter(self):

        store = ParameterStore()

        parameter = Parameter(
            name="x",
            value=10,
            datatype="Integer",
        )

        store.set(parameter)

        assert store.get("x") == 10
        assert store.get_parameter("x") == parameter
        assert store.exists("x")

    def test_remove_parameter(self):

        store = ParameterStore()

        store.set(
            Parameter(
                name="x",
                value=10,
                datatype="Integer",
            )
        )

        store.remove("x")

        assert not store.exists("x")
        assert store.get("x") is None

    def test_higher_scope_cannot_be_overwritten_by_lower_scope(self):

        store = ParameterStore()

        store.set(
            Parameter(
                name="x",
                value="system",
                datatype="String",
                scope=ParameterScope.SYSTEM,
            )
        )

        with pytest.raises(ValueError):
            store.set(
                Parameter(
                    name="x",
                    value="local",
                    datatype="String",
                    scope=ParameterScope.LOCAL,
                )
            )

    def test_higher_scope_can_replace_lower_scope(self):

        store = ParameterStore()

        store.set(
            Parameter(
                name="x",
                value="local",
                datatype="String",
                scope=ParameterScope.LOCAL,
            )
        )

        store.set(
            Parameter(
                name="x",
                value="global",
                datatype="String",
                scope=ParameterScope.GLOBAL,
            )
        )

        assert store.get("x") == "global"


# ============================================================
# ArgumentStore
# ============================================================


class TestArgumentStore:

    def test_argument_store(self):

        store = ArgumentStore()

        store.set("x", 123)

        assert store.get("x") == 123
        assert store.exists("x")
        assert store.all()["x"] == 123


# ============================================================
# ArgumentBinding
# ============================================================


class TestArgumentBinding:

    def test_parameter_binding_is_valid(self):

        binding = ArgumentBinding(
            argument_name="username",
            source_type=SourceType.PARAMETER,
            source_name="current_user",
        )

        assert binding.validate() is True

    def test_user_value_binding_is_valid(self):

        binding = ArgumentBinding(
            argument_name="username",
            source_type=RightSourceType.USER_VALUE,
            value="simran",
        )

        assert binding.validate() is True

    def test_parameter_binding_requires_source_name(self):

        binding = ArgumentBinding(
            argument_name="username",
            source_type=SourceType.PARAMETER,
        )

        with pytest.raises(
            ValueError,
            match="Parameter source requires source_name",
        ):
            binding.validate()

    def test_parameter_binding_cannot_have_value(self):

        binding = ArgumentBinding(
            argument_name="username",
            source_type=SourceType.PARAMETER,
            source_name="user",
            value="simran",
        )

        with pytest.raises(
            ValueError,
            match="Parameter source cannot have value",
        ):
            binding.validate()

    def test_user_value_requires_value(self):

        binding = ArgumentBinding(
            argument_name="username",
            source_type=RightSourceType.USER_VALUE,
        )

        with pytest.raises(
            ValueError,
            match="User value source requires value",
        ):
            binding.validate()

    def test_user_value_cannot_have_source_name(self):

        binding = ArgumentBinding(
            argument_name="username",
            source_type=RightSourceType.USER_VALUE,
            source_name="user",
            value="simran",
        )

        with pytest.raises(
            ValueError,
            match="User value source cannot have source_name",
        ):
            binding.validate()


# ============================================================
# ActionExecutor
# ============================================================


class TestActionExecutor:

    def test_build_continue_action(self):

        config = ActionConfig(
            type="CONTINUE"
        )

        action = ActionExecutor().build(config)

        assert isinstance(
            action,
            ContinueAction,
        )

    def test_build_jump_action(self):

        config = ActionConfig(
            type="JUMP",
            parameters={
                "ruleset_name": "Child",
            },
        )

        action = ActionExecutor().build(config)

        assert isinstance(
            action,
            JumpToRuleset,
        )

        assert action.ruleset_name == "Child"
        assert action.argument_bindings == []

    def test_build_jump_with_parameter_binding(self):

        config = ActionConfig(
            type="JUMP",
            parameters={
                "ruleset_name": "Child",
                "argument_bindings": [
                    {
                        "argument_name": "username",
                        "source_type": "Parameter",
                        "source_name": "current_user",
                    }
                ],
            },
        )

        action = ActionExecutor().build(config)

        assert len(
            action.argument_bindings
        ) == 1

        binding = action.argument_bindings[0]

        assert binding.argument_name == "username"
        assert binding.source_type == SourceType.PARAMETER

    def test_build_jump_requires_ruleset_name(self):

        config = ActionConfig(
            type="JUMP",
            parameters={},
        )

        with pytest.raises(
            ValueError,
            match="JUMP action requires 'ruleset_name'",
        ):
            ActionExecutor().build(config)

    def test_unsupported_action(self):

        config = ActionConfig(
            type="UNKNOWN"
        )

        with pytest.raises(
            ValueError,
            match="Unsupported action type",
        ):
            ActionExecutor().build(config)


# ============================================================
# Condition comparators
# ============================================================


class TestComparators:

    def test_string_equals(self):

        comparator = ComparatorFactory.get("String")

        assert comparator.compare(
            "hello",
            "hello",
            Operator.EQUALS,
        )

    def test_string_contains(self):

        comparator = ComparatorFactory.get("String")

        assert comparator.compare(
            "hello world",
            "world",
            Operator.CONTAINS,
        )

    def test_string_regex(self):

        comparator = ComparatorFactory.get("String")

        assert comparator.compare(
            "abc123",
            r"abc\d+",
            Operator.REGEX_MATCH,
        )

    def test_integer_comparison(self):

        comparator = ComparatorFactory.get("Integer")

        assert comparator.compare(
            10,
            5,
            Operator.GREATER_THAN,
        )

        assert comparator.compare(
            10,
            10,
            Operator.GREATER_THAN_EQUALS,
        )

        assert comparator.compare(
            5,
            10,
            Operator.LESS_THAN,
        )

    def test_boolean_comparison(self):

        comparator = ComparatorFactory.get("Boolean")

        assert comparator.compare(
            True,
            "true",
            Operator.EQUALS,
        )

        assert comparator.compare(
            "false",
            False,
            Operator.EQUALS,
        )

    def test_ipv4_comparison(self):

        comparator = ComparatorFactory.get("IPv4")

        assert comparator.compare(
            "192.168.1.1",
            "192.168.1.1",
            Operator.EQUALS,
        )

        assert comparator.compare(
            "192.168.1.1",
            "192.168.1.2",
            Operator.NOT_EQUALS,
        )


# ============================================================
# ConditionResolver / ConditionEvaluator
# ============================================================


class TestConditions:

    def test_parameter_equals_user_value(self):

        context = make_context()

        context.set_parameter(
            "username",
            "simran",
        )

        condition = Condition(
            left_type=SourceType.PARAMETER,
            left_name="username",
            operator=Operator.EQUALS,
            right_type=RightSourceType.USER_VALUE,
            right_value="simran",
        )

        evaluator = ConditionEvaluator()

        assert evaluator.evaluate(
            condition,
            context,
        ) is True

    def test_parameter_not_equals(self):

        context = make_context()

        context.set_parameter(
            "username",
            "simran",
        )

        condition = Condition(
            left_type=SourceType.PARAMETER,
            left_name="username",
            operator=Operator.NOT_EQUALS,
            right_type=RightSourceType.USER_VALUE,
            right_value="bob",
        )

        assert ConditionEvaluator().evaluate(
            condition,
            context,
        ) is True

    def test_argument_condition(self):

        context = make_context()

        arguments = {
            "age": 25,
        }

        condition = Condition(
            left_type=SourceType.ARGUMENT,
            left_name="age",
            operator=Operator.GREATER_THAN,
            right_type=RightSourceType.USER_VALUE,
            right_value=18,
        )

        assert ConditionEvaluator().evaluate(
            condition,
            context,
            arguments,
        ) is True

    def test_right_side_parameter(self):

        context = make_context()

        context.set_parameter(
            "expected",
            "approved",
        )

        context.set_parameter(
            "status",
            "approved",
        )

        condition = Condition(
            left_type=SourceType.PARAMETER,
            left_name="status",
            operator=Operator.EQUALS,
            right_type=RightSourceType.PARAMETER,
            right_value="expected",
        )

        assert ConditionEvaluator().evaluate(
            condition,
            context,
        ) is True

    def test_exists(self):

        context = make_context()

        context.set_parameter(
            "username",
            "simran",
        )

        condition = Condition(
            left_type=SourceType.PARAMETER,
            left_name="username",
            operator=Operator.EXISTS,
        )

        assert ConditionEvaluator().evaluate(
            condition,
            context,
        ) is True

    def test_does_not_exist(self):

        context = make_context()

        condition = Condition(
            left_type=SourceType.PARAMETER,
            left_name="missing",
            operator=Operator.DOES_NOT_EXIST,
        )

        assert ConditionEvaluator().evaluate(
            condition,
            context,
        ) is True

    def test_missing_left_value_returns_false(self):

        context = make_context()

        condition = Condition(
            left_type=SourceType.PARAMETER,
            left_name="missing",
            operator=Operator.EQUALS,
            right_type=RightSourceType.USER_VALUE,
            right_value="x",
        )

        assert ConditionEvaluator().evaluate(
            condition,
            context,
        ) is False

    def test_list_any(self):

        context = make_context()

        context.set_parameter(
            "roles",
            ["user", "admin", "guest"],
            datatype="String",
        )

        condition = Condition(
            left_type=SourceType.PARAMETER,
            left_name="roles",
            operator=Operator.EQUALS,
            match_mode=MatchMode.ANY,
            right_type=RightSourceType.USER_VALUE,
            right_value="admin",
        )

        assert ConditionEvaluator().evaluate(
            condition,
            context,
        ) is True

    def test_list_all(self):

        context = make_context()

        context.set_parameter(
            "numbers",
            [10, 20, 30],
            datatype="Integer",
        )

        condition = Condition(
            left_type=SourceType.PARAMETER,
            left_name="numbers",
            operator=Operator.GREATER_THAN,
            match_mode=MatchMode.ALL,
            right_type=RightSourceType.USER_VALUE,
            right_value=5,
        )

        assert ConditionEvaluator().evaluate(
            condition,
            context,
        ) is True

    def test_list_none(self):

        context = make_context()

        context.set_parameter(
            "roles",
            ["user", "guest"],
            datatype="String",
        )

        condition = Condition(
            left_type=SourceType.PARAMETER,
            left_name="roles",
            operator=Operator.EQUALS,
            match_mode=MatchMode.NONE,
            right_type=RightSourceType.USER_VALUE,
            right_value="admin",
        )

        assert ConditionEvaluator().evaluate(
            condition,
            context,
        ) is True


# ============================================================
# ConditionGroup
# ============================================================


class TestConditionGroups:

    def test_and_group(self):

        context = make_context()

        context.set_parameter("x", 10)
        context.set_parameter("y", 20)

        evaluator = ConditionGroupEvaluator(
            ConditionEvaluator()
        )

        group = ConditionGroup(
            GroupOperator.AND,
            [
                Condition(
                    SourceType.PARAMETER,
                    "x",
                    Operator.EQUALS,
                    right_type=RightSourceType.USER_VALUE,
                    right_value=10,
                ),
                Condition(
                    SourceType.PARAMETER,
                    "y",
                    Operator.EQUALS,
                    right_type=RightSourceType.USER_VALUE,
                    right_value=20,
                ),
            ],
        )

        assert evaluator.evaluate(
            group,
            context,
        ) is True

    def test_and_group_fails_if_one_condition_fails(self):

        context = make_context()

        context.set_parameter("x", 10)
        context.set_parameter("y", 20)

        evaluator = ConditionGroupEvaluator(
            ConditionEvaluator()
        )

        group = ConditionGroup(
            GroupOperator.AND,
            [
                Condition(
                    SourceType.PARAMETER,
                    "x",
                    Operator.EQUALS,
                    right_type=RightSourceType.USER_VALUE,
                    right_value=10,
                ),
                Condition(
                    SourceType.PARAMETER,
                    "y",
                    Operator.EQUALS,
                    right_type=RightSourceType.USER_VALUE,
                    right_value=999,
                ),
            ],
        )

        assert evaluator.evaluate(
            group,
            context,
        ) is False

    def test_or_group(self):

        context = make_context()

        context.set_parameter("status", "pending")

        evaluator = ConditionGroupEvaluator(
            ConditionEvaluator()
        )

        group = ConditionGroup(
            GroupOperator.OR,
            [
                Condition(
                    SourceType.PARAMETER,
                    "status",
                    Operator.EQUALS,
                    right_type=RightSourceType.USER_VALUE,
                    right_value="approved",
                ),
                Condition(
                    SourceType.PARAMETER,
                    "status",
                    Operator.EQUALS,
                    right_type=RightSourceType.USER_VALUE,
                    right_value="pending",
                ),
            ],
        )

        assert evaluator.evaluate(
            group,
            context,
        ) is True

    def test_empty_group_rejected(self):

        with pytest.raises(
            ValueError,
            match="at least one condition",
        ):
            ConditionGroup(
                GroupOperator.AND,
                [],
            )


# ============================================================
# Operations
# ============================================================


class TestOperations:

    def test_arithmetic_add(self):

        result = arithmetic_execute(

            [
                10,
                5
            ],

            ArithmeticOperator.ADD,

        )

        assert result == 15
        


    def test_arithmetic_subtract(self):

        result = arithmetic_execute(

            [
                10,
                5
            ],

            ArithmeticOperator.SUBTRACT,

        )
        assert result == 5


    def test_arithmetic_multiply(self):

        result = arithmetic_execute(

            [
                10,
                5
            ],

            ArithmeticOperator.MULTIPLY,

        )
        assert result == 50


    def test_arithmetic_divide(self):

        result = arithmetic_execute(

            [
                10,
                5
            ],

            ArithmeticOperator.DIVIDE,

        )
        assert result == 2


    def test_division_by_zero(self):

        with pytest.raises(
            ValueError,
            match="Division by zero",
        ):

            arithmetic_execute(

                [
                    10,
                    0
                ],

                ArithmeticOperator.DIVIDE,

            )
    def test_arithmetic_add_multiple_operands(self):

        result = arithmetic_execute(

            [
                10,
                20,
                30,
                40
            ],

            ArithmeticOperator.ADD,

        )
        assert result == 100


    def test_arithmetic_subtract_multiple_operands(self):

        result = arithmetic_execute(

            [
                100,
                20,
                10,
                5
            ],

            ArithmeticOperator.SUBTRACT,

        )
        assert result == 65


    def test_arithmetic_multiply_multiple_operands(self):

        result = arithmetic_execute(

            [
                2,
                3,
                4,
                5
            ],

            ArithmeticOperator.MULTIPLY,

        )
        assert result == 120


    def test_arithmetic_divide_multiple_operands(self):

        result = arithmetic_execute(

            [
                100,
                2,
                5
            ],

            ArithmeticOperator.DIVIDE,

        )
        assert result == 10

    def test_concatenate(self):

        result = concatenate_execute(
            ["hello", "world"],
            " ",
        )

        assert result["result"] == "hello world"

    def test_convert_integer(self):

        result = convert_integer("123")

        assert result["result"] == 123

    def test_convert_string(self):

        result = convert_string(123)

        assert result["result"] == "123"

    def test_regex_match(self):

        result = regex_match(
            "hello123",
            r"hello\d+",
        )

        assert result["result"] is True

    def test_regex_replace(self):

        result = regex_replace(
            "hello123",
            r"\d+",
            "456",
        )

        assert result["result"] == "hello456"


# ============================================================
# SetParameterOperation
# ============================================================


class TestSetParameterOperation:

    def test_set_parameter(self):

        context = make_context()

        operation = SetParameterOperation()

        result = operation.execute(
            context,
            {
                "name": "username",
                "value": "simran",
            },
        )

        assert result is True
        assert context.get_parameter(
            "username"
        ).value == "simran"

    def test_missing_name(self):

        context = make_context()

        with pytest.raises(
            ValueError,
            match="requires 'name'",
        ):
            SetParameterOperation().execute(
                context,
                {
                    "value": "x",
                },
            )

    def test_missing_value(self):

        context = make_context()

        with pytest.raises(
            ValueError,
            match="requires 'value'",
        ):
            SetParameterOperation().execute(
                context,
                {
                    "name": "x",
                },
            )

    def test_invalid_scope(self):

        context = make_context()

        with pytest.raises(
            ValueError,
            match="Invalid parameter scope",
        ):
            SetParameterOperation().execute(
                context,
                {
                    "name": "x",
                    "value": "y",
                    "scope": "Invalid",
                },
            )


# ============================================================
# Rule / RuleEvaluator
# ============================================================


class TestRuleEvaluator:

    def test_rule_does_not_execute_when_condition_fails(self):

        context = make_context()

        context.set_parameter(
            "status",
            "denied",
        )

        condition = Condition(
            SourceType.PARAMETER,
            "status",
            Operator.EQUALS,
            right_type=RightSourceType.USER_VALUE,
            right_value="approved",
        )

        rule = make_runtime_rule(
            make_condition_group(condition),
            ContinueAction(),
        )

        evaluator = RuleEvaluator(
            ConditionGroupEvaluator(
                ConditionEvaluator()
            ),
            OperationExecutor(),
        )

        assert evaluator.evaluate(
            rule,
            context,
        ) is None

    def test_rule_returns_continue_action(self):

        context = make_context()

        context.set_parameter(
            "status",
            "approved",
        )

        condition = Condition(
            SourceType.PARAMETER,
            "status",
            Operator.EQUALS,
            right_type=RightSourceType.USER_VALUE,
            right_value="approved",
        )

        rule = make_runtime_rule(
            make_condition_group(condition),
            ContinueAction(),
        )

        evaluator = RuleEvaluator(
            ConditionGroupEvaluator(
                ConditionEvaluator()
            ),
            OperationExecutor(),
        )

        result = evaluator.evaluate(
            rule,
            context,
        )

        assert isinstance(
            result,
            ContinueAction,
        )

    def test_rule_operation_executes_before_action(self):

        context = make_context()

        context.set_parameter(
            "status",
            "approved",
        )

        condition = Condition(
            SourceType.PARAMETER,
            "status",
            Operator.EQUALS,
            right_type=RightSourceType.USER_VALUE,
            right_value="approved",
        )

        operation = Operation(
            name="set-parameter",
            parameters={
                "name": "result",
                "value": "success",
            },
        )

        rule = make_runtime_rule(
            make_condition_group(condition),
            ContinueAction(),
            operations=[operation],
        )

        evaluator = RuleEvaluator(
            ConditionGroupEvaluator(
                ConditionEvaluator()
            ),
            OperationExecutor(),
        )

        evaluator.evaluate(
            rule,
            context,
        )

        assert context.get_parameter(
            "result"
        ).value == "success"


# ============================================================
# RulesetRegistry
# ============================================================


class TestRulesetRegistry:

    def test_register_and_get(self):

        registry = RulesetRegistry()

        ruleset = RuntimeRuleset(
            "Main",
            [],
        )

        registry.register(ruleset)

        assert registry.exists("Main")
        assert registry.get("Main") is ruleset

    def test_duplicate_ruleset_rejected(self):

        registry = RulesetRegistry()

        registry.register(
            RuntimeRuleset("Main", [])
        )

        with pytest.raises(
            ValueError,
            match="already exists",
        ):
            registry.register(
                RuntimeRuleset("Main", [])
            )

    def test_missing_ruleset_rejected(self):

        registry = RulesetRegistry()

        with pytest.raises(
            ValueError,
            match="Ruleset not found",
        ):
            registry.get("Missing")


# ============================================================
# RulesetExecutor
# ============================================================


class TestRulesetExecutor:

    def build_executor(self, registry):

        evaluator = RuleEvaluator(
            ConditionGroupEvaluator(
                ConditionEvaluator()
            ),
            OperationExecutor(),
        )

        return RulesetExecutor(
            evaluator,
            registry,
        )

    def test_continue_moves_to_next_rule(self):

        context = make_context()

        context.set_parameter(
            "status",
            "approved",
        )

        condition = Condition(
            SourceType.PARAMETER,
            "status",
            Operator.EQUALS,
            right_type=RightSourceType.USER_VALUE,
            right_value="approved",
        )

        rule1 = make_runtime_rule(
            make_condition_group(condition),
            ContinueAction(),
            name="first",
        )

        rule2 = make_runtime_rule(
            make_condition_group(condition),
            ContinueAction(),
            name="second",
        )

        ruleset = RuntimeRuleset(
            "Main",
            [rule1, rule2],
        )

        registry = RulesetRegistry()
        registry.register(ruleset)

        executor = self.build_executor(
            registry
        )

        result = executor.execute(
            ruleset,
            context,
        )

        assert isinstance(
            result,
            ContinueAction,
        )

    def test_jump_to_child_ruleset(self):

        context = make_context()

        context.set_parameter(
            "status",
            "approved",
        )

        parent_condition = Condition(
            SourceType.PARAMETER,
            "status",
            Operator.EQUALS,
            right_type=RightSourceType.USER_VALUE,
            right_value="approved",
        )

        child_condition = Condition(
            SourceType.ARGUMENT,
            "username",
            Operator.EQUALS,
            right_type=RightSourceType.USER_VALUE,
            right_value="simran",
        )

        child_rule = make_runtime_rule(
            make_condition_group(
                child_condition
            ),
            ContinueAction(),
        )

        child = RuntimeRuleset(
            "Child",
            [child_rule],
            arguments={
                "username": type(
                    "ArgumentDefinition",
                    (),
                    {
                        "default_value": None,
                    },
                )(),
            },
        )

        parent_rule = make_runtime_rule(
            make_condition_group(
                parent_condition
            ),
            JumpToRuleset(
                "Child",
                [
                    ArgumentBinding(
                        argument_name="username",
                        source_type=RightSourceType.USER_VALUE,
                        value="simran",
                    )
                ],
            ),
        )

        parent = RuntimeRuleset(
            "Parent",
            [parent_rule],
        )

        registry = RulesetRegistry()

        registry.register(parent)
        registry.register(child)

        executor = self.build_executor(
            registry
        )

        result = executor.execute(
            parent,
            context,
        )

        assert isinstance(
            result,
            ContinueAction,
        )

        assert context.get_ruleset_path() == []

    def test_jump_argument_from_parameter(self):

        context = make_context()

        context.set_parameter(
            "username",
            "simran",
        )

        child_condition = Condition(
            SourceType.ARGUMENT,
            "username",
            Operator.EQUALS,
            right_type=RightSourceType.USER_VALUE,
            right_value="simran",
        )

        child_rule = make_runtime_rule(
            make_condition_group(
                child_condition
            ),
            ContinueAction(),
        )

        child = RuntimeRuleset(
            "Child",
            [child_rule],
        )

        parent_rule = make_runtime_rule(
            ConditionGroup(
                GroupOperator.AND,
                [
                    Condition(
                        SourceType.PARAMETER,
                        "username",
                        Operator.EXISTS,
                    )
                ],
            ),
            JumpToRuleset(
                "Child",
                [
                    ArgumentBinding(
                        argument_name="username",
                        source_type=SourceType.PARAMETER,
                        source_name="username",
                    )
                ],
            ),
        )

        parent = RuntimeRuleset(
            "Parent",
            [parent_rule],
        )

        registry = RulesetRegistry()
        registry.register(parent)
        registry.register(child)

        result = self.build_executor(
            registry
        ).execute(
            parent,
            context,
        )

        assert isinstance(
            result,
            ContinueAction,
        )

    def test_missing_jump_target(self):

        context = make_context()

        context.set_parameter(
            "x",
            "anything",
        )
        condition = Condition(
            SourceType.PARAMETER,
            "x",
            Operator.EXISTS,


        )

        rule = make_runtime_rule(
            make_condition_group(condition),
            JumpToRuleset("Missing"),
        )

        parent = RuntimeRuleset(
            "Parent",
            [rule],
        )

        registry = RulesetRegistry()
        registry.register(parent)

        with pytest.raises(
            ValueError,
            match="Ruleset not found",
        ):
            self.build_executor(
                registry
            ).execute(
                parent,
                context,
            )

    def test_maximum_jump_depth(self):

        context = make_context()

        condition = Condition(
            SourceType.PARAMETER,
            "x",
            Operator.EXISTS,
        )

        rule = make_runtime_rule(
            make_condition_group(condition),
            JumpToRuleset("Loop"),
        )

        ruleset = RuntimeRuleset(
            "Loop",
            [rule],
        )

        registry = RulesetRegistry()
        registry.register(ruleset)

        context.set_parameter(
            "x",
            True,
        )

        with pytest.raises(
            RuntimeError,
            match="Maximum ruleset jump depth exceeded",
        ):
            self.build_executor(
                registry
            ).execute(
                ruleset,
                context,
            )


# ============================================================
# Configuration models
# ============================================================


class TestConfigurationModels:

    def test_add_and_remove_rules(self):

        ruleset = RulesetConfig(
            name="Main"
        )

        rule1 = RuleConfig(
            name="Rule 1"
        )

        rule2 = RuleConfig(
            name="Rule 2"
        )

        ruleset.add_rule(rule1)
        ruleset.add_rule(rule2)

        assert rule1.order == 1
        assert rule2.order == 2

        ruleset.remove_rule(
            rule1.id
        )

        assert len(
            ruleset.rules
        ) == 1

        assert ruleset.rules[0].order == 1

    def test_firewall_configuration(self):

        configuration = FirewallConfiguration()

        ruleset = RulesetConfig(
            name="Main"
        )

        configuration.add_ruleset(
            ruleset
        )

        assert configuration.get_ruleset(
            ruleset.id
        ) is ruleset

        configuration.remove_ruleset(
            ruleset.id
        )

        assert configuration.get_ruleset(
            ruleset.id
        ) is None


# ============================================================
# Serializers
# ============================================================


class TestSerializers:

    def test_condition_round_trip(self):

        serializer = ConditionSerializer()

        condition = ConditionConfig(
            left_type="Parameter",
            left_name="status",
            operator="Equals",
            match_mode="Any",
            right_type="User_Value",
            right_value="approved",
        )

        data = serializer.serialize(
            condition
        )

        restored = serializer.deserialize(
            data
        )

        assert restored.id == condition.id
        assert restored.left_type == condition.left_type
        assert restored.left_name == condition.left_name
        assert restored.operator == condition.operator
        assert restored.right_type == condition.right_type
        assert restored.right_value == condition.right_value

    def test_condition_group_round_trip(self):

        serializer = ConditionSerializer()

        group = ConditionGroupConfig(
            operator="AND"
        )

        group.add_condition(
            ConditionConfig(
                left_type="Parameter",
                left_name="status",
                operator="Equals",
                right_type="User_Value",
                right_value="approved",
            )
        )

        data = serializer.serialize_group(
            group
        )

        restored = serializer.deserialize_group(
            data
        )

        assert restored.id == group.id
        assert restored.operator == "AND"
        assert len(restored.conditions) == 1

    def test_operation_round_trip(self):

        serializer = OperationSerializer()

        operation = OperationConfig(
            name="set-parameter",
            parameters={
                "name": "status",
                "value": "approved",
            },
        )

        data = serializer.serialize(
            operation
        )

        restored = serializer.deserialize(
            data
        )

        assert restored.id == operation.id
        assert restored.name == operation.name
        assert restored.parameters == operation.parameters

    def test_action_round_trip(self):

        serializer = ActionSerializer()

        action = ActionConfig(
            type="JUMP",
            parameters={
                "ruleset_name": "Child",
                "argument_bindings": [
                    ArgumentBinding(
                        argument_name="username",
                        source_type=RightSourceType.USER_VALUE,
                        value="simran",
                    )
                ],
            },
        )

        data = serializer.serialize(
            action
        )

        restored = serializer.deserialize(
            data
        )

        assert restored.id == action.id
        assert restored.type == "JUMP"

        binding = restored.parameters[
            "argument_bindings"
        ][0]

        assert isinstance(
            binding,
            ArgumentBinding,
        )

        assert binding.argument_name == "username"
        assert binding.value == "simran"

    def test_ruleset_round_trip(self):

        ruleset = RulesetConfig(
            name="Main"
        )

        rule = RuleConfig(
            name="Check status"
        )

        rule.condition_group = ConditionGroupConfig(
            operator="AND"
        )

        rule.condition_group.add_condition(
            ConditionConfig(
                left_type="Parameter",
                left_name="status",
                operator="Equals",
                right_type="User_Value",
                right_value="approved",
            )
        )

        rule.operations.append(
            OperationConfig(
                name="set-parameter",
                parameters={
                    "name": "result",
                    "value": "success",
                },
            )
        )

        rule.action = ActionConfig(
            type="CONTINUE"
        )

        ruleset.add_rule(
            rule
        )

        serializer = RulesetSerializer()

        data = serializer.export(
            ruleset
        )

        restored = serializer.import_ruleset(
            data
        )

        assert restored.id == ruleset.id
        assert restored.name == ruleset.name
        assert len(restored.rules) == 1

        restored_rule = restored.rules[0]

        assert restored_rule.id == rule.id
        assert restored_rule.name == rule.name
        assert restored_rule.order == 1
        assert restored_rule.action.type == "CONTINUE"

        assert len(
            restored_rule.operations
        ) == 1

        assert (
            restored_rule.operations[0].name
            == "set-parameter"
        )

    def test_full_configuration_round_trip(self):

        configuration = FirewallConfiguration()

        ruleset = RulesetConfig(
            name="Main"
        )

        rule = RuleConfig(
            name="Rule 1"
        )

        rule.condition_group = ConditionGroupConfig(
            operator="AND"
        )

        rule.condition_group.add_condition(
            ConditionConfig(
                left_type="Parameter",
                left_name="status",
                operator="Equals",
                right_type="User_Value",
                right_value="approved",
            )
        )

        rule.operations.append(
            OperationConfig(
                name="set-parameter",
                parameters={
                    "name": "result",
                    "value": "success",
                },
            )
        )

        rule.action = ActionConfig(
            type="CONTINUE"
        )

        ruleset.add_rule(rule)
        configuration.add_ruleset(ruleset)

        serializer = FirewallConfigurationSerializer()
        deserializer = FirewallConfigurationDeserializer()

        data = serializer.export(
            configuration
        )

        restored = deserializer.deserialize(
            data
        )

        assert len(
            restored.rulesets
        ) == 1

        restored_ruleset = restored.rulesets[0]

        assert restored_ruleset.id == ruleset.id
        assert restored_ruleset.name == "Main"

        assert len(
            restored_ruleset.rules
        ) == 1

        restored_rule = restored_ruleset.rules[0]

        assert restored_rule.id == rule.id
        assert restored_rule.name == "Rule 1"
        assert restored_rule.order == 1

        assert (
            restored_rule.condition_group.operator
            == "AND"
        )

        assert len(
            restored_rule.condition_group.conditions
        ) == 1

        assert len(
            restored_rule.operations
        ) == 1

        assert (
            restored_rule.operations[0].parameters[
                "value"
            ]
            == "success"
        )

        assert (
            restored_rule.action.type
            == "CONTINUE"
        )


# ============================================================
# Draft lifecycle
# ============================================================


class TestDraftLifecycle:

    def setup_services(self):

        repository = DraftRepository()

        version_service = FakeVersionService()

        initial_configuration = FirewallConfiguration()

        version = FakeVersion(
            initial_configuration
        )

        version_service.add_version(
            version
        )

        service = DraftService(
            repository,
            version_service,
        )

        return (
            service,
            repository,
            version_service,
            version,
        )

    def test_create_draft(self):

        (
            service,
            repository,
            version_service,
            version,
        ) = self.setup_services()

        configuration = FirewallConfiguration()

        draft = service.create_draft(
            version.id,
            configuration,
        )

        assert draft.base_version_id == version.id
        assert repository.get(
            draft.id
        ) is draft

    def test_draft_configuration_is_deep_copy(self):

        (
            service,
            repository,
            version_service,
            version,
        ) = self.setup_services()

        configuration = FirewallConfiguration()

        ruleset = RulesetConfig(
            name="Main"
        )

        configuration.add_ruleset(
            ruleset
        )

        draft = service.create_draft(
            version.id,
            configuration,
        )

        configuration.rulesets[0].name = "Changed"

        assert (
            draft.configuration.rulesets[0].name
            == "Main"
        )

    def test_update_configuration(self):

        (
            service,
            repository,
            version_service,
            version,
        ) = self.setup_services()

        draft = service.create_draft(
            version.id,
            FirewallConfiguration(),
        )

        new_configuration = FirewallConfiguration()

        new_configuration.add_ruleset(
            RulesetConfig(
                name="Updated"
            )
        )

        updated = service.update_configuration(
            draft.id,
            new_configuration,
        )

        assert (
            updated.configuration.rulesets[0].name
            == "Updated"
        )

    def test_clear_changes(self):

        (
            service,
            repository,
            version_service,
            version,
        ) = self.setup_services()

        draft = service.create_draft(
            version.id,
            FirewallConfiguration(),
        )

        assert service.clear_changes(
            draft.id
        ) is True

        assert repository.get(
            draft.id
        ) is None

    def test_commit_creates_version(self):

        (
            service,
            repository,
            version_service,
            version,
        ) = self.setup_services()

        configuration = FirewallConfiguration()

        configuration.add_ruleset(
            RulesetConfig(
                name="Committed"
            )
        )

        draft = service.create_draft(
            version.id,
            configuration,
        )

        committed_version = service.commit(
            draft.id,
            name="Committed Configuration",
        )

        assert committed_version is not None

        assert (
            committed_version.configuration.rulesets[0].name
            == "Committed"
        )

        assert repository.get(
            draft.id
        ) is None

    def test_create_draft_requires_existing_version(self):

        (
            service,
            repository,
            version_service,
            version,
        ) = self.setup_services()

        with pytest.raises(
            ValueError,
            match="Version not found",
        ):
            service.create_draft(
                uuid4(),
                FirewallConfiguration(),
            )

    def test_missing_draft_rejected(self):

        (
            service,
            repository,
            version_service,
            version,
        ) = self.setup_services()

        with pytest.raises(
            ValueError,
            match="Draft not found",
        ):
            service.commit(
                uuid4(),
                name="Should Not Be Created",
            )
    

    def test_commit_preserves_draft_if_version_creation_fails(self):

        (
            service,
            repository,
            version_service,
            version,
        ) = self.setup_services()

        draft = service.create_draft(
            version.id,
            FirewallConfiguration(),
        )

        def fail_create_version(**kwargs):
            raise RuntimeError("Version storage failed")

        version_service.create_version = fail_create_version

        with pytest.raises(
            RuntimeError,
            match="Version storage failed",
        ):
            service.commit(
                draft.id,
                name="Failed Commit",
            )

        assert repository.get(draft.id) is draft


    def test_committed_configuration_is_independent(self):

        (
            service,
            repository,
            version_service,
            version,
        ) = self.setup_services()

        configuration = FirewallConfiguration()

        configuration.add_ruleset(
            RulesetConfig(name="Original")
        )

        draft = service.create_draft(
            version.id,
            configuration,
        )

        committed = service.commit(
            draft.id,
            name="Release 1",
        )

        # The committed version must not share mutable
        # configuration state with the original input.
        configuration.rulesets[0].name = "Changed Input"

        assert (
            committed.configuration.rulesets[0].name
            == "Original"
        )

        assert committed.name == "Release 1"
        assert committed.parent_version_id == version.id
        assert repository.get(draft.id) is None


# ============================================================
# Complete end-to-end flow
# ============================================================


class TestEndToEnd:

    def test_parameter_condition_operation_and_action_flow(self):

        context = ExecutionContext()

        context.set_parameter(
            "status",
            "approved",
        )

        condition = Condition(
            left_type=SourceType.PARAMETER,
            left_name="status",
            operator=Operator.EQUALS,
            right_type=RightSourceType.USER_VALUE,
            right_value="approved",
        )

        operation = Operation(
            name="set-parameter",
            parameters={
                "name": "decision",
                "value": "allow",
            },
        )

        rule = make_runtime_rule(
            condition_group=ConditionGroup(
                GroupOperator.AND,
                [condition],
            ),
            operations=[operation],
            action=ContinueAction(),
        )

        ruleset = RuntimeRuleset(
            "Main",
            [rule],
        )

        registry = RulesetRegistry()
        registry.register(
            ruleset
        )

        evaluator = RuleEvaluator(
            ConditionGroupEvaluator(
                ConditionEvaluator()
            ),
            OperationExecutor(),
        )

        executor = RulesetExecutor(
            evaluator,
            registry,
        )

        result = executor.execute(
            ruleset,
            context,
        )

        assert isinstance(
            result,
            ContinueAction,
        )

        assert context.get_parameter(
            "decision"
        ).value == "allow"

        assert context.get_ruleset_path() == []

# ============================================================
# Ruleset Argument Edge Cases
# ============================================================


class TestRulesetArgumentEdgeCases:

    def build_executor(self, registry):

        evaluator = RuleEvaluator(
            ConditionGroupEvaluator(
                ConditionEvaluator()
            ),
            OperationExecutor(),
        )

        return RulesetExecutor(
            evaluator,
            registry,
        )

    def test_missing_required_argument(self):

        ruleset = Ruleset("Test")

        ruleset.add_argument(
            Argument(
                name="username",
                datatype=DataType.STRING,
                collection_type=CollectionType.SCALAR,
            )
        )

        with pytest.raises(
            ValueError,
            match="Missing argument: username",
        ):
            ruleset.validate_arguments()

    def test_unknown_argument_rejected(self):

        ruleset = Ruleset("Test")

        ruleset.add_argument(
            Argument(
                name="username",
                datatype=DataType.STRING,
                collection_type=CollectionType.SCALAR,
            )
        )

        with pytest.raises(
            ValueError,
            match="Unknown argument: password",
        ):
            ruleset.validate_arguments({
                "password": "secret",
            })

    def test_default_argument_is_used(self):

        ruleset = Ruleset("Test")

        ruleset.add_argument(
            Argument(
                name="username",
                datatype=DataType.STRING,
                collection_type=CollectionType.SCALAR,
                default_value="guest",
            )
        )

        result = ruleset.validate_arguments()

        assert result == {
            "username": "guest",
        }

    def test_explicit_argument_overrides_default(self):

        ruleset = Ruleset("Test")

        ruleset.add_argument(
            Argument(
                name="username",
                datatype=DataType.STRING,
                collection_type=CollectionType.SCALAR,
                default_value="guest",
            )
        )

        result = ruleset.validate_arguments({
            "username": "simran",
        })

        assert result == {
            "username": "simran",
        }

    def test_string_argument_rejects_integer(self):

        ruleset = Ruleset("Test")

        ruleset.add_argument(
            Argument(
                name="username",
                datatype=DataType.STRING,
                collection_type=CollectionType.SCALAR,
            )
        )

        with pytest.raises(
            ValueError,
            match="Argument username expects String",
        ):
            ruleset.validate_arguments({
                "username": 123,
            })

    def test_integer_argument_rejects_string(self):

        ruleset = Ruleset("Test")

        ruleset.add_argument(
            Argument(
                name="count",
                datatype=DataType.INTEGER,
                collection_type=CollectionType.SCALAR,
            )
        )

        with pytest.raises(
            ValueError,
            match="Argument count expects Integer",
        ):
            ruleset.validate_arguments({
                "count": "10",
            })

    def test_integer_argument_rejects_boolean(self):

        ruleset = Ruleset("Test")

        ruleset.add_argument(
            Argument(
                name="count",
                datatype=DataType.INTEGER,
                collection_type=CollectionType.SCALAR,
            )
        )

        with pytest.raises(
            ValueError,
            match="Argument count expects Integer",
        ):
            ruleset.validate_arguments({
                "count": True,
            })

    def test_boolean_argument_rejects_string(self):

        ruleset = Ruleset("Test")

        ruleset.add_argument(
            Argument(
                name="enabled",
                datatype=DataType.BOOLEAN,
                collection_type=CollectionType.SCALAR,
            )
        )

        with pytest.raises(
            ValueError,
            match="Argument enabled expects Boolean",
        ):
            ruleset.validate_arguments({
                "enabled": "true",
            })

    def test_collection_argument_accepts_list(self):

        ruleset = Ruleset("Test")

        ruleset.add_argument(
            Argument(
                name="roles",
                datatype=DataType.STRING,
                collection_type=CollectionType.SET,
            )
        )

        result = ruleset.validate_arguments({
            "roles": [
                "admin",
                "user",
            ],
        })

        assert result == {
            "roles": [
                "admin",
                "user",
            ],
        }

    def test_collection_argument_rejects_scalar(self):

        ruleset = Ruleset("Test")

        ruleset.add_argument(
            Argument(
                name="roles",
                datatype=DataType.STRING,
                collection_type=CollectionType.SET,
            )
        )

        with pytest.raises(
            ValueError,
            match="Argument roles expects collection value",
        ):
            ruleset.validate_arguments({
                "roles": "admin",
            })

    def test_collection_argument_validates_each_item(self):

        ruleset = Ruleset("Test")

        ruleset.add_argument(
            Argument(
                name="numbers",
                datatype=DataType.INTEGER,
                collection_type=CollectionType.SET,
            )
        )

        with pytest.raises(
            ValueError,
            match="Argument numbers expects Integer",
        ):
            ruleset.validate_arguments({
                "numbers": [
                    1,
                    2,
                    "three",
                ],
            })

    def test_child_arguments_are_isolated_from_parent(self):

        parent = Ruleset("Parent")

        parent.add_argument(
            Argument(
                name="username",
                datatype=DataType.STRING,
                collection_type=CollectionType.SCALAR,
            )
        )

        child = Ruleset("Child")

        child.add_argument(
            Argument(
                name="username",
                datatype=DataType.STRING,
                collection_type=CollectionType.SCALAR,
            )
        )

        parent_arguments = parent.validate_arguments({
            "username": "parent-user",
        })

        child_arguments = child.validate_arguments({
            "username": "child-user",
        })

        assert parent_arguments == {
            "username": "parent-user",
        }

        assert child_arguments == {
            "username": "child-user",
        }

        assert parent_arguments != child_arguments

    def test_child_arguments_do_not_modify_parent_arguments(self):

        parent = Ruleset("Parent")

        parent.add_argument(
            Argument(
                name="username",
                datatype=DataType.STRING,
                collection_type=CollectionType.SCALAR,
            )
        )

        child = Ruleset("Child")

        child.add_argument(
            Argument(
                name="username",
                datatype=DataType.STRING,
                collection_type=CollectionType.SCALAR,
            )
        )

        parent_arguments = parent.validate_arguments({
            "username": "parent-user",
        })

        child_arguments = child.validate_arguments({
            "username": "child-user",
        })

        child_arguments["username"] = "changed-child-user"

        assert parent_arguments == {
            "username": "parent-user",
        }

        assert child_arguments == {
            "username": "changed-child-user",
        }

    def test_child_missing_required_argument_rejected(self):

        child = Ruleset("Child")

        child.add_argument(
            Argument(
                name="username",
                datatype=DataType.STRING,
                collection_type=CollectionType.SCALAR,
            )
        )

        with pytest.raises(
            ValueError,
            match="Missing argument: username",
        ):
            child.validate_arguments({})

    def test_child_default_argument_used_during_jump(self):

        child = Ruleset("Child")

        child.add_argument(
            Argument(
                name="username",
                datatype=DataType.STRING,
                collection_type=CollectionType.SCALAR,
                default_value="guest",
            )
        )

        assert child.validate_arguments({}) == {
            "username": "guest",
        }

    def test_child_explicit_argument_overrides_default(self):

        child = Ruleset("Child")

        child.add_argument(
            Argument(
                name="username",
                datatype=DataType.STRING,
                collection_type=CollectionType.SCALAR,
                default_value="guest",
            )
        )

        arguments = child.validate_arguments({
            "username": "alice",
        })

        assert arguments == {
            "username": "alice",
        }

    def test_jump_explicit_argument_reaches_child(self):

        context = make_context()

        child_condition = Condition(
            SourceType.ARGUMENT,
            "username",
            Operator.EQUALS,
            right_type=RightSourceType.USER_VALUE,
            right_value="alice",
        )

        child_rule = make_runtime_rule(
            make_condition_group(
                child_condition
            ),
            ContinueAction(),
        )

        child = RuntimeRuleset(
            "Child",
            [child_rule],
        )

        parent_rule = make_runtime_rule(
            ConditionGroup(
                GroupOperator.AND,
                [
                    Condition(
                        SourceType.PARAMETER,
                        "run_child",
                        Operator.EXISTS,
                    )
                ],
            ),
            JumpToRuleset(
                "Child",
                [
                    ArgumentBinding(
                        argument_name="username",
                        source_type=RightSourceType.USER_VALUE,
                        value="alice",
                    )
                ],
            ),
        )

        parent = RuntimeRuleset(
            "Parent",
            [parent_rule],
        )

        registry = RulesetRegistry()

        registry.register(parent)
        registry.register(child)

        context.set_parameter(
            "run_child",
            True,
        )

        result = self.build_executor(
            registry
        ).execute(
            parent,
            context,
        )

        assert isinstance(
            result,
            ContinueAction,
        )

        assert context.get_ruleset_path() == []
    def test_ruleset_without_arguments_accepts_none(self):

        ruleset = Ruleset("Main")

        assert ruleset.validate_arguments() == {}


    def test_ruleset_without_arguments_accepts_empty_dict(self):

        ruleset = Ruleset("Main")

        assert ruleset.validate_arguments({}) == {}


    def test_ruleset_without_arguments_rejects_arguments(self):

        ruleset = Ruleset("Main")

        with pytest.raises(
            ValueError,
            match="Ruleset Main does not accept arguments",
        ):
            ruleset.validate_arguments({
                "username": "simran",
            })


    def test_ruleset_with_required_argument_requires_argument(self):

        ruleset = Ruleset("Child")

        ruleset.add_argument(
            Argument(
                name="username",
                datatype=DataType.STRING,
                collection_type=CollectionType.SCALAR,
            )
        )

        with pytest.raises(
            ValueError,
            match="Missing argument: username",
        ):
            ruleset.validate_arguments()


    def test_ruleset_with_default_argument_can_omit_argument(self):

        ruleset = Ruleset("Child")

        ruleset.add_argument(
            Argument(
                name="username",
                datatype=DataType.STRING,
                collection_type=CollectionType.SCALAR,
                default_value="guest",
            )
        )

        assert ruleset.validate_arguments() == {
            "username": "guest",
        }
    def test_jump_to_child_without_required_argument_fails(self):

        context = make_context()

        child = RuntimeRuleset(
            "Child",
            [],
            arguments={
                "username": type(
                    "ArgumentDefinition",
                    (),
                    {
                        "default_value": None,
                    },
                )(),
            },
        )

        parent_rule = make_runtime_rule(
            ConditionGroup(
                GroupOperator.AND,
                [
                    Condition(
                        SourceType.PARAMETER,
                        "run_child",
                        Operator.EXISTS,
                    )
                ],
            ),
            JumpToRuleset("Child"),
        )

        parent = RuntimeRuleset(
            "Parent",
            [parent_rule],
        )

        registry = RulesetRegistry()

        registry.register(parent)
        registry.register(child)

        context.set_parameter(
            "run_child",
            True,
        )

        with pytest.raises(
            ValueError,
            match="Missing argument: username",
        ):
            self.build_executor(
                registry
            ).execute(
                parent,
                context,
            )

    def test_jump_to_child_uses_default_argument(self):

        context = make_context()

        child_condition = Condition(
            SourceType.ARGUMENT,
            "username",
            Operator.EQUALS,
            right_type=RightSourceType.USER_VALUE,
            right_value="guest",
        )

        child_rule = make_runtime_rule(
            make_condition_group(
                child_condition
            ),
            ContinueAction(),
        )

        child = RuntimeRuleset(
            "Child",
            [child_rule],
            arguments={
                "username": type(
                    "ArgumentDefinition",
                    (),
                    {
                        "default_value": "guest",
                    },
                )(),
            },
        )

        parent_rule = make_runtime_rule(
            ConditionGroup(
                GroupOperator.AND,
                [
                    Condition(
                        SourceType.PARAMETER,
                        "run_child",
                        Operator.EXISTS,
                    )
                ],
            ),
            JumpToRuleset("Child"),
        )

        parent = RuntimeRuleset(
            "Parent",
            [parent_rule],
        )

        registry = RulesetRegistry()

        registry.register(parent)
        registry.register(child)

        context.set_parameter(
            "run_child",
            True,
        )

        result = self.build_executor(
            registry
        ).execute(
            parent,
            context,
        )

        assert isinstance(
            result,
            ContinueAction,
        )

        assert context.get_ruleset_path() == []
    def test_ruleset_arguments_round_trip(self):

        ruleset = RulesetConfig(
            name="Security_Profile"
        )

        ruleset.add_argument(
            Argument(
                name="profile",
                datatype=DataType.STRING,
                collection_type=CollectionType.SCALAR,
                default_value="standard",
            )
        )

        serializer = RulesetSerializer()

        exported = serializer.export(
            ruleset
        )

        imported = serializer.import_ruleset(
            exported
        )

        assert imported.name == "Security_Profile"

        assert len(
            imported.arguments
        ) == 1

        argument = imported.arguments[0]

        assert argument.name == "profile"

        assert argument.datatype == DataType.STRING

        assert argument.collection_type == CollectionType.SCALAR

        assert argument.default_value == "standard"

# ============================================================
# Rule operations
# ============================================================


class TestRuleOperations:

    def setup_services(self):

        repository = DraftRepository()

        version_service = FakeVersionService()

        initial_configuration = FirewallConfiguration()

        version = FakeVersion(
            initial_configuration
        )

        version_service.add_version(
            version
        )

        draft_service = DraftService(
            repository,
            version_service
        )

        draft = draft_service.create_draft(
            version.id,
            initial_configuration
        )

        ruleset_service = RulesetService(
            draft_service
        )

        ruleset = ruleset_service.create_ruleset(
            draft.id,
            "Main"
        )

        rule = ruleset_service.add_rule(
            draft.id,
            ruleset.id,
            "Process Request"
        )

        rule_service = RuleService(
            draft_service
        )

        return (
            draft_service,
            rule_service,
            draft,
            ruleset,
            rule
        )


    def test_create_operation(self):

        (
            draft_service,
            rule_service,
            draft,
            ruleset,
            rule
        ) = self.setup_services()

        operation = rule_service.create_operation(

            draft.id,

            ruleset.id,

            rule.id,

            "set-parameter",

            {
                "name": "risk",
                "value": 10,
                "scope": "REQUEST"
            }

        )

        assert isinstance(
            operation,
            OperationConfig
        )

        assert operation.name == "set-parameter"

        assert operation.parameters == {
            "name": "risk",
            "value": 10,
            "scope": "REQUEST"
        }

        assert len(
            rule.operations
        ) == 1

        assert rule.operations[0] == operation


    def test_created_operation_has_id(self):

        (
            draft_service,
            rule_service,
            draft,
            ruleset,
            rule
        ) = self.setup_services()

        operation = rule_service.create_operation(

            draft.id,

            ruleset.id,

            rule.id,

            "set-parameter"

        )

        assert operation.id is not None


    def test_create_operation_without_parameters_uses_empty_dict(self):

        (
            draft_service,
            rule_service,
            draft,
            ruleset,
            rule
        ) = self.setup_services()

        operation = rule_service.create_operation(

            draft.id,

            ruleset.id,

            rule.id,

            "set-parameter"

        )

        assert operation.parameters == {}


    def test_create_operation_requires_name(self):

        (
            draft_service,
            rule_service,
            draft,
            ruleset,
            rule
        ) = self.setup_services()

        with pytest.raises(
            ValueError,
            match="Operation name is required"
        ):

            rule_service.create_operation(

                draft.id,

                ruleset.id,

                rule.id,

                ""

            )


    def test_create_operation_requires_existing_rule(self):

        (
            draft_service,
            rule_service,
            draft,
            ruleset,
            rule
        ) = self.setup_services()

        with pytest.raises(
            ValueError,
            match="Rule not found"
        ):

            rule_service.create_operation(

                draft.id,

                ruleset.id,

                "00000000-0000-0000-0000-000000000000",

                "set-parameter"

            )


    def test_multiple_operations_preserve_order(self):

        (
            draft_service,
            rule_service,
            draft,
            ruleset,
            rule
        ) = self.setup_services()

        first = rule_service.create_operation(

            draft.id,
            ruleset.id,
            rule.id,
            "set-parameter",
            {
                "name": "first",
                "value": 1
            }

        )

        second = rule_service.create_operation(

            draft.id,
            ruleset.id,
            rule.id,
            "set-parameter",
            {
                "name": "second",
                "value": 2
            }

        )

        assert len(
            rule.operations
        ) == 2

        assert rule.operations[0].id == first.id

        assert rule.operations[1].id == second.id


    def test_get_operation(self):

        (
            draft_service,
            rule_service,
            draft,
            ruleset,
            rule
        ) = self.setup_services()

        operation = rule_service.create_operation(

            draft.id,
            ruleset.id,
            rule.id,
            "set-parameter",
            {
                "name": "risk",
                "value": 10
            }

        )

        restored = rule_service.get_operation(

            draft.id,

            ruleset.id,

            rule.id,

            operation.id

        )

        assert restored is operation


    def test_get_missing_operation_returns_none(self):

        (
            draft_service,
            rule_service,
            draft,
            ruleset,
            rule
        ) = self.setup_services()

        result = rule_service.get_operation(

            draft.id,

            ruleset.id,

            rule.id,

            "00000000-0000-0000-0000-000000000000"

        )

        assert result is None


    def test_remove_operation(self):

        (
            draft_service,
            rule_service,
            draft,
            ruleset,
            rule
        ) = self.setup_services()

        operation = rule_service.create_operation(

            draft.id,

            ruleset.id,

            rule.id,

            "set-parameter",

            {
                "name": "risk",
                "value": 10
            }

        )

        removed = rule_service.remove_operation(

            draft.id,

            ruleset.id,

            rule.id,

            0

        )

        assert removed is operation

        assert rule.operations == []


    def test_remove_operation_invalid_index_fails(self):

        (
            draft_service,
            rule_service,
            draft,
            ruleset,
            rule
        ) = self.setup_services()

        with pytest.raises(
            IndexError,
            match="Operation index out of range"
        ):

            rule_service.remove_operation(

                draft.id,

                ruleset.id,

                rule.id,

                0

            )
    