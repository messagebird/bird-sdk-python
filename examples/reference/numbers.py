"""Example source for the generated numbers methods.

Each bird:snippet region is harvested for the docs site + README; the keys match
the surface catalog (numbers.<leaf>). Hand-written and type-checked (pyright
includes examples/); nothing regenerates over it.
"""

from bird import Bird

client = Bird()


def numbers_available_list() -> None:
    # The search is always country-scoped, so country_code is required.
    page = client.numbers.available.list(country_code="GB", capabilities=["sms", "voice"])
    for candidate in page.data:
        print(candidate.number, candidate.number_type)


def numbers_available_get() -> None:
    # A number a carrier supplies is only on sale while the carrier still has
    # it, so a 404 here means someone else took it.
    candidate = client.numbers.available.get("+447700900201")
    print(candidate.country_code, candidate.capabilities)


def numbers_orders_create() -> None:
    order = client.numbers.orders.create(number="+447700900201")
    # Most orders finish inside the request. One that has to wait on a carrier
    # comes back without a number_id. Poll it until completed or failed.
    if order.status == "completed":
        print("allocated as", order.number_id)
    else:
        print("still", order.status, "; poll", order.id)


def numbers_orders_get() -> None:
    order = client.numbers.orders.get("nor_01krdgeqcxet5s7t44vh8rt9mg")
    # failure_reason says what went wrong, and only ever on a failed order.
    print(order.status, order.failure_reason or "")


def numbers_orders_list() -> None:
    page = client.numbers.orders.list(status="failed")
    for order in page.data:
        print(order.number, order.failure_reason or "")


def numbers_list() -> None:
    for allocated in client.numbers.list(country_code="GB"):
        # kind tells a number you bought from one Bird manages for several
        # workspaces.
        print(allocated.number, allocated.kind, allocated.status)


def numbers_get() -> None:
    allocated = client.numbers.get("nda_01krdgeqcxet5s7t44vh8rt9mg")
    # A country that asks for ownership paperwork answers here; most answer None.
    print(allocated.status, allocated.ownership or "no paperwork required")


def numbers_release() -> None:
    # Releasing stops the monthly charge and the number stops working for you.
    # Only a dedicated number can be released; a shared one answers E14002.
    client.numbers.release("nda_01krdgeqcxet5s7t44vh8rt9mg")
