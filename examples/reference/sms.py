"""Example source for the generated sms methods.

Each bird:snippet region is harvested for the docs site + README, and the
surfacegen Python writer injects it (marker-free) as the docstring example on
the generated method. Hand-written and type-checked (pyright includes
examples/); nothing regenerates over it. The sends stay hand-written, so their
examples stay inline in src/bird/resources/sms.py.
"""

from bird import Bird

client = Bird()


def sms_get() -> None:
    message = client.sms.get("sms_abc123")
    print(message.id, message.status)


def sms_list() -> None:
    for message in client.sms.list(direction="outbound"):
        print(message.id, message.status)
