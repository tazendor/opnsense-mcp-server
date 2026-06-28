from __future__ import annotations

import re

from opnsense_mcp.errors import ToolError

_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)
_ALIAS_NAME_RE = re.compile(r"^[A-Za-z0-9_]{1,32}$")


def validate_uuid(uuid: str) -> str:
    if not _UUID_RE.match(uuid):
        raise ToolError(f"Invalid UUID format: {uuid!r}")
    return uuid


def validate_alias_name(name: str) -> str:
    if not _ALIAS_NAME_RE.match(name):
        raise ToolError(
            f"Invalid alias name {name!r}: "
            "use 1-32 alphanumeric characters or underscores"
        )
    return name
