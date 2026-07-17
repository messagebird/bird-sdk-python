# Changelog

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
