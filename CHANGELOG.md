# Changelog

## 0.44.0

- Mailboxes now report `size_bytes`: the stored bytes of their retained messages (the metadata and extracted text kept for the retention tier plus attachment bytes). Plans can cap it per mailbox; a send from a mailbox at its cap is rejected with `E17049`.

## 0.43.0

- Mailbox `retention_tier` now accepts `90d` and `1y` on create and update, gated by the organization's plan; a tier the plan does not include is rejected with `E17048`.

## 0.42.0

- **Breaking:** `Webhooks`/`AsyncWebhooks` are constructed as `Webhooks(client, secret)`; a receiver verifies through `Bird(webhook_secret=...)` — no API key required.
- The client is constructible with only the webhook secret — no API key — for receiver-only deployments; an API call on such a client fails with a missing-API-key error before any request is sent.
- `webhooks` now manages endpoints: list, get, create, update, delete, send a test event, inspect delivery attempts, and rotate the signing secret.

## 0.41.1

- SMS segment docs: the UCS2 limit is 70 UTF-16 code units, not 70 characters, so 35 non-BMP emoji fill one segment.

## 0.41.0

- Add the `workspace` resource: `get()` returns the workspace the credential is scoped to, including its id, name, owning organization's id, and notification and logo settings.

## 0.40.0

- A `404` from checking or advancing a verification now says that no verification matched the recipient: either none exists for the exact recipient given, or the most recent one is already resolved as verified, expired, or out of attempts. It also says when to create another — create one when the recipient has no verification, or the last one expired or ran out of attempts, and not when the recipient already passed. The error code is unchanged, so match it exactly as before; a `404` is not evidence the recipient failed to verify, so treat your own record of an earlier `success: true` as the outcome.

## 0.39.0

- A WhatsApp message carrying contact cards a contact shared now reads them back on `contact_cards`, where it previously reported `unsupported` with type `contacts`.
- `undelivered` now documents as a final status, `validity_period` as bounding the carrier's delivery attempts rather than ours, and `scheduled` and `canceled` as reserved for send-later scheduling. `category` no longer describes per-country compliance rules that are not implemented.

## 0.38.2

- Sending a WhatsApp template: the `parameters` field now documents which button types take no value, so no component is sent for them.

## 0.38.1

- Example values on `date`, `date-time` and numeric fields now match the examples the API declares (`2026-05-01` for a `date` field, `0.0` for a nullable number).

## 0.38.0

- Add the `preferences` resource — list, get, create, and delete stated messaging preferences (consent grants and opt-outs) across email, SMS, and WhatsApp — plus `contacts.preferences.list` for the rows keyed to a contact's own handles, and typed webhook events for `preference.granted`, `preference.revoked`, `preference.deleted`, and `whatsapp_suppression.created`.

## 0.37.2

- `refresh_cursor` fetches the items that sort before a response's first row in the current sort order. Those are the items added since the response only when new items sort first, so a list sorted another way is refreshed by re-fetching it.

## 0.37.1

- `Number.kind` documentation now distinguishes workspace-owned subscriptions from Bird-managed shared numbers.

## 0.37.0

- Voice call records carry a `tags` array, and the voice call list takes a repeatable `tag` filter (`name` or `name:value`). On the CLI that is `bird voice list --tag campaign:spring --tag queue`.

## 0.36.0

- Add the `info` SMS keyword operation, and the previously undocumented `confirm`, to the SMSKeywordOperation open enum.

## 0.35.0

- Add the `sms_suppression.created` webhook event type.

## 0.34.0

- **Breaking:** the API now rejects a request that carries a query parameter an operation does not declare, with a 422 `E01029`, instead of silently ignoring it. This affects `extra_query`/`default_query` on `bird.Client`/`bird.AsyncClient` (Python), the `query` option on `bird.request` (Node), the `$query` argument on generated resource methods (PHP), and a query string written into the path passed to `Client.Get` and its sibling verb methods (Go): an unrecognized key that previously had no effect now fails the call. Check any code passing one of these against the operation's documented query parameters.
- Listing WhatsApp messages now takes `to` and `from` filters (`from_` in Python, where `from` is reserved), each matching an E.164 phone number or a business-scoped user ID. The `phone_number` filter is deprecated; use the new pair instead.

## 0.33.1

- A voice call's `actor` now documents the values its `type` can take: `user`, `oauth_token`, `api_key`, `system`, `sso`, and `service_account`. The enum stays open, so treat an unrecognized value as a newer type rather than an error.

## 0.33.0

- Add the `verify.verification.failed` webhook event, which fires when no planned channel could deliver a verification's passcode, plus the `undeliverable` session reason and the `not_billable` attempt reason that say why it could not.

## 0.32.0

- Email broadcasts report `started_at` and `canceled_at`: when sending began, and when cancellation was requested.

## 0.31.0

- Numbers are now available on the public API. Search a country's available numbers, order one, list and read the numbers your workspace holds, and release a dedicated number you no longer want.
- **Breaking:** a voice call's `cost` is its own call-cost type rather than the shared money type, so a caller that names the money type for that field changes it to the call-cost type — reading `cost.amount` and `cost.currency_code` needs no change. The money type is gone from the package, having been reachable only through that field.
- A voice call's `cost` gains `outbound_amount`, `inbound_amount` and `call_handling_amount`, naming the components behind the total so a call charged for more than one thing can report which amount is which. Each reads `null` until that component is priced. Every amount on a voice call's cost now renders at six decimal places, the scale the reference documents.
- A WhatsApp message that failed because WhatsApp could not fetch the media URL, or refused the file it found there, now reports `media_rejected` on `last_error.code` instead of `undeliverable`, with WhatsApp's own reason in `last_error.description`.
- A sending domain's inbound MX records now report `optional` as `true` until you enable receiving on that domain, so the records you must publish to send are no longer listed alongside ones that would reroute the domain's existing mail.
- The numbers reference and examples describe a number as allocated to a workspace, the same word the API reference and the dashboard use.
- The numbers methods document what each one does to a carrier and to your balance — that a search can go stale before an order lands, that an order may settle after the call returns, and that a release is irreversible.
- Pagination cursors now carry an example value, so a cursor field shows a representative token instead of nothing when you inspect the SDK types or the API schema.
- The `verify.attempt.sent` schema example pairs a routable destination with the sender that destination resolves to.
- A voice call's `actor.type` can be `service_account`, meaning the call was placed by an integration acting for the workspace rather than by a user or an API key. Documented on the actor's `id` and `type`, and on the call's own `actor` field, which previously described only users and API keys.
- Sending a WhatsApp message from a number whose setup has not finished now returns a `422` `WhatsAppSenderNotConnected`, rather than an unknown-number error or an accepted send that later fails.

## 0.30.0

- Add client.sms_keyword_rules: read Bird's SMS keyword catalogue and manage a workspace's own overrides of it.
- Add client.sms.stats and client.sms_suppressions: SMS statistics (outbound, inbound breakdowns) and the suppression list, plus sms.list_events for a message's timeline.
- Add end-to-end encrypted channels: `realtime.publish` and `realtime.publish_batch` seal `private-encrypted-` payloads under the `realtime_encryption_master_key` client option (install `messagebird-sdk[realtime-encryption]` for the cipher), and the new `realtime.authorize_channel` signs channel subscriptions, adding the channel's `shared_secret` on encrypted channels.
- A sending domain read now says what to do next. `next` carries the steps that get the domain verified, in the order to take them: an `external` step for a DNS record only you can publish, then the operation that re-checks it. An empty list means nothing is asked of you on that axis, and `capabilities` still reports what each capability needs before the domain can send or receive.
- Email defaults now cover `ip_pool_id`, applied to every send that does not name a pool.
- `email.mailboxes.messages.create` now honors the email defaults for the fields a compose accepts: `reply_to`, `category`, `tags`, and `metadata`.
- Optional fields on a WhatsApp message's content — a media caption, a location's name and address — are omitted when unset rather than returned as null.
- Getting or listing a WhatsApp message now returns the free-form `text`, `image`, `video`, `audio`, `sticker`, `document` or `location` content it carried.
- The `whatsapp.received` webhook event is now available, delivering an inbound WhatsApp message's content as it arrives.
- `whatsapp.send` now accepts free-form `text`, `image`, `video`, `audio`, `sticker`, `document` and `location` content, `from_` for the business number every send but a Bird-managed template requires, and per-message `tags` and `metadata`.
- Method, parameter and field documentation now states what each call does and what each value accepts, including its default, its units, and the fields it depends on.

## 0.29.0

- **Breaking:** an SMS template is referenced by its `slug`, not its `name`. On a send, `template.name` becomes `template.slug` (unchanged if you pass an id). On a template read, `slug` is the handle you send by and `name` is now the display label the old `description` carried, so `description` reads null for Bird's built-in templates.
- An SMS template read now reports what a send will do with languages, the way email and WhatsApp already did: `default_language`, `languages`, `on_missing_language` and `language_source_required`. Its `published_version_id` is now `live_version_id`, and its status vocabulary drops `approved`, which was never returned, for `inactive`.
- **Breaking:** the contacts list `phone_number` filter now takes a list of numbers rather than one, matching any of up to 50 in a single request; pass an existing single number as a one-element list, and set `limit` to at least the number of values you pass.
- **Breaking:** the recovery steps on an error are `NextAction` rather than `ErrorNextAction`, and each one states a `kind` of `operation`, `external`, `wait` or `terminal`. Rename the type at your call site, and read `kind` before `operation`: only an `operation` step carries one. Treat a `kind` you do not recognise as display-only.
- Schedule an email from the SDK instead of dropping to raw HTTP for that one call: `scheduled_at=` holds a send until a future instant.
- Telegram is a known verification channel, so a verification can be created with `telegram` in `options.channels` and a passcode can be delivered over it.
- WhatsApp message events gain a `WhatsAppEventType` export carrying the event's known values, matching the `WhatsAppErrorCode`/`EmailEventType` constants already exported.
- Document sending a stored email template, with a per-language example on email.send.
- SMS sends normalize the recipient to canonical E.164 and echo that form back; an unroutable recipient returns the new SMSInvalidRecipient error.

## 0.28.0

- Adds the lookup channel: bird.lookup.email() and bird.lookup.phone_number(), on both Bird and AsyncBird.
- The contacts documentation now names `phone_number`, the identifier the API accepts, where it previously named `phone` — including the batch `match_on` value, which is rejected as `phone`.
- LookupPropertyStatus is now an open enum, so a future property status will not break a deployed client.

## 0.27.0

- **Breaking:** a contact's phone identifier is now named `phone_number`, matching the rest of the API. It replaces `phone` in create, update, batch-upsert and read bodies; the `GET /v1/contacts` filter becomes `?phone_number=`; the `identifier` filter value and the batch `match_on` / `matched_on` values become `phone_number` — they name the field, so they move with it. On the TCR brand surface, a brand's own `phone` becomes `phone_number` as well. The CLI's `bird contacts create|update` take `--phone-number`, and `bird contacts list` filters on `--phone-number`. Qualified compounds are unchanged: `mobile_phone`, `primary_phone` and `business_contact_phone` keep their names.
- Add `options.smart_encoding` to an SMS send (`--smart-encoding` on the CLI): it replaces characters outside the GSM-7 alphabet (curly quotes, dashes, ellipses, fullwidth forms, non-breaking spaces) with their closest equivalent, which lowers the segment count and the cost on a body that would otherwise send as `UCS2`. Off unless you ask for it, and all-or-nothing: a body still holding an emoji or a non-Latin script afterwards is sent exactly as you supplied it. The message reports the settings that were applied, and its `text` reflects the body as sent.
- **Breaking:** a verification's email recipient is now named `email`, replacing `email_address` — rename it at the call site on a verification's `to`, and in any handler reading the `to` of a `verify.*` webhook payload. Phone recipients are unchanged: `phone_number` keeps its name. The old spelling is not accepted: a request sending `email_address` is rejected as an unknown property.

## 0.26.0

- **Breaking:** `carrier` and `mcc_mnc` are omitted from `sms.sent`, `sms.delivered` and `sms.received` webhook payloads when the carrier reports none, instead of arriving as `null`; `subject` on `sms.received` behaves the same way. They are now optional rather than required, so a typed field changes to a pointer or an optional — check for absence where you checked for `null`. This matches how the message resource has always reported the same fields.
- `sms.accepted` now carries `segments`, the segment breakdown the send is billed on, so a webhook-only integration can explain the `cost` on the same event instead of fetching the message to reconcile a charge.
- Subscribe to `sms.received` to be pushed inbound SMS instead of polling for it. The payload carries the message body, its segment breakdown, both numbers, and the sending operator where the carrier reports one; a `STOP` arrives as an ordinary received message and is yours to act on.

## 0.25.1

- A verification attempt can now report `delivery_timeout` as its failure reason, meaning no delivery confirmation arrived before the channel's timeout and the verification failed over to the next channel.
- Path ids are percent-encoded, so an id containing a reserved character reaches the intended endpoint instead of silently becoming URL structure.

## 0.25.0

- An SMS error `code` is now an open enum: a reason added by a newer server parses through as a plain string instead of raising a validation error, so a delivery receipt carrying one no longer fails to read. The values known at this version are exported as `SMSErrorCode`.
- The `sms.expired` webhook payload now carries `error`, the same failure detail the other terminal SMS events carry: a Bird-stable `code`, a `description`, and the provider's `carrier_error_code` when it sent one.
- **Breaking:** An email template reads the recipient's contact record through `bird.contact.<attribute>` and the unsubscribe link through `bird.unsubscribe_url`. Rewrite a template that uses any other spelling for those values and republish it.
- **Breaking:** A send by template must supply a value for every parameter its template uses, and a parameter name must be a single word. A send that omits one is rejected rather than delivered with a blank in place of the value.
- **Breaking:** A `marketing` template has to place `bird.unsubscribe_url` in its body to publish, in every language it carries. The token stands on its own: no filters, not inside an `{% if %}` or `{% for %}` block, and not in the subject. Where a language has both an HTML and a text body, the HTML one has to carry it.
- `bird` is now the only name you cannot use for a parameter, so `contact`, `unsubscribe_url` and `first_name` are all available.
- Listing calls now accepts in-flight and final statuses together in one `status` filter and returns them as a single page, where mixing them used to be rejected.
- **Breaking:** a WhatsApp template parameter's `text` is now optional and should be read as nullable. It carries a value only on a `text` parameter, and a parameter of any other kind carries its value in the field named for that kind.
- Template parameters can now describe more than text. `type` accepts `image`, `video`, `gif`, `document` and `location` alongside `text`: `image`, `video`, `gif` and `document` carry a media header's file in `url`, and `location` carries a location header's point in `location`. A parameter's kind names only the field its value travels in — a coupon button's code is a plain string, so it is still a `text` parameter (`{"type":"text","text":"LUCAS25"}`), the same shape the code was authored under. A `carousel` component carries its values per card, in `cards[]`, one entry per card in the order the template was approved with.
- Three WhatsApp field descriptions now match what the API does. Omitting a template send's `language` sends the template's default language rather than returning a `422`; `received` is documented as an inbound message's status rather than as reserved; and a WhatsApp message's `cost` explains that an inbound message is never priced.

## 0.24.0

- Listing contacts gains an `identifier` filter (`email` or `phone`), and each contact now includes its `audiences`.
- **Breaking:** an SMS message's `text` is now optional — a message you sent always carries one, but a received message may not. Handle its absence rather than assuming every message has a body.
- Every `sms.*` webhook payload now carries `cost`, split into `transaction_amount` and `passthrough_amount` over one currency. The figure is as of that event, and the components are named so a subscriber merges them per component rather than replacing the object, since webhook delivery is not ordered.
- Verify gains a next-channel action: when a recipient reports the passcode never arrived, send a fresh one on the next channel in the verification's plan without waiting out the resend cooldown. Identify the verification by the same recipient you started it with, as with a check — there is still no id to store. Every passcode already sent stays valid, so a late arrival can still be checked. Available as `verify.verifications.nextChannel` / `NextChannel` / `next_channel` / `nextChannel` on the TypeScript, Go, Python, and PHP SDKs, `bird verify verifications next-channel` on the CLI, and the `verify_verifications_next_channel` MCP tool. A verification whose channel plan is exhausted answers `422 NoNextChannel`.
- Add a `voice` resource for reading the call log: list the workspace's calls with the dashboard's filters, and fetch one call at any point in its lifecycle.
- A voice call now reports `actor`, the API key or user that placed it. It is absent on calls that ended before Bird began recording it, and on any call your trunk admitted by source IP address, since that path carries no credential to identify a caller.
- A WhatsApp message's `cost` now names its components, matching SMS: `transaction_amount` is what Bird charged to send the message, and `passthrough_amount` is reserved for third-party fees. `amount` remains the total.
- The create-verification docs no longer name SMS as the phone channel: a phone recipient is verified over the phone channels enabled for its destination country, in that country's configured order.

## 0.23.0

- An SMS message's `cost` now names its components: `transaction_amount` is what Bird charged to carry the message, and `passthrough_amount` is reserved for third-party fees such as US 10DLC carrier surcharges. `amount` remains the total.

## 0.22.0

- Listing WhatsApp messages gains a `category` filter, matching the equivalent filter on SMS and email messages.

## 0.21.0

- The Realtime app credentials can now be overridden per call, keyed by security scheme: `options={"credentials": {"RealtimeKey": …, "RealtimeSecret": …}}`. One client can address several Realtime apps; setting them on the client stays the default.
- Batch contact upserts now match each entry automatically on every identifier it carries (email, phone, or external_id), refusing entries whose identifiers belong to more than one contact; `match_on` (`email`, `phone`, or `external_id`) forces a single key. Result items echo what each entry supplied under a nested `entry` object (`email`, `phone`, `external_id`, null where absent, never the contact's current state), plus a top-level `matched_on` naming which identifier matched, null for created rows.
- Failed rows in a batch contact upsert carry the specific error `code` (for example `E04058`, ambiguous match, versus `E04055`, phone taken) alongside `type` and `message`, so a sync can branch on which conflict it hit.
- **Breaking (0.x):** `Contact.channels` is removed: the field restated which identifiers are set under a reachability claim the platform cannot back. Read `email`/`phone` presence directly.
- **Breaking (0.x):** `Contact.email` is now optional: a contact may be identified by an E.164 phone number instead of, or as well as, an email address. Contacts gain `phone` and the contact list gains an exact `phone` filter.
- Filter WhatsApp messages by `direction`. The unfiltered list returns the whole conversation, so `direction` narrows it to what you sent or what the contact sent you.

## 0.20.0

- Voice call webhook payloads name the two parties from and to, replacing src_number and dst_number. A handler reading those fields on voice_call.initiated, voice_call.answered or voice_call.ended must rename them; every other field is unchanged.
- WhatsApp and SMS template `language` fields now take a BCP-47 tag (for example `pt-BR`); Meta's underscore form (`pt_BR`) is still accepted as an input alias but is no longer echoed back. WhatsApp template sends can now also address a template by `id`, as an alternative to `slug`: the existing `template` argument takes either, resolving a `wat_`-prefixed value as the id — the same convention it already uses for SMS's `smt_`.
- WhatsApp send: the `to` field now accepts a business-scoped user ID as well as an E.164 phone number, so you can message a WhatsApp user whose phone number you do not have. One-time-passcode templates still require a phone number and return `422 WhatsAppRecipientNotSupportedForTemplate` when sent to a business-scoped user ID.

## 0.19.0

- Add a `datetime` contact property type: an RFC 3339 timestamp with an explicit offset.
- Add realtime.members.send: deliver an event to every connection one member holds, addressing the person rather than a channel.
- Listing contacts gains an `include_total` flag for a total count, and `q` now matches first and last name as well as email.
- WhatsApp `rejected` now covers every refusal before transmit, not only a suppressed recipient: a charge decline (insufficient wallet balance, unpriced destination) and an undeliverable recipient report `status: rejected` with a `whatsapp.rejected` timeline event instead of `failed`. `whatsapp.rejected` is also now published on the message-events enum.
- **Breaking:** a WhatsApp send against a template that declares named parameters must now name every parameter, matched as a set, so order no longer matters; an unnamed, misnamed, duplicated, or missing name returns `422 WhatsAppTemplateParameterMismatch`. `bird_otp` stays positional: its values go in `{{n}}` order and must carry no name. Unnamed values were previously matched by position and could render the wrong content while reporting success, so sends made against these templates before this release are worth re-checking.
- Clarify the email broadcast and template descriptions, including the errors each operation can return.
- Correct the `parameters` field description for an inline send.
- Document that an authentication-category message returns a redacted body.
- Template variables now report a `sensitive` flag showing whether the value is redacted before storage.
- The mailbox read and statistics methods now carry a description instead of an empty docstring.

## 0.18.0

- Open-enum fields now carry their known values: reading one offers the values the API can send, and a value added by a newer server still decodes.

## 0.17.0

- Add a per-send `language` override for templated email: `EmailSendParams.Language` on the Go SDK, a `language` keyword argument on `client.email.send`/`send_batch` in the Python SDK, and `--language` on `bird email send`. Omitting it keeps today's behavior, sending the template's default language.
- Export the known values of every open enum (EmailEventType, VerificationChannel, WhatsAppErrorCode and the rest) as constants, so an open enum is no longer a bare string with its values buried in prose.
- Email message reads and send responses now report `requested_language` and `resolved_language`.
- Email message reads and send responses now report `template_id` and `template_version_id`. A template's live version changes each time you submit it, so the version is what identifies the wording a message was actually delivered with, and the two together fetch that content back.
- Passcode attempts can report `channel_disabled`, meaning Bird has temporarily stopped sending over that channel and the verification moved on to the next one.

## 0.16.0

- **Breaking:** a WhatsApp send addresses its template by `slug` (previously `name`), and a WhatsApp message read echoes `template.slug` (previously `template.name`). Templates carry the slug as their permanent handle; the display name is cosmetic and never affects sending.

## 0.15.0

- Email message reads now report the message as delivered. For a send that used a template, `subject` and the bodies from the message-content endpoint previously returned the template source, tokens and all, which is content no recipient received; they now return that source with the send's substitution values applied. The values themselves are exposed as a new `parameters` field so the inputs stay visible beside the result. Sends that supplied their content inline are unaffected.
- Nest mailboxes and threads under email, matching the URL and the CLI/MCP names. client.mailbox becomes client.email.mailboxes, client.mailbox_thread becomes client.email.threads, client.mailbox_thread_message becomes client.email.threads.messages, client.mailbox_receive_rule becomes client.email.mailboxes.receive_rules, and mailbox.compose becomes email.mailboxes.messages.create. Params TypedDicts are renamed to match.
- Document that a template's `language_source_required` setting makes the send block's `language` mandatory.
- Documented how category resolves on a send-by-template: omitting it takes the template's own classification, and setting it always overrides the template.

## 0.14.0

- Add an optional `language` to the email template send block, selecting which of the template's languages to send. The template's `on_missing_language` decides whether an unstocked language falls back or is rejected.
- `domains.create` / `update` now take wire-shaped nested params as typed TypedDicts (e.g. `tracking={'name': ...}`, `settings={'click_tracking': True}`) instead of flattened kwargs, matching Go and TypeScript.
- Add `contacts.batch`; its `contacts` argument is now typed `Sequence[ContactCreateParams]` instead of an untyped mapping.
- `mailbox_thread_message.reply` now accepts the full message body, including structured `tags` (`{name, value}`) and `attachments`. In Go, `ReplyAll` is now `*bool` so an explicit `false` reaches the wire.
- `mailbox_thread.update`: `labels` and `contact_id` are now typed keyword arguments.
- `mailbox.update`: the fields are now typed keyword arguments, and `confirm` is accepted and sent as a query parameter.
- Add the `mailbox` resource: `list`, `create`, `get`, `stats`, `labels`, `restore`, `resume`, and `delete`.
- **Go:** the create body's `ReceivePolicy` and `RetentionTier` are now the typed `MailboxCreateReceivePolicy` / `MailboxCreateRetentionTier` enums instead of plain strings.
- **TypeScript:** a write whose body has no required field now defaults its params to `{}`, so `bird.mailbox.create()`, `bird.audiences.update(id)`, and `bird.domains.update(id)` are callable without a body; the unused `MailboxList` envelope export is removed.
- Add the `mailbox_thread_message` reads: `list`, `get`, `body`, and `attachments`.
- **Python:** the `client.mailbox_thread.messages` nested accessor is replaced by the top-level `client.mailbox_thread_message` (matching Go and TypeScript).
- **TypeScript:** the unused `EmailThreadMessageList` export is removed.
- Add the `mailbox_thread` reads (`list`, `get`) and `delete`.
- **Go (breaking, 0.x):** `MailboxThreadService.Delete` takes `MailboxThreadDeleteParams{Permanent bool}` instead of a positional `permanent bool`.
- **TypeScript:** `mailboxThread.delete` accepts an optional `MailboxThreadDeleteQuery`; the unused `EmailThreadList` export is removed.
- **Python:** `mailbox_thread.delete` accepts a `permanent` keyword.
- Add the `mailbox_receive_rule` resource: `list`, `create`, and `delete`.
- **Go:** the create body's `Action` is now the typed `ReceiveRuleCreateAction` enum instead of a plain string.
- **Python:** the `client.mailbox.receive_rules` nested accessor is replaced by the top-level `client.mailbox_receive_rule` (matching Go and TypeScript).
- **TypeScript:** the unused `ReceiveRuleList` export is removed.
- Add the SMS reads `get` and `list`; `list` now accepts a `tag` filter.
- Add the `sms_templates` and `whatsapp_templates` resources; export the `SmsTemplateListParams` query TypedDict.
- Add the WhatsApp reads `get`, `list`, and `list_events`; `list` now accepts a `tag` filter.
- **Breaking (0.x):** `verify.verifications` `create` and `check` now take `to` (and `options_`) in the nested shape instead of flat `email`/`phone`/`code_length`/`channels` keyword arguments.
- WhatsApp messages now return `cost`, the amount charged for the message.
- The email template send block addresses a stored template by `slug` (previously `name`). Templates carry the slug as their permanent handle plus a separate free-text display `name`.
- The realtime.* webhook event type constants are no longer exported. Realtime webhooks are created and managed in the Bird dashboard.
- **Breaking:** remove the WhatsApp templates-list surface — `bird whatsapp templates list`, the `whatsapp_templates_list` MCP tool, and `whatsappTemplates.list` / `WhatsappTemplates.List` / `whatsapp_templates.list` in the TypeScript, Go, and Python SDKs. WhatsApp is still in preview and the templates contract is being reshaped for localisation; templates return to the public and command audiences at GA in the new shape.
- Clarified the VoiceCallStatus documentation: ringing and in_progress describe a call that is still up, rather than values held back for a future feature.
- SMS alphanumeric sender IDs now allow dashes and underscores alongside letters, digits, and spaces, and must contain at least one letter with no separator at either end. A digits-only value is a long code or short code, and is no longer accepted as a sender ID.
- `contact-properties` `create` and `update`: the fallback value is typed as any JSON value, and the property type is the named `ContactPropertyType`.
- Add the email read methods: `get`, `list`, and `cancel`.
- `EmailThreadMessageReplyRequest` gains an optional `attachments` field, matching the compose and direct-send surfaces.
- The SMS-template list filters carry their named enum types from the spec (TemplateScope, SMSMessageCategory) instead of inline unions.
- The stats trend-grain, message direction, and email status read filters are now typed rather than plain strings, so each carries the values it accepts.

## 0.13.0

- Add Realtime data-plane methods: publish, batch publish, channel list/get/members, and member disconnect.
- `contacts.update` now clears a nullable field when passed `None` (distinct from omitting it, which leaves it unchanged).
- Add the audiences resource. `AudienceContactsAddParams`/`AudienceContactsRemoveParams` are now `AudienceAddContactsParams`/`AudienceRemoveContactsParams` (match the method names).
- Add the domains resource: create, read, update, delete, and verify. List supports `sort`/`order`/`include_total`.
- Export the request-unset sentinel `Omit` / `omit` from the top-level `bird` package: a request-body parameter defaults to `omit` (left out of the request), distinct from an explicit `None` (sends JSON `null`, clearing a nullable field). Standardizes the SDK on a single `Omit` sentinel (previously an internal `NotGiven`).
- Add `verify.*` webhook event types and payloads.
- Internal improvements.

## 0.12.2

- The verification terminal reason is now the named type `VerificationTerminalReason`, carrying its known values, rather than a bare string.
- Internal improvements.
- Stats `period.grain` is now typed as a shared `StatsGrain` (`day` | `hour`) instead of a plain string. No wire or behavioural change.

## 0.12.1

- Resource and package docstrings now describe behavior only.

## 0.12.0

- Agent mailboxes (inbox.ai): client.mailbox, client.mailbox_receive_rule, client.mailbox_thread, client.mailbox_thread_message
- Internal improvements.

## 0.11.0

- Add the `rejected` WhatsApp message delivery status, returned when the recipient is on the workspace's suppression list.
- Add the `whatsapp.rejected` webhook event, delivered when Bird rejects a WhatsApp message before sending because the recipient is on the workspace's suppression list.
- Rename voice call webhook event types from voice.call.* to voice_call.* (single-dot resource convention; events were never emitted, so no delivered payload changes)

## 0.10.0

- Add sms.tfn_verification webhook event types
- Add email statistics reads under `email.stats`: the period summary, the daily and hourly time series, and the dimension breakdowns (by tag, category, sending IP, sending domain, recipient domain, mailbox provider, mailbox-provider region, template, location, client, bounce code, complaint type, and broadcast).
- **Breaking:** the Realtime webhook event type `realtime.subscription_count` is now `realtime.connection_count`, matching Bird's Realtime vocabulary (per channel it counts connections — one connection cannot subscribe twice). Realtime is in early access; the old event type had no GA consumers.
- Operations and fields now document their units, defaults, omission behavior, and per-value status meanings. Several descriptions were corrected to match actual behavior, including engagement-rate denominators, suppression prefix matching, and stored-content retention.
- Internal improvements.
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
