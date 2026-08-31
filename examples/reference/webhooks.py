"""Example source for the generated webhook methods.

Each bird:snippet region is harvested for the docs site + README; the keys match
the surface catalog (webhook.<leaf>). Hand-written and type-checked (pyright
includes examples/); nothing regenerates over it.
"""

from bird import Bird

client = Bird()


def webhook_create() -> None:
    created = client.webhooks.create(
        url="https://acme.com/hooks/bird",
        events=["email.delivered", "email.bounced"],
        description="Delivery pipeline",
    )
    print(created.id, created.secret)


def webhook_list() -> None:
    for endpoint in client.webhooks.list():
        print(endpoint.id, endpoint.url, endpoint.status)


def webhook_get() -> None:
    endpoint = client.webhooks.get("whk_01krdgeqcxet5s7t44vh8rt9mg")
    print(endpoint.url, endpoint.events)


def webhook_update() -> None:
    endpoint = client.webhooks.update(
        "whk_01krdgeqcxet5s7t44vh8rt9mg",
        events=["email.delivered"],
    )
    print(endpoint.events)


def webhook_test() -> None:
    result = client.webhooks.test(
        "whk_01krdgeqcxet5s7t44vh8rt9mg",
        event_type="email.delivered",
    )
    print(result.status)


def webhook_attempts() -> None:
    attempts = client.webhooks.attempts("whk_01krdgeqcxet5s7t44vh8rt9mg")
    for attempt in attempts.data:
        print(attempt.status, attempt.response_status_code)


def webhook_rotate_secret() -> None:
    rotated = client.webhooks.rotate_secret("whk_01krdgeqcxet5s7t44vh8rt9mg")
    print(rotated.secret)


def webhook_delete() -> None:
    client.webhooks.delete("whk_01krdgeqcxet5s7t44vh8rt9mg")
