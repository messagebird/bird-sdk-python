"""Example source for the broadcasts methods.

Each bird:snippet region is harvested for the docs site + README; the keys match
the surface catalog (broadcasts.<leaf>). Hand-written and type-checked (pyright
includes examples/); nothing regenerates over it.
"""

from bird import Bird

client = Bird()


def broadcasts_create() -> None:
    broadcast = client.broadcasts.create(
        from_="newsletter@example.com",
        audience_id="adn_01krdgeqcxet5s7t44vh8rt9mg",
        template="emt_01krdgeqcxet5s7t44vh8rt9mg",
    )
    print(broadcast.id, broadcast.status)


def broadcasts_get() -> None:
    broadcast = client.broadcasts.get("eb_01krdgeqcxet5s7t44vh8rt9mg")
    print(broadcast.status, broadcast.sent_count, broadcast.delivered_count)


def broadcasts_update() -> None:
    broadcast = client.broadcasts.update(
        "eb_01krdgeqcxet5s7t44vh8rt9mg",
        template="emt_01krdgeqcxet5s7t44vh8rt9mg",
    )
    print(broadcast.status)


def broadcasts_delete() -> None:
    client.broadcasts.delete("eb_01krdgeqcxet5s7t44vh8rt9mg")


def broadcasts_list() -> None:
    for broadcast in client.broadcasts.list(status=["sent"]):
        print(broadcast.id, broadcast.status)


def broadcasts_send() -> None:
    broadcast = client.broadcasts.send("eb_01krdgeqcxet5s7t44vh8rt9mg")
    print(broadcast.status)


def broadcasts_cancel() -> None:
    broadcast = client.broadcasts.cancel("eb_01krdgeqcxet5s7t44vh8rt9mg")
    print(broadcast.status)


def broadcasts_send_quota() -> None:
    quota = client.broadcasts.send_quota("eb_01krdgeqcxet5s7t44vh8rt9mg")
    if quota.allowed < quota.recipients:
        print(quota.limited_by, "allowance covers only", quota.allowed)


def broadcasts_counts() -> None:
    counts = client.broadcasts.counts("eb_01krdgeqcxet5s7t44vh8rt9mg")
    print(counts.total, counts.addressable, counts.sendable)


def broadcasts_list_recipients() -> None:
    for recipient in client.broadcasts.list_recipients("eb_01krdgeqcxet5s7t44vh8rt9mg"):
        print(recipient.recipient, recipient.status)


def broadcasts_list_events() -> None:
    for event in client.broadcasts.list_events(
        "eb_01krdgeqcxet5s7t44vh8rt9mg", type="email.bounced"
    ):
        print(event.type, event.recipient_id, event.bounce_type)


def broadcasts_list_clicked_links() -> None:
    links = client.broadcasts.list_clicked_links("eb_01krdgeqcxet5s7t44vh8rt9mg")
    for link in links.data:
        print(link.url, link.click_count, link.recipient_count)
