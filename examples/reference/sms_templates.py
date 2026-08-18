"""Example source for the generated sms_templates methods.

Each bird:snippet region is harvested for the docs site + README, and the
surfacegen Python writer injects it (marker-free) as the docstring example on
the generated method. Hand-written and type-checked (pyright includes
examples/); nothing regenerates over it.
"""

from bird import Bird

client = Bird()


def sms_templates_list() -> None:
    templates = client.sms_templates.list(scope="system")
    for template in templates.data:
        print(template.id, template.slug)


def sms_templates_get() -> None:
    template = client.sms_templates.get("bird_otp_verification")
    print(template.body, template.variables)
