"""Example source for the generated verify methods.

Each bird:snippet region is harvested for the docs site + README; the keys match
the surface catalog (verify.verifications.<leaf>). Hand-written and type-checked
(pyright includes examples/); nothing regenerates over it.
"""

from bird import Bird

client = Bird()


def verify_verifications_create() -> None:
    verification = client.verify.verifications.create(to={"phone_number": "+15551234567"})
    print(verification.id, verification.status)


def verify_verifications_check() -> None:
    result = client.verify.verifications.check(
        to={"phone_number": "+15551234567"}, code="123456"
    )
    print(result.success)
