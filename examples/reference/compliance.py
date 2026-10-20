"""Example source for the generated compliance methods.

Each bird:snippet region is harvested for the docs site + README; the keys match
the surface catalog (compliance_<resource>.<leaf>). Hand-written and type-checked
(pyright includes examples/); nothing regenerates over it.
"""

from bird import Bird

client = Bird()


def compliance_requirements_get() -> None:
    requirement = client.compliance_requirements.get(
        subject_kind="number",
        subject_id="nda_01krdgeqcxet5s7t44vh8rt9mg",
        country_code="US",
    )
    for field in requirement.fields or []:
        print(field.key, field.state)


def compliance_submissions_create() -> None:
    submission = client.compliance_submissions.create(
        subject_kind="number",
        subject_id="nda_01krdgeqcxet5s7t44vh8rt9mg",
        program="local",
        country_code="US",
        answers=[
            {"key": "legal_entity_name", "value": "Goldcrest Communications Inc"},
            {"key": "business_registration_number", "value": "90012768"},
        ],
    )
    # There is no draft: the answers are filed for review as of this call.
    print(submission.id, submission.satisfied)


def compliance_submissions_get() -> None:
    submission = client.compliance_submissions.get("csb_01krdgeqcxet5s7t44vh8rt9mg")
    for item in submission.items or []:
        print(item.key, item.state, item.reason or "")


def compliance_submissions_resupply() -> None:
    submission = client.compliance_submissions.resupply(
        "csb_01krdgeqcxet5s7t44vh8rt9mg",
        answers=[{"key": "business_registration_number", "value": "90012769"}],
    )
    print(submission.satisfied)


def compliance_attachments_list() -> None:
    for attachment in client.compliance_attachments.list():
        print(attachment.id, attachment.filename, attachment.status)


def compliance_attachments_delete() -> None:
    # Once a registration cites the attachment, this returns a 409.
    client.compliance_attachments.delete("tca_01krdgeqcxet5s7t44vh8rt9mg")


def compliance_identities_list() -> None:
    for identity in client.compliance_identities.list():
        print(identity.id, identity.name)


def compliance_identities_get() -> None:
    identity = client.compliance_identities.get("cid_01krdgeqcxet5s7t44vh8rt9mg")
    print(identity.name, list(identity.answers))


def compliance_identities_create() -> None:
    client.compliance_identities.create(name="Goldcrest")


def compliance_identities_update() -> None:
    client.compliance_identities.update("cid_01krdgeqcxet5s7t44vh8rt9mg", name="Goldcrest SAS")


def compliance_identities_delete() -> None:
    client.compliance_identities.delete("cid_01krdgeqcxet5s7t44vh8rt9mg")


def sms_senders_list() -> None:
    client.sms_senders.list()


def sms_senders_get() -> None:
    client.sms_senders.get("snd_01krdgeqcxet5s7t44vh8rt9mg")


def sms_senders_create() -> None:
    client.sms_senders.create(type="alpha", sender="GOLDCREST")


def sms_sender_requirements_list() -> None:
    client.sms_sender_requirements.list("snd_01krdgeqcxet5s7t44vh8rt9mg")


def sms_sender_registrations_create() -> None:
    client.sms_sender_registrations.create("snd_01krdgeqcxet5s7t44vh8rt9mg", country_code="NL")


def billing_prices_resolve() -> None:
    import os
    # Use a delegated user OAuth token with org:billing:read in its issuing region.
    client = Bird(api_key=os.environ["BIRD_OAUTH_ACCESS_TOKEN"], region="eu1")
    client.billing_prices.resolve(product_slug="sms_sender_registration", dimensions={"country_code": "NL", "sender_type": "alphanumeric"})


def billing_wallets_list() -> None:
    import os
    # Use a delegated user OAuth token with org:billing:read in its issuing region.
    client = Bird(api_key=os.environ["BIRD_OAUTH_ACCESS_TOKEN"], region="eu1")
    client.billing_wallets.list()
