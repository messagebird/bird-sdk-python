"""Example source for the preferences methods.

Each bird:snippet region is harvested for the docs site + README; the keys
match the surface catalog (preferences.<leaf>). Hand-written and type-checked
(pyright includes examples/); nothing regenerates over it.
"""

from bird import Bird

client = Bird()


def preferences_list() -> None:
    for preference in client.preferences.list(channel="email"):
        print(preference.id, preference.handle, preference.status)


def preferences_get() -> None:
    preference = client.preferences.get("prf_01krdgeqcxet5s7t44vh8rt9mg")
    print(preference.status, preference.coverage)


def preferences_create() -> None:
    result = client.preferences.create(
        channel="email",
        handle="jane@acme.com",
        status="granted",
        consented_at="2026-08-20T14:03:10Z",
        source="signup-form-v2",
    )
    if result.preference:
        print(result.applied, result.preference.id)


def preferences_delete() -> None:
    result = client.preferences.delete("prf_01krdgeqcxet5s7t44vh8rt9mg")
    if not result.applied and result.preference:
        print("refused, current statement:", result.preference.status)
