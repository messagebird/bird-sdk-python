# Bird Python SDK

The official Python SDK for the [Bird](https://bird.com) email platform.

> **Status:** in development. The PyPI distribution name is `messagebird-sdk`; the import package is `bird`.

Requires Python 3.10+.

## Install

```bash
pip install messagebird-sdk      # or: uv add messagebird-sdk
```

> This SDK is generated from Bird's public OpenAPI bundle inside Bird's internal monorepo, which is the single source of truth; this repository tracks tagged releases. Generation runs in the monorepo, so `make generate` won't work from a clone here — see [CONTRIBUTING.md](./CONTRIBUTING.md).

## Quickstart

<!-- bird:snippet quickstart-email -->

```python
from bird import APIError, Bird

with Bird() as client:
    try:
        message = client.email.send(
            from_={"email": "onboarding@messagebird.dev", "name": "Bird"},
            to=["delivered@messagebird.dev"],
            subject="Hello from Bird",
            html="<p>My first Bird email.</p>",
        )
        print(message.id, message.status)
    except APIError as err:
        print("send failed:", err)
```

`api_key` and `base_url` fall back to the `BIRD_API_KEY` / `BIRD_BASE_URL` environment variables, so `Bird()` with no arguments works when they are set. Use the client as a context manager (`with Bird(...) as client:`) to close the underlying HTTP connection pool.

## Email

```python
# Send
message = client.email.send(from_="hi@acme.com", to=["c@x.com"], subject="Hi", text="hello")

# Fetch
message = client.email.get("em_01krd…")

# List — iterating the page auto-paginates across cursors
for message in client.email.list(status="delivered"):
    print(message.id, message.status)
```

### Client-wide email defaults

Defaults fill any unset `send` field; a per-send value always wins.

```python
client = Bird(
    api_key="bk_eu1_...",
    email_defaults={"from_": "noreply@acme.com", "reply_to": ["support@acme.com"]},
)
client.email.send(to=["c@x.com"], subject="Receipt", text="…")  # uses noreply@acme.com
```

## Webhooks

```python
from bird import Bird, WebhookVerificationError

client = Bird(api_key="bk_eu1_...", webhook_secret="whsec_...")

# In your web handler — pass the RAW request body (bytes) and the request headers
try:
    event = client.webhooks.unwrap(request.body, request.headers)
except WebhookVerificationError:
    return Response(status=400)

if event.root.type == "email.delivered":
    print("delivered:", event.root.data.message_id)
```

> Endpoint management (registering/listing webhook endpoints) is not in this release; it returns once the delivery substrate stabilises.

## Errors

Every failure raises a typed exception rooted at `BirdError`. `APIError` covers anything that goes wrong issuing a request — including transport failures — so a single `except APIError` is enough; `APIStatusError` carries the HTTP `status_code`.

<!-- bird:snippet email.errors -->

```python
from bird import APIStatusError, RateLimitError, ValidationError

try:
    client.email.send(
        from_={"email": "onboarding@messagebird.dev", "name": "Bird"},
        to=["delivered@messagebird.dev"],
        subject="Hello from Bird",
        text="My first Bird email.",
    )
except RateLimitError as err:
    print("rate limited; retry after", err.retry_after)
except ValidationError as err:
    print(err.status_code, err.details)
except APIStatusError as err:
    print(err.status_code, err.code, err.request_id)
```

Transient failures (timeouts, 429, 5xx) retry automatically with jittered backoff that honors `Retry-After`; a mutation reuses one idempotency key across attempts, so a retried write never double-applies.

## Raw response

Reach the status, headers, and `request_id` alongside the parsed model:

```python
raw = client.email.with_raw_response.send(from_="hi@acme.com", to=["c@x.com"], subject="Hi", text="…")
print(raw.status_code, raw.request_id)
message = raw.parse()
```

## Async

`AsyncBird` mirrors `Bird` method-for-method — `await` each call and `async for` over a list:

```python
import asyncio
from bird import AsyncBird

async def main() -> None:
    async with AsyncBird(api_key="bk_eu1_...") as client:
        await client.email.send(from_="hi@acme.com", to=["c@x.com"], subject="Hi", text="hello")
        async for message in client.email.list(status="delivered"):
            print(message.id)

asyncio.run(main())
```

## Configuration

| Option                   | Description                                                                    |
| ------------------------ | ------------------------------------------------------------------------------ |
| `api_key`                | API key; falls back to `BIRD_API_KEY`.                                         |
| `region` / `base_url`    | Region (or explicit base URL); falls back to the key prefix / `BIRD_BASE_URL`. |
| `timeout`, `max_retries` | Request timeout and retry budget; overridable per call via `options`.          |
| `webhook_secret`         | Signing secret for `webhooks.unwrap`.                                          |
| `email_defaults`         | Client-wide `send` defaults.                                                   |
| `http_client`            | Inject your own `httpx.Client` / `AsyncClient`.                                |

`client.with_options(...)` derives a new client (reusing the connection pool); every method also takes a trailing `options` for per-call `timeout` / `max_retries` / `idempotency_key` / `extra_headers`.

## Escape hatch

Any endpoint outside the typed surface is reachable through the verb methods, with the same auth, retries, and idempotency:

<!-- bird:snippet client.verbs -->

```python
from bird import EmailMessage

message = client.get("/v1/email/messages/em_01krd...", cast_to=EmailMessage)
client.post("/v1/some/new/endpoint", body={"key": "value"})
```

## Design

The wire models are generated from the OpenAPI spec into `bird._generated`; this package is the hand-written idiomatic layer on top.
