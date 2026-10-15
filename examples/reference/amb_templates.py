"""Example source for the generated amb_templates methods.

Each bird:snippet region is harvested for the docs site + README, and the
surfacegen Python writer injects it (marker-free) as the docstring example on
the generated method. Hand-written and type-checked (pyright includes
examples/); nothing regenerates over it.
"""

from bird import Bird

client = Bird()


def amb_templates_list() -> None:
    for template in client.amb.templates.list(scope="system"):
        print(template.id, template.slug)


def amb_templates_get() -> None:
    template = client.amb.templates.get("bird_order_update")
    print(template.default_language, template.live_version_id)


def amb_templates_versions_list() -> None:
    for version in client.amb.templates.versions.list("bird_order_update"):
        print(version.id, version.version_number)


def amb_templates_versions_get() -> None:
    version = client.amb.templates.versions.get(
        "bird_order_update", "amv_01ky4x8e4genzb7way45txfkm1"
    )
    print(version.id, list(version.languages))


def amb_templates_versions_languages_list() -> None:
    languages = client.amb.templates.versions.languages.list(
        "bird_order_update", "amv_01ky4x8e4genzb7way45txfkm1"
    )
    for language in languages.data:
        print(language.language, language.revision)


def amb_templates_versions_languages_get() -> None:
    language = client.amb.templates.versions.languages.get(
        "bird_order_update", "amv_01ky4x8e4genzb7way45txfkm1", "en"
    )
    print(language.language, language.content)
