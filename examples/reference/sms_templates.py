"""Example source for the generated sms_templates methods.

Each bird:snippet region is harvested for the docs site + README, and the
surfacegen Python writer injects it (marker-free) as the docstring example on
the generated method. Hand-written and type-checked (pyright includes
examples/); nothing regenerates over it.
"""

from bird import Bird

client = Bird()


def sms_templates_list() -> None:
    for template in client.sms_templates.list(scope="system"):
        print(template.id, template.slug)


def sms_templates_get() -> None:
    template = client.sms_templates.get("bird_otp_verification")
    print(template.default_language, template.live_version_id)


def sms_templates_versions_list() -> None:
    for version in client.sms_templates.versions.list("bird_otp_verification"):
        print(version.id, version.version_number)


def sms_templates_versions_get() -> None:
    version = client.sms_templates.versions.get(
        "bird_otp_verification", "smv_01ky4x8e4genzb7way45txfkm1"
    )
    print(version.id, list(version.languages))


def sms_templates_versions_languages_list() -> None:
    languages = client.sms_templates.versions.languages.list(
        "bird_otp_verification", "smv_01ky4x8e4genzb7way45txfkm1"
    )
    for language in languages.data:
        print(language.language, language.revision)


def sms_templates_versions_languages_get() -> None:
    language = client.sms_templates.versions.languages.get(
        "bird_otp_verification", "smv_01ky4x8e4genzb7way45txfkm1", "en"
    )
    print(language.language, language.text)
