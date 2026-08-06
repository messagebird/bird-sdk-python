"""Example source for the generated contacts methods.

Each bird:snippet region is harvested for the docs site + README; the keys match
the surface catalog (contacts.<leaf>). Hand-written and type-checked (pyright
includes examples/); nothing regenerates over it.
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


def contacts_update() -> None:
    contact = client.contacts.update("con_01krdgeqcxet5s7t44vh8rt9mg", first_name="Jane")
    print(contact.first_name)


def contacts_batch() -> None:
    result = client.contacts.batch(contacts=[{"email": "jane@acme.com", "first_name": "Jane"}])
    for item in result.data:
        print(item.entry.email, item.status)


def contacts_list() -> None:
    for contact in client.contacts.list(q="acme.com"):
        print(contact.id, contact.email)
