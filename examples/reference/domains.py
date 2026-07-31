"""Example source for the generated domains methods.

Each bird:snippet region is harvested for the docs site + README; the keys match
the surface catalog (domains.<leaf>). Hand-written and type-checked (pyright
includes examples/); nothing regenerates over it.
"""

from bird import Bird

client = Bird()


def domains_create() -> None:
    domain = client.domains.create(domain="mail.acme.com")
    print(domain.id, domain.status)


def domains_update() -> None:
    domain = client.domains.update(
        "dom_01krdgeqcxet5s7t44vh8rt9mg",
        settings={"click_tracking": True, "open_tracking": True},
        tracking={"name": "links"},
    )
    print(domain.id)


def domains_get() -> None:
    domain = client.domains.get("dom_01krdgeqcxet5s7t44vh8rt9mg")
    print(domain.domain)


def domains_verify() -> None:
    domain = client.domains.verify("dom_01krdgeqcxet5s7t44vh8rt9mg")
    print(domain.status)


def domains_delete() -> None:
    client.domains.delete("dom_01krdgeqcxet5s7t44vh8rt9mg")


def domains_list() -> None:
    for domain in client.domains.list():
        print(domain.id, domain.status)
