# Changelog

## 0.10.0

- Add sms.tfn_verification webhook event types
- Add email statistics reads under `email.stats`: the period summary, the daily and hourly time series, and the dimension breakdowns (by tag, category, sending IP, sending domain, recipient domain, mailbox provider, mailbox-provider region, template, location, client, bounce code, complaint type, and broadcast).
- **Breaking:** the Realtime webhook event type `realtime.subscription_count` is now `realtime.connection_count`, matching Bird's Realtime vocabulary (per channel it counts connections — one connection cannot subscribe twice). Realtime is in early access; the old event type had no GA consumers.
- Documentation-only: docstrings and help text regenerated from a description pass across the entire API spec. Operations and fields now document units, defaults, omission behavior, and per-value status meanings. Several descriptions were corrected to match actual behavior, including engagement-rate denominators, suppression prefix matching, and stored-content retention. No functional changes.
- Regenerate from the beak codegen toolchain (generator provenance headers only; no API changes)
- Regenerated models: timestamp examples now render in RFC 3339 format
- WhatsApp templates: create and list/get a workspace's own message templates. Reads now include a template id and an optional description; create takes a name, category, components, a WhatsApp language code, and an optional description; sending gained a named parameter name for named-parameter templates. Additive; no breaking change.

## 0.9.2

- Suppressions: `reason`, `origin`, and `applies_to` are now documented as growing vocabularies (open enums on the wire) — `origin` gained `unsubscribe_link`, a suppression created by the recipient through Bird's hosted unsubscribe page or its one-click link. Treat unknown values as informational rather than rejecting the record. Additive; no breaking change.

## 0.9.1

- Add voice call-event webhook types: `voice.call.initiated`, `voice.call.answered`, and `voice.call.ended` are now recognized event types with typed payloads. Additive; no breaking change.

## 0.9.0

- **Breaking:** WhatsApp message reads now return `from` and `to` (each a phone number and/or business-scoped user ID) in place of `business` and `contact`, matching the SMS/email convention.

## 0.8.4

- **Breaking:** the contact list free-text filter is now `q` (was `search`), matching the API's renamed query parameter. Update `client.contacts.list(search=...)` to `client.contacts.list(q=...)`.

## 0.8.3

- Received messages and the `email.received` event now carry `authentication` (`pass`/`fail`/`unknown`), a single summary of sender authentication; treat `unknown` as not verified. The `spf_pass`/`dkim_pass`/`dmarc_pass` fields remain. Additive; no breaking change.

## 0.8.2

- Add the WhatsApp webhook event types: `WHATSAPP_ACCEPTED`, `WHATSAPP_SENT`, `WHATSAPP_DELIVERED`, `WHATSAPP_READ`, and `WHATSAPP_FAILED`. Additive; no breaking change.

## 0.8.1

- Docs: align the SDK example markers on the `audiences`, `contacts`, and `contact_properties` resources with their operation keys so the API reference renders their Python code samples. Marker comments only — no change to the published API or runtime.

## 0.8.0

- Add the sending domains collection (sync and async): `client.domains.create`, `.get`, `.list`, `.update`, `.delete`, and `.verify`. Register a sending domain, publish the DNS records it returns, then verify until it is usable as a sender. Requires an API key with the `domains` scope.

## 0.7.5

- Add the Realtime webhook event types: `REALTIME_CACHE_CHANNELS`, `REALTIME_CHANNEL_EXISTENCE`, `REALTIME_CLIENT_EVENTS`, `REALTIME_PRESENCE`, and `REALTIME_SUBSCRIPTION_COUNT`. Additive; no breaking change.

## 0.7.4

- Contacts now carry `channels` (the channels a contact can be reached on) and audience members carry the `audiences` they belong to. Listing an audience's contacts gains an optional `search` filter (email substring). Additive response fields and an optional parameter; no breaking change.

## 0.7.3

- Correct the `verify.verifications.check` documentation: an already-resolved verification is no longer checkable and returns a 404, not a result with `success=False`. Documentation only; no API or behavior change.

## 0.7.2

- WhatsApp failure detail now carries `meta_error_code`, the raw error code from the WhatsApp Cloud API, and a fuller `description` sourced from Meta's error details. Additive response fields; no breaking change.

## 0.7.1

- Correct the error-code names shown in preview-feature field descriptions (regenerated from the API spec). Documentation only; no API or behavior change.

## 0.7.0

- Add the Verify product (sync and async): `client.verify.verifications.create` sends a one-time passcode to a recipient and `client.verify.verifications.check` validates the code they submit.

## 0.6.0

- Add the WhatsApp channel (sync and async): `client.whatsapp.send`, `.get`, `.list`, `.list_events`. Add WhatsApp templates (read-only): `client.whatsapp_templates.list`.

## 0.5.0

- Remove the email templates collection (`client.email_templates.create`, `.get`, `.update`, `.delete`, `.publish`, `.list`, `.list_versions`, `.get_version`), added in 0.3.0. Template management is no longer part of the public API. Sending a published template with `client.email.send` (pass `template` as an `emt_…` ID or name handle) is unchanged.

## 0.4.1

- Add `client.email.cancel` (sync and async): cancel a scheduled message before it sends. A message that already started sending, or was already canceled, raises a conflict error.
- Attribute the calling tool on every request via the `Bird-Caller` header, detected from the environment (no configuration).

## 0.4.0

- Add the contacts collection (sync and async): `client.contacts.create`, `.get`, `.list`, `.update`, `.delete`, and `.batch` (bulk upsert by email). Requires an API key with the `email_marketing` scope.
- Add the audiences collection (sync and async): `client.audiences.create`, `.get`, `.list`, `.update`, `.delete`, plus membership `.list_contacts`, `.add_contacts`, `.remove_contacts`, `.remove_contact`.
- Add contact properties: `client.contact_properties.create`, `.get`, `.list`, `.update`, `.archive`, `.unarchive`.

## 0.3.0

- Add the SMS channel (sync and async): `client.sms.send`, `.send_batch`, `.get`, `.list`.
- Add SMS templates (read-only): `client.sms_templates.list`, `client.sms_templates.get`.
- Add email templates: `client.email_templates.create`, `.get`, `.update`, `.delete`, `.publish`, `.list`, plus versions `.list_versions` and `.get_version`.
- `client.email.send` can send a published template: pass `template` (an `emt_…` ID or name handle) with `parameters` in place of inline `subject`/`html`/`text`.

## 0.2.2

- Rename the anonymous client-identity headers from `X-Bird-*` to `Bird-*` (the `X-` prefix is deprecated, RFC 6648). Same telemetry, new header names; no other behavior or API-surface change.

## 0.2.1

- Send anonymous `X-Bird-*` client-identity headers (surface, version, language, os, arch) on every request, so Bird can attribute API usage by surface. No personal data, credentials, or request content: just which Bird client and platform. Telemetry only; no behavior or API-surface change.

## 0.2.0

- Add batch email send: `client.email.send_batch` (sync and async).
- Point package metadata at the docs (https://bird.com/docs/sdks/python).

## 0.1.0

- Initial release: sync and async clients, email send, webhook verification, pagination, typed errors.
