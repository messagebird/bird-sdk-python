"""Example source for the generated contact_properties methods.

Each bird:snippet region is harvested for the docs site + README; the keys match
the surface catalog (contact_properties.<leaf>). Hand-written and type-checked
(pyright includes examples/); nothing regenerates over it. The override methods —
contact_properties.create/update — keep their examples inline in
src/bird/resources/contact_properties.py, since nothing regenerates over a hand
method.
"""

from bird import Bird

client = Bird()


def contact_properties_create() -> None:
    prop = client.contact_properties.create(key="plan", type="string")
    print(prop.id, prop.key)


def contact_properties_update() -> None:
    prop = client.contact_properties.update("prp_01krdgeqcxet5s7t44vh8rt9mg", fallback_value="free")
    print(prop.fallback_value)


def contact_properties_get() -> None:
    prop = client.contact_properties.get("prp_01krdgeqcxet5s7t44vh8rt9mg")
    print(prop.key, prop.type)


def contact_properties_list() -> None:
    for prop in client.contact_properties.list():
        print(prop.id, prop.key)


def contact_properties_archive() -> None:
    prop = client.contact_properties.archive("prp_01krdgeqcxet5s7t44vh8rt9mg")
    print(prop.key, prop.archived)


def contact_properties_unarchive() -> None:
    prop = client.contact_properties.unarchive("prp_01krdgeqcxet5s7t44vh8rt9mg")
    print(prop.archived)
