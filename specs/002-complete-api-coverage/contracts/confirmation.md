# MCP Tool Contract: Confirm-Then-Execute Pattern (cross-cutting)

This is not a single tool's contract — it's the shared calling convention every high-risk
tool in this spec follows (FR-007–FR-011). Each high-risk tool's own contract (see
`system.md`, `trust.md`, `captiveportal.md`, VPN contracts' teardown/disable tools)
references this document instead of repeating it.

**No dedicated OPNsense endpoint** — this is server-side logic in front of the real
endpoint; OPNsense is not contacted until the confirmed call.

## Shared parameter: `confirm`

Every high-risk tool accepts an additional optional parameter:

```json
{
  "confirm": {
    "type": "string",
    "description": "Confirmation token from a prior unconfirmed call to this same tool. Omit to preview the operation without executing it."
  }
}
```

## Call 1 — Preview (no `confirm`, or `confirm` omitted)

The server validates the tool's other arguments (schema + any input validation that
doesn't require contacting OPNsense), computes a human-readable description of the
effect, registers a `PendingOperation` (see `data-model.md`), and returns:

```json
{
  "status": "confirmation_required",
  "confirm_token": "<opaque, single-use, ~43-char urlsafe string>",
  "description": "<what will happen, specific to the arguments given>",
  "expires_in_seconds": 120
}
```

**No request reaches OPNsense during this call** (FR-008, SC-003).

## Call 2 — Confirmed (`confirm=<token>`)

The server looks up `confirm_token`. It MUST match:
1. An unexpired, unconsumed token,
2. issued for this exact tool name,
3. issued for arguments identical to the ones supplied on this call (excluding `confirm`
   itself).

If all three hold: the token is consumed (removed — single-use, FR-010), the real
OPNsense request is sent exactly once (SC-004), and the tool's normal success/error
response is returned.

If any check fails (missing, expired, wrong tool, mismatched arguments, already
consumed): the server raises `ToolError` with a message telling the caller to request a
fresh preview. **No request reaches OPNsense.**

## Logging (FR-011, SC-005)

- The preview call produces a diagnostic record with `outcome="preview"` (tool name,
  arguments, generated token — never a request to OPNsense, so no status code).
- The confirmed call produces the normal per-call log record for the underlying OPNsense
  request (`outcome="success"|"error"`), plus is distinguishable from the preview by
  carrying the same `confirm_token` value for correlation.

## Expiry (FR-010, Edge Case)

Tokens expire `expires_in_seconds` after issuance (default 120s, see
`data-model.md`/`research.md` §1). Expiry is enforced lazily — checked when the token is
looked up, not via a background timer. An expired token behaves identically to a missing
one: `ToolError`, fresh preview required.

## Non-goals

- Not persisted across server restarts (spec Assumptions).
- Not a general-purpose auth/approval system — scoped to the specific high-risk
  operations enumerated in FR-007.
- Does not protect against the underlying OPNsense state changing between preview and
  confirmation (spec Edge Case: the confirmed call is still attempted; whatever error
  OPNsense returns is surfaced as-is).
