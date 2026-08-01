# MCP Tool Contracts: Trust / Certificates & PKI Domain

Core module `trust`. Certificate/CA mutations are staged in the OPNsense sense (no
separate apply step exists for this domain — `add`/`set`/`del` take effect immediately in
the config store, same as the underlying OPNsense behavior; there is no `trust_apply`).
Revocation is high-risk (FR-016).

---

## Tool: `trust_ca_list` / `_get`

`/api/trust/ca/{search|get}[/{uuid}]`. Object key `ca`: `refid`, `descr`, `crt` (base64
cert), `prv` (base64 private key), `csr`.

**`prv` and `prv_payload` redacted on every read** (FR-017) — see the one-shot-disclosure
exception under `trust_ca_add` below.

## Tool: `trust_ca_add`

**Description**: Import or issue a new Certificate Authority.

**OPNsense endpoint**: `POST /api/trust/ca/add`

**Input schema**: `{"type": "object", "properties": {"ca": {"type": "object",
  "description": "action (internal/external/import), key_type, digest, cert_type, lifetime, private_key_location, crt_payload, csr_payload, prv_payload, descr, etc."}}, "required": ["ca"]}`

**Output**: `{"result": "saved", "uuid": "<new-uuid>"}`. **Exception to the redaction
rule**: when `private_key_location=local` is requested, OPNsense's own `add` response
includes the freshly generated key once, as `private_key`, in this same response — this
tool passes that field through untouched (the caller just asked for it), but its docstring
states this explicitly so a one-shot creation disclosure is never confused with a leak on
a later read. `private_key_location=firewall` (the default) never returns key material —
it's persisted server-side in `prv` instead, which is redacted on every future read.

## Tool: `trust_ca_update` / `_delete`

`POST /api/trust/ca/set/{uuid}`, `POST /api/trust/ca/del/{uuid}`. Standard risk (editing
metadata or removing an unused CA is not itself a trust-revocation event — see
`trust_certificate_revoke` for the high-risk operation in this domain).

---

## Tool: `trust_certificate_list` / `_get`

`/api/trust/cert/{search|get}[/{uuid}]`. Same shape as CA plus `caref` (issuing CA).
Same redaction rule and one-shot-disclosure exception as `trust_ca_*`.

## Tool: `trust_certificate_add`

**OPNsense endpoint**: `POST /api/trust/cert/add`. Same `action`/`private_key_location`
semantics as CA (internal/external/import/import_csr/sign_csr/reissue/manual).

## Tool: `trust_certificate_update` / `_delete`

`POST /api/trust/cert/set/{uuid}`, `POST /api/trust/cert/del/{uuid}`. Standard risk.

## Tool: `trust_certificate_export`

**Description**: Export a certificate/key/CSR/PKCS12 bundle in a specific format.

**OPNsense endpoint**: `GET /api/trust/cert/generate_file/{uuid}/{type}` (`type` = crt |
csr | prv | pkcs12).

**Notes**: `type=prv` and `type=pkcs12` return private key material by explicit request —
**not redacted**, since the caller is directly asking this specific tool to export the key
they already control. This is a deliberate export action, distinct from the general
`_get`/`_list` read path that FR-017 protects. Document this distinction clearly so it
isn't mistaken for a bypass of the redaction requirement.

---

## Tool: `trust_certificate_revoke`

**Description**: Revoke a certificate. High-risk — gated by `confirmation.md` (FR-016).

**No dedicated OPNsense revoke endpoint exists** (research.md §7, verified against source
and docs). This tool performs a read-modify-write against the CRL for the certificate's
issuing CA: `GET /api/trust/crl/get/{caref}` → add the cert's `refid` into the requested
`revoked_reason_N` bucket (default reason `0`=unspecified if the caller doesn't specify
one) → `POST /api/trust/crl/set/{caref}` with the updated state.

**Input schema**:
```json
{
  "type": "object",
  "properties": {
    "uuid": {"type": "string", "description": "Certificate UUID to revoke"},
    "reason": {"type": "integer", "minimum": 0, "maximum": 6, "default": 0,
      "description": "0=unspecified 1=keyCompromise 2=cACompromise 3=affiliationChanged 4=superseded 5=cessationOfOperation 6=certificateHold"},
    "confirm": {"type": "string"}
  },
  "required": ["uuid"]
}
```

**Preview description example**: `"Will revoke certificate <descr> (<refid>) issued by CA
<caref>, reason=<reason>. This cannot be undone via this tool (un-revoking requires
manually editing the CRL)."`

**Output on confirmed execution**: `{"result": "saved"}` (the `Crl.set` response) plus the
`caref`/`refid` acted on, for confirmation.

---

## Tool: `trust_crl_list` / `_get`

**Description**: Read the current CRL state for a CA (which certs are revoked and why) —
useful for a client to inspect before calling `trust_certificate_revoke`, and to verify
its effect afterward.

**OPNsense endpoint**: `GET /api/trust/crl/search`, `GET /api/trust/crl/get/{caref}`.

## Tool: `trust_settings_get` / `_update`

Whole-model general trust settings. `GET /api/trust/settings/get`, `POST /api/trust/settings/set`.
Standard risk.
