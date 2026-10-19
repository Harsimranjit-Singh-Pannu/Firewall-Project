import pytest

from lists.list_column import ListColumn
from lists.list_definition import ListDefinition
from lists.list_manager import ListManager
from lists.list_repository import ListRepository
from storage.json_storage import JsonStorage



@pytest.fixture
def manager(tmp_path):
    storage = JsonStorage(
        folder=tmp_path / "lists"
    )

    repository = ListRepository(
        storage=storage
    )

    manager = ListManager(
        repository=repository
    )

    columns = [
        ListColumn(
            name="sender",
            datatype="String",
            unique=True,
            optional=False,
        ),
        ListColumn(
            name="regex_pattern",
            datatype="Regex",
            optional=False,
        ),
        ListColumn(
            name="action",
            datatype="String",
            optional=False,
        ),
    ]

    manager.create_list(
        name="sender_rules",
        columns=columns,
        rows=[
            {
                "sender": "12344",
                "regex_pattern": "^SPAM.*",
                "action": "BLOCK",
            },
            {
                "sender": "56789",
                "regex_pattern": "^HELLO.*",
                "action": "ALLOW",
            },
        ],
    )

    return manager


def test_create_list_has_permanent_alias(manager):
    definition = manager.get_list("LMS_1_sender_rules")

    assert definition.alias == "LMS_1_sender_rules"
    assert len(definition.columns) == 3


def test_duplicate_column_names_are_rejected():
    columns = [
        ListColumn("sender", "String"),
        ListColumn("sender", "Integer"),
    ]

    with pytest.raises(ValueError):
        ListDefinition(
            list_number=1,
            name="sender_rules",
            columns=columns,
        )


def test_duplicate_unique_values_are_rejected():
    manager = ListManager()

    columns = [
        ListColumn(
            "sender",
            "String",
            unique=True,
        ),
    ]

    with pytest.raises(ValueError):
        manager.create_list(
            name="duplicate_senders",
            columns=columns,
            rows=[
                {"sender": "12344"},
                {"sender": "12344"},
            ],
        )


def test_required_columns_are_enforced():
    manager = ListManager()

    columns = [
        ListColumn(
            "sender",
            "String",
            optional=False,
        ),
    ]

    with pytest.raises(ValueError):
        manager.create_list(
            name="missing_sender",
            columns=columns,
            rows=[{}],
        )


def test_get_rows_returns_independent_copies(manager):
    rows = manager.get_rows("LMS_1_sender_rules")
    rows[0]["action"] = "ALLOW"

    stored_rows = manager.get_rows("LMS_1_sender_rules")

    assert stored_rows[0]["action"] == "BLOCK"


def test_column_metadata_is_immutable(manager):
    column = manager.get_list(
        "LMS_1_sender_rules"
    ).get_column("sender")

    with pytest.raises(AttributeError):
        column.datatype = "Integer"

    with pytest.raises(AttributeError):
        column.unique = False


def test_list_definition_schema_is_immutable(manager):
    definition = manager.get_list(
        "LMS_1_sender_rules"
    )

    with pytest.raises(AttributeError):
        definition.name = "renamed_list"

    with pytest.raises(AttributeError):
        definition.columns = ()


def test_update_cell(manager):
    manager.update_cell(
        "LMS_1_sender_rules",
        0,
        "action",
        "ALLOW",
    )

    rows = manager.get_rows("LMS_1_sender_rules")

    assert rows[0]["action"] == "ALLOW"


def test_update_unique_value_rejects_duplicates(manager):
    with pytest.raises(ValueError):
        manager.update_cell(
            "LMS_1_sender_rules",
            0,
            "sender",
            "56789",
        )

    rows = manager.get_rows("LMS_1_sender_rules")
    assert rows[0]["sender"] == "12344"


def test_add_row(manager):
    manager.add_row(
        "LMS_1_sender_rules",
        {
            "sender": "99999",
            "regex_pattern": "^TEST.*",
            "action": "BLOCK",
        },
    )

    rows = manager.get_rows("LMS_1_sender_rules")

    assert len(rows) == 3
    assert rows[2]["sender"] == "99999"


def test_add_invalid_row_is_rejected(manager):
    with pytest.raises(ValueError):
        manager.add_row(
            "LMS_1_sender_rules",
            {
                "sender": "12344",
                "regex_pattern": "^DUPLICATE.*",
                "action": "BLOCK",
            },
        )

    assert len(manager.get_rows("LMS_1_sender_rules")) == 2


def test_delete_row(manager):
    manager.delete_row(
        "LMS_1_sender_rules",
        0,
    )

    rows = manager.get_rows("LMS_1_sender_rules")

    assert len(rows) == 1
    assert rows[0]["sender"] == "56789"


def test_invalid_row_index_is_rejected(manager):
    with pytest.raises(IndexError):
        manager.delete_row(
            "LMS_1_sender_rules",
            99,
        )


def test_integer_column_rejects_boolean():
    manager = ListManager()

    with pytest.raises(ValueError):
        manager.create_list(
            name="integer_test",
            columns=[
                ListColumn("count", "Integer"),
            ],
            rows=[
                {"count": True},
            ],
        )


def test_regex_column_rejects_invalid_pattern():
    manager = ListManager()

    with pytest.raises(ValueError):
        manager.create_list(
            name="regex_test",
            columns=[
                ListColumn("pattern", "Regex"),
            ],
            rows=[
                {"pattern": "["},
            ],
        )


def test_ip_address_column_rejects_invalid_address():
    manager = ListManager()

    with pytest.raises(ValueError):
        manager.create_list(
            name="ip_test",
            columns=[
                ListColumn("address", "IPAddress"),
            ],
            rows=[
                {"address": "999.999.999.999"},
            ],
        )


def test_boolean_column_accepts_boolean():
    manager = ListManager()

    manager.create_list(
        name="boolean_test",
        columns=[
            ListColumn("enabled", "Boolean"),
        ],
        rows=[
            {"enabled": True},
            {"enabled": False},
        ],
    )

    assert len(manager.get_rows("LMS_1_boolean_test")) == 2