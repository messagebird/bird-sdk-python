"""Example source for the generated whatsapp methods.

Each bird:snippet region is harvested for the docs site + README, and the
surfacegen Python writer injects it (marker-free) as the docstring example on
the generated method. Hand-written and type-checked (pyright includes
examples/); nothing regenerates over it. ``send`` stays hand-written, so its
example stays inline in src/bird/resources/whatsapp.py.
"""

from bird import Bird

client = Bird()


def whatsapp_get() -> None:
    msg = client.whatsapp.get("wa_abc123")
    print(msg.id, msg.status)


def whatsapp_list() -> None:
    for msg in client.whatsapp.list(status=["delivered"]):
        print(msg.id, msg.status)


def whatsapp_list_events() -> None:
    events = client.whatsapp.list_events("wa_abc123")
    for event in events.data:
        print(event.type, event.occurred_at)
