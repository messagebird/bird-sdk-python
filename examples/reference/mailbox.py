"""Example source for the generated mailbox methods.

Each bird:snippet region is harvested for the docs site + README; the keys match
the surface catalog (mailbox.<leaf>). Hand-written and type-checked (pyright
includes examples/); nothing regenerates over it. The one override method
(mailbox.compose) keeps its example inline in resources/mailbox.py.
"""

from bird import Bird

client = Bird()


def mailbox_list() -> None:
    for mailbox in client.mailbox.list():
        print(mailbox.id, mailbox.address)


def mailbox_create() -> None:
    mailbox = client.mailbox.create(display_name="Acme Support")
    print(mailbox.id)


def mailbox_get() -> None:
    mailbox = client.mailbox.get("mbx_01krdgeqcxet5s7t44vh8rt9mg")
    print(mailbox.address)


def mailbox_delete() -> None:
    client.mailbox.delete("mbx_01krdgeqcxet5s7t44vh8rt9mg")


def mailbox_restore() -> None:
    mailbox = client.mailbox.restore("mbx_01krdgeqcxet5s7t44vh8rt9mg")
    print(mailbox.id)


def mailbox_resume() -> None:
    mailbox = client.mailbox.resume("mbx_01krdgeqcxet5s7t44vh8rt9mg")
    print(mailbox.state)


def mailbox_stats() -> None:
    stats = client.mailbox.stats("mbx_01krdgeqcxet5s7t44vh8rt9mg")
    print(stats.summary)


def mailbox_labels() -> None:
    labels = client.mailbox.labels("mbx_01krdgeqcxet5s7t44vh8rt9mg")
    for label in labels.data:
        print(label.name)


def mailbox_update() -> None:
    mailbox = client.mailbox.update(
        "mbx_01krdgeqcxet5s7t44vh8rt9mg", display_name="Billing"
    )
    print(mailbox.display_name)
