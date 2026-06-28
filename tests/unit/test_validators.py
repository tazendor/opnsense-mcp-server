"""Tests for input validation helpers."""

import pytest

from opnsense_mcp._validators import validate_alias_name, validate_uuid
from opnsense_mcp.errors import ToolError


class TestValidateUuid:
    def test_accepts_valid_lowercase_uuid(self) -> None:
        uuid = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        assert validate_uuid(uuid) == uuid

    def test_accepts_valid_uppercase_uuid(self) -> None:
        uuid = "AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA"
        assert validate_uuid(uuid) == uuid

    def test_accepts_mixed_case_uuid(self) -> None:
        uuid = "Aa1Bb2Cc-3Dd4-5Ee6-Ff78-9Aa0Bb1Cc2Dd"
        assert validate_uuid(uuid) == uuid

    def test_rejects_plain_string(self) -> None:
        with pytest.raises(ToolError, match="Invalid UUID"):
            validate_uuid("not-a-uuid")

    def test_rejects_path_traversal(self) -> None:
        with pytest.raises(ToolError, match="Invalid UUID"):
            validate_uuid("../../etc/passwd")

    def test_rejects_uuid_with_extra_chars(self) -> None:
        with pytest.raises(ToolError, match="Invalid UUID"):
            validate_uuid("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa/extra")

    def test_rejects_empty_string(self) -> None:
        with pytest.raises(ToolError, match="Invalid UUID"):
            validate_uuid("")

    def test_rejects_uuid_missing_segment(self) -> None:
        with pytest.raises(ToolError, match="Invalid UUID"):
            validate_uuid("aaaaaaaa-aaaa-aaaa-aaaa")


class TestValidateAliasName:
    def test_accepts_simple_alphanumeric_name(self) -> None:
        assert validate_alias_name("MyAlias") == "MyAlias"

    def test_accepts_name_with_underscore(self) -> None:
        assert validate_alias_name("my_alias_1") == "my_alias_1"

    def test_accepts_single_char_name(self) -> None:
        assert validate_alias_name("A") == "A"

    def test_accepts_32_char_name(self) -> None:
        name = "A" * 32
        assert validate_alias_name(name) == name

    def test_rejects_name_with_slash(self) -> None:
        with pytest.raises(ToolError, match="Invalid alias name"):
            validate_alias_name("foo/bar")

    def test_rejects_path_traversal(self) -> None:
        with pytest.raises(ToolError, match="Invalid alias name"):
            validate_alias_name("../../etc/passwd")

    def test_rejects_name_with_dot(self) -> None:
        with pytest.raises(ToolError, match="Invalid alias name"):
            validate_alias_name("foo.bar")

    def test_rejects_empty_name(self) -> None:
        with pytest.raises(ToolError, match="Invalid alias name"):
            validate_alias_name("")

    def test_rejects_name_over_32_chars(self) -> None:
        with pytest.raises(ToolError, match="Invalid alias name"):
            validate_alias_name("A" * 33)

    def test_rejects_name_with_newline(self) -> None:
        with pytest.raises(ToolError, match="Invalid alias name"):
            validate_alias_name("foo\nbar")
