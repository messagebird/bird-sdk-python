"""Example source for the generated mailbox_receive_rule methods.

Each bird:snippet region is harvested for the docs site + README; the keys match
the surface catalog (mailbox_receive_rule.<leaf>). Hand-written and type-checked
(pyright includes examples/); nothing regenerates over it.
"""

from bird import Bird

client = Bird()


def mailbox_receive_rule_list() -> None:
    for rule in client.mailbox_receive_rule.list("mbx_01krdgeqcxet5s7t44vh8rt9mg"):
        print(rule.id, rule.action)


def mailbox_receive_rule_create() -> None:
    rule = client.mailbox_receive_rule.create(
        "mbx_01krdgeqcxet5s7t44vh8rt9mg", action="block", entry="spam.example.com"
    )
    print(rule.id)


def mailbox_receive_rule_delete() -> None:
    client.mailbox_receive_rule.delete(
        "mbx_01krdgeqcxet5s7t44vh8rt9mg", "rrule_01krdgeqcxet5s7t44vh8rt9mg"
    )
