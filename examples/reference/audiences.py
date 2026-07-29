"""Example source for the generated audiences methods.

Each bird:snippet region is harvested for the docs site + README; the keys match
the surface catalog (audiences.<leaf>). Hand-written and type-checked (pyright
includes examples/); nothing regenerates over it.
"""

from bird import Bird

client = Bird()


def audiences_create() -> None:
    audience = client.audiences.create(name="Newsletter subscribers")
    print(audience.id, audience.name)


def audiences_get() -> None:
    audience = client.audiences.get("adn_01krdgeqcxet5s7t44vh8rt9mg")
    print(audience.name)


def audiences_update() -> None:
    audience = client.audiences.update("adn_01krdgeqcxet5s7t44vh8rt9mg", name="Renamed")
    print(audience.name)


def audiences_delete() -> None:
    client.audiences.delete("adn_01krdgeqcxet5s7t44vh8rt9mg")


def audiences_list() -> None:
    for audience in client.audiences.list():
        print(audience.id, audience.name)


def audiences_list_contacts() -> None:
    for member in client.audiences.list_contacts("adn_01krdgeqcxet5s7t44vh8rt9mg"):
        print(member.contact.email, member.joined_at)


def audiences_add_contacts() -> None:
    client.audiences.add_contacts(
        "adn_01krdgeqcxet5s7t44vh8rt9mg", contact_ids=["con_01krdgeqcxet5s7t44vh8rt9mg"],
    )


def audiences_remove_contacts() -> None:
    client.audiences.remove_contacts(
        "adn_01krdgeqcxet5s7t44vh8rt9mg", contact_ids=["con_01krdgeqcxet5s7t44vh8rt9mg"],
    )


def audiences_remove_contact() -> None:
    client.audiences.remove_contact(
        "adn_01krdgeqcxet5s7t44vh8rt9mg", "con_01krdgeqcxet5s7t44vh8rt9mg",
    )
