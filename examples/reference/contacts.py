"""Example source for the generated contacts methods.

Each bird:snippet region is harvested for the docs site + README; the keys match
the surface catalog (contacts.<leaf>). Hand-written and type-checked (pyright
includes examples/); nothing regenerates over it. The override methods —
contacts.update/batch/list — keep their examples inline in
src/bird/resources/contacts.py, since nothing regenerates over a hand method.
"""

from bird import Bird

client = Bird()


def contacts_create() -> None:
    contact = client.contacts.create(email="jane@acme.com", first_name="Jane")
    print(contact.id, contact.email)


def contacts_get() -> None:
    contact = client.contacts.get("con_01krdgeqcxet5s7t44vh8rt9mg")
    print(contact.email)


def contacts_delete() -> None:
    client.contacts.delete("con_01krdgeqcxet5s7t44vh8rt9mg")


def contacts_list() -> None:
    for contact in client.contacts.list(q="acme.com"):
        print(contact.id, contact.email)
