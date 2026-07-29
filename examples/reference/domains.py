"""Example source for the generated domains methods.

Each bird:snippet region is harvested for the docs site + README; the keys match
the surface catalog (domains.<leaf>). Hand-written and type-checked (pyright
includes examples/); nothing regenerates over it. The override methods —
domains.create and domains.update — keep their examples inline in
src/bird/resources/domains.py, since nothing regenerates over a hand method.
"""

from bird import Bird

client = Bird()


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
