# Data Model: Complete OPNsense API Coverage (Read-Write)

## Overview

Same shape as 001: this server is a typed proxy with no owned persistent state. 002 adds
exactly one piece of *process-local, non-persistent* state — the pending-confirmation
store — plus the domain types for the new subsystems. All domain types mirror OPNsense's
documented JSON response structures (FR-003); no fields are invented, renamed, or removed,
except that private-key fields are redacted on the way out (FR-017).

---

## Pending Operation / Confirmation (new — supports FR-007–FR-011)

```python
from __future__ import annotations

import secrets
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class PendingOperation:
    token: str
    tool_name: str
    arguments: dict[str, Any]
    description: str
    expires_at: float  # time.monotonic() deadline


class PendingOperationStore:
    def __init__(self, ttl_seconds: float = 120.0) -> None:
        self._ttl = ttl_seconds
        self._pending: dict[str, PendingOperation] = {}

    def create(self, tool_name: str, arguments: dict[str, Any], description: str) -> PendingOperation:
        self._evict_expired()
        token = secrets.token_urlsafe(32)
        op = PendingOperation(
            token=token,
            tool_name=tool_name,
            arguments=arguments,
            description=description,
            expires_at=time.monotonic() + self._ttl,
        )
        self._pending[token] = op
        return op

    def consume(self, token: str, tool_name: str, arguments: dict[str, Any]) -> PendingOperation:
        """Single-use: raises ToolError if missing/expired/mismatched; removes on success."""
        ...

    def _evict_expired(self) -> None: ...
```

- **Lifecycle**: created by a high-risk tool's unconfirmed call; consumed exactly once by
  the matching confirmed call; otherwise evicted after `expires_at` (checked lazily on
  next `create`/`consume`, no background task — Constitution Principle I, simplest
  structure satisfying the requirement).
- **Scoping** (FR-010): `consume` MUST verify `tool_name` and `arguments` match what was
  stored, not just that *some* token was supplied — prevents reusing a reboot confirmation
  to authorize a different high-risk call.
- **Never persisted**: lives on the `OPNsenseClient`-adjacent server instance; a process
  restart drops all pending confirmations (matches spec Assumptions).

---

## VPN Instance (OpenVPN / IPsec / WireGuard)

A configured tunnel/service. Shape differs per protocol (mirrors OPNsense's own object
shapes exactly — no unifying abstraction invented, per Constitution Principle I: three
concrete shapes, not one premature "VPNInstance" superclass):

- **OpenVPN `Instance`**: `vpnid`, `enabled`, `role` (server/client), `dev_type`, `proto`,
  `port`, `local`, `remote`, `topology`, `cert`, `ca`, `tls_key`, `authmode`.
- **IPsec `Connection`**: `enabled`, `proposals`, `version`, `local_addrs`, `remote_addrs`,
  `pools`, `description`, nested `locals`/`remotes`/`children`.
- **WireGuard `Server`**: `name`, `instance`, `pubkey`, `privkey` (redacted on read),
  `port`, `mtu`, `dns`, `tunneladdress`, `peers`, `gateway`.

## VPN Peer/Client Entry

- **OpenVPN `ClientOverwrite`** (`cso`): per-client override tied to a common name.
- **IPsec `Child`** (phase 2 / child SA): `local_ts`, `remote_ts`, tied to a `Connection`.
- **WireGuard `Client`** (peer): `name`, `pubkey`, `psk`, `tunneladdress`, `endpoint`,
  `keepalive`. No private-key field exists on this object (see research.md §4) — FR-017
  redaction is a documented no-op here, not a missed case.

## Proxy Configuration

Squid general settings object (`proxy/settings/get`): nested `general`, `cache`,
`traffic`, `forward` (containing the flat ACL CSV-list fields — `allowedSubnets`,
`unrestricted`, `bannedHosts`, `whiteList`, `blackList`, `safePorts`, `sslPorts`),
`parentproxy`, `icap`, `auth`. Plus array-typed `remoteACLs.blacklists.blacklist` entries
(downloadable feed definitions) and PAC rule/proxy/match entries.

## Captive Portal Zone

`zone`: `enabled`, `zoneid`, `interfaces`, `authservers`, `idletimeout`, `hardtimeout`,
`concurrentlogins`, `certificate`, `allowedAddresses`, `allowedMACAddresses`, `template`,
`description`. Contains (by reference, not embedding) active **Session** entries:
`sessionId`, `userName`, `ipAddress`, `macAddress`, `startTime`.

## Certificate / Certificate Authority

`Ca`/`Cert` (near-identical shape): `refid`, `descr`, `caref` (Cert only), `crt` (base64
cert), `prv` (base64 private key — **redacted on read**), `csr`. Creation-time-only
fields: `action`, `key_type`, `digest`, `cert_type`, `lifetime`, `private_key_location`,
`crt_payload`/`csr_payload`/`prv_payload`. Revocation state lives in a separate `Crl`
object per CA: `revoked_reason_0` … `revoked_reason_6`, each a CSV list of cert `refid`s.

---

## Redaction Helper (new — supports FR-017)

```python
def redact_private_keys(obj: dict[str, Any], fields: frozenset[str]) -> dict[str, Any]:
    """Return a shallow copy with any of `fields` present at the top level removed.
    Applied per-domain with an explicit field set (StaticKey.key, KeyPair.privateKey,
    PreSharedKey.Key, WireGuard Server.privkey, Cert/Ca.prv and .prv_payload) — no
    generic "any key-shaped string" heuristic, since that would risk both false positives
    (redacting legitimate non-secret fields) and false negatives (missing a field named
    unexpectedly). Explicit is better than clever here (Constitution Principle I/II).
    """
```

Applied at the tool layer (in each domain's `_xxx_get`/`_xxx_list`/`_xxx_search` wrapper),
not in `OPNsenseClient` — the client stays a thin, domain-agnostic transport; redaction is
domain knowledge and belongs with the tools that have it (matches existing separation
between `client.py` and `tools/*.py`).

---

## Service Module List (FR-006 — reconciliation)

Current `SUPPORTED_MODULES` in `tools/services.py` is `{"unbound", "kea", "ids"}`. This
must be re-verified against 26.7.1 before 002 ships (task in tasks.md), and extended to
include `openvpn`, `ipsec`, `wireguard`, `squid` (proxy), `captiveportal` — each of these
domains' own `Service` controller already provides `start`/`stop`/`restart`/`status`
identical in shape to the existing ones, so the existing generic `service_*` tools can
cover them **if** their module-path prefix matches the `{module}/service/{action}` pattern
already assumed by `tools/services.py`. Confirmed all six do.
