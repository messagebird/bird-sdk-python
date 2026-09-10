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


def whatsapp_mark_read() -> None:
    ack = client.whatsapp.mark_read("wam_01krdgeqcxet5s7t44vh8rt9mg", typing_indicator=True)
    print(ack.typing_indicator)


def whatsapp_reaction_set() -> None:
    reaction = client.whatsapp.reaction.set("wam_01krdgeqcxet5s7t44vh8rt9mg", emoji="\U0001f44d")
    print(reaction.id, reaction.emoji)


def whatsapp_reaction_remove() -> None:
    client.whatsapp.reaction.remove("wam_01krdgeqcxet5s7t44vh8rt9mg")


def whatsapp_reaction_list_events() -> None:
    for event in client.whatsapp.reaction.list_events("wam_01krdgeqcxet5s7t44vh8rt9mg"):
        print(event.id, event.emoji, event.status)


def whatsapp_templates_list() -> None:
    for tpl in client.whatsapp.templates.list():
        print(tpl.slug, tpl.status)


def whatsapp_templates_get() -> None:
    tpl = client.whatsapp.templates.get("bird_otp")
    print(tpl.default_language, tpl.available_languages)


def whatsapp_templates_versions_list() -> None:
    for version in client.whatsapp.templates.versions.list("bird_otp"):
        print(version.id, version.version_number)


def whatsapp_templates_versions_get() -> None:
    version = client.whatsapp.templates.versions.get("bird_otp", "wav_01ky4x8e4genzb7way45txfkm1")
    print(version.id, list(version.languages))


def whatsapp_templates_versions_languages_list() -> None:
    languages = client.whatsapp.templates.versions.languages.list(
        "bird_otp", "wav_01ky4x8e4genzb7way45txfkm1"
    )
    for language in languages.data:
        print(language.language, language.status)


def whatsapp_templates_versions_languages_get() -> None:
    language = client.whatsapp.templates.versions.languages.get(
        "bird_otp", "wav_01ky4x8e4genzb7way45txfkm1", "nl-BE"
    )
    for component in language.components:
        print(component.type)
