
from parameters import (
    ParameterStore,
    Parameter,
    ParameterScope
)

from arguments import ArgumentStore

from lists.list_manager import ListManager


class ExecutionContext:

    def __init__(self, list_manager=None):
        self.parameters = ParameterStore()
        self.arguments = ArgumentStore()
        self.ruleset_path = []

        # Incoming message metadata supplied by the
        # message ingress layer or simulation script.
        self.metadata = {}

        self.list_manager = (
            list_manager
            if list_manager is not None
            else ListManager()
        )

    # -------------------------
    # Message Metadata
    # -------------------------

    def set_metadata(self, metadata):
        if not isinstance(metadata, dict):
            raise ValueError(
                "Message metadata must be a dictionary"
            )

        self.metadata = dict(metadata)

    def get_metadata(self, name, default=None):
        return self.metadata.get(name, default)

    # -------------------------
    # Parameter Management
    # -------------------------

    def set_parameter(
        self,
        name,
        value,
        datatype="String",
        scope=ParameterScope.LOCAL
    ):
        parameter = Parameter(
            name=name,
            value=value,
            datatype=datatype,
            scope=scope
        )

        self.parameters.set(parameter)

    def get_parameter(self, name):
        return self.parameters.get_parameter(name)

    # -------------------------
    # Argument Management
    # -------------------------

    def set_argument(self, name, value):
        self.arguments.set(name, value)

    def get_argument(self, name):
        return self.arguments.get(name)

    # -------------------------
    # Ruleset Execution Path
    # -------------------------

    def enter_ruleset(self, ruleset_name):
        self.ruleset_path.append(ruleset_name)

    def exit_ruleset(self):
        if self.ruleset_path:
            return self.ruleset_path.pop()

        return None

    def get_ruleset_path(self):
        return list(self.ruleset_path)