# Changelog

## 0.2.1

- Send anonymous `X-Bird-*` client-identity headers (surface, version, language, os, arch) on every request, so Bird can attribute API usage by surface. No personal data, credentials, or request content: just which Bird client and platform. Telemetry only; no behavior or API-surface change.

## 0.2.0

- Add batch email send: `client.email.send_batch` (sync and async).
- Point package metadata at the docs (https://bird.com/docs/sdks/python).

## 0.1.0

- Initial release: sync and async clients, email send, webhook verification, pagination, typed errors.
