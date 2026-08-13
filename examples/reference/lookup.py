"""Example source for the generated lookup methods.

Each bird:snippet region is harvested for the docs site + README; the keys match
the surface catalog (lookup.<leaf>). Hand-written and type-checked (pyright
includes examples/); nothing regenerates over it.
"""

from bird import Bird

client = Bird()


def lookup_email() -> None:
    answer = client.lookup.email(email="aisha.khan@example.com")
    # result is an open vocabulary; delivery_confidence is always comparable.
    print(answer.result, answer.delivery_confidence)


def lookup_phone_number() -> None:
    answer = client.lookup.phone_number(
        phone_number="+31612345678", type=["classification", "score"]
    )
    print(answer.country_code, answer.line_type)
    # Only a block whose status is ok carries a value, and only that one is billed.
    if answer.score is not None and answer.score.status == "ok":
        print(answer.score.value)
