"""Examples for generated contact_properties methods.

The snippet regions supply the documentation and generated method examples.
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
