# Changelog

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
