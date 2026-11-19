"""Example source for the labels methods.

Each bird:snippet region is harvested for the docs site + README; the keys
match the surface catalog (labels.<leaf>). Hand-written and type-checked
(pyright includes examples/); nothing regenerates over it.
"""

from bird import Bird

client = Bird()


def labels_list() -> None:
    labels = client.labels.list()
    for label in labels.data:
        print(label.id, label.name)


def labels_get() -> None:
    label = client.labels.get("lbl_01krdgeqcxet5s7t44vh8rt9mg")
    print(label.name, label.description)


def labels_create() -> None:
    label = client.labels.create(
        name="refund-request",
        color="#E5484D",
        description="The customer asks for their money back.",
    )
    print(label.id)


def labels_update() -> None:
    label = client.labels.update(
        "lbl_01krdgeqcxet5s7t44vh8rt9mg",
        name="refund",
        color=None,
    )
    print(label.name)


def labels_delete() -> None:
    client.labels.delete("lbl_01krdgeqcxet5s7t44vh8rt9mg")
