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
        parameters={
            "title": "Welcome",
            "offer": "OCTOBER20",
            "discount": 20,
            "featured": False,
        },
    )
    print(broadcast.id, broadcast.status)


def broadcasts_get() -> None:
    broadcast = client.broadcasts.get("eb_01krdgeqcxet5s7t44vh8rt9mg")
    print(broadcast.status, broadcast.sent_count, broadcast.delivered_count)


def broadcasts_update() -> None:
    broadcast = client.broadcasts.update(
        "eb_01krdgeqcxet5s7t44vh8rt9mg",
        template="emt_01krdgeqcxet5s7t44vh8rt9mg",
        parameters={},
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


def broadcasts_validate() -> None:
    template = {
        "parameters": {
            "title": "Welcome",
            "offer": "OCTOBER20",
            "discount": 20,
            "featured": False,
        }
    }
    result = client.broadcasts.validate("eb_01krdgeqcxet5s7t44vh8rt9mg", template=template)
    print(result.ready_for_admission, result.problems)


def broadcasts_preview() -> None:
    template = {
        "parameters": {
            "title": "Welcome",
            "offer": "OCTOBER20",
            "discount": 20,
            "featured": False,
        }
    }
    contact_id = "con_01krdgeqcxet5s7t44vh8rt9mg"
    preview = client.broadcasts.preview(
        "eb_01krdgeqcxet5s7t44vh8rt9mg", template=template, contact_id=contact_id
    )
    print(preview.subject, preview.preview_fingerprint)


def broadcasts_test() -> None:
    template = {
        "parameters": {
            "title": "Welcome",
            "offer": "OCTOBER20",
            "discount": 20,
            "featured": False,
        }
    }
    contact_id = "con_01krdgeqcxet5s7t44vh8rt9mg"
    preview = client.broadcasts.preview(
        "eb_01krdgeqcxet5s7t44vh8rt9mg", template=template, contact_id=contact_id
    )
    accepted = client.broadcasts.test(
        "eb_01krdgeqcxet5s7t44vh8rt9mg",
        template=template,
        contact_id=contact_id,
        to="member@example.com",
        preview_fingerprint=preview.preview_fingerprint,
        options={"idempotency_key": "broadcast-preview-intent-1"},
    )
    print(accepted.id, accepted.status)


def email_template_parameters() -> None:
    discovery = client.email.templates.parameters("emt_01krdgeqcxet5s7t44vh8rt9mg")
    print(discovery.parameters, discovery.variables)
