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


def whatsapp_numbers_list() -> None:
    for number in client.whatsapp.numbers.list(status=["connected"]):
        print(number.id, number.phone_number, number.status)


def whatsapp_numbers_get() -> None:
    number = client.whatsapp.numbers.get("wan_01krdgeqcxet5s7t44vh8rt9mg")
    print(number.status, number.quality_rating, number.messaging_limit)


def whatsapp_numbers_profile_get() -> None:
    profile = client.whatsapp.numbers.profile.get("wan_01krdgeqcxet5s7t44vh8rt9mg")
    print(profile.display_name, profile.description)


def whatsapp_numbers_list_events() -> None:
    for event in client.whatsapp.numbers.list_events("wan_01krdgeqcxet5s7t44vh8rt9mg"):
        print(event.created_at, event.type, event.summary)


def whatsapp_business_accounts_list() -> None:
    for account in client.whatsapp.business_accounts.list():
        print(account.id, account.name, account.status)


def whatsapp_business_accounts_get() -> None:
    account = client.whatsapp.business_accounts.get("waa_01krdgeqcxet5s7t44vh8rt9mg")
    print(account.account_review_status, account.business_verification_status)

def whatsapp_stats_summary() -> None:
    summary = client.whatsapp.stats.summary(
        from_="2026-08-01", to="2026-08-31", timezone="Europe/Amsterdam"
    )
    print(summary.delivery, summary.latency)


def whatsapp_stats_daily() -> None:
    stats = client.whatsapp.stats.daily(from_="2026-08-01", to="2026-08-31")
    for point in stats.data or []:
        print(point.bucket, point.delivery)


def whatsapp_stats_hourly() -> None:
    stats = client.whatsapp.stats.hourly(from_="2026-08-30T00:00:00Z", to="2026-08-31T00:00:00Z")
    for point in stats.data or []:
        print(point.bucket, point.delivery)


def whatsapp_stats_by_error_code() -> None:
    stats = client.whatsapp.stats.by_error_code(from_="2026-08-01", to="2026-08-31")
    for row in stats.data or []:
        print(row.error_code, row.count)


def whatsapp_stats_by_template() -> None:
    stats = client.whatsapp.stats.by_template(from_="2026-08-01", to="2026-08-31")
    for row in stats.data or []:
        print(row.template_id, row.delivery)


def whatsapp_stats_by_template_category() -> None:
    stats = client.whatsapp.stats.by_template_category(from_="2026-08-01", to="2026-08-31")
    for row in stats.data or []:
        print(row.category, row.delivery)


def whatsapp_stats_by_tag() -> None:
    stats = client.whatsapp.stats.by_tag(from_="2026-08-01", to="2026-08-31")
    for row in stats.data or []:
        print(row.tag, row.delivery)


def whatsapp_stats_by_phone_number() -> None:
    stats = client.whatsapp.stats.by_phone_number(from_="2026-08-01", to="2026-08-31")
    for row in stats.data or []:
        print(row.phone_number, row.delivery)


def whatsapp_stats_by_country() -> None:
    stats = client.whatsapp.stats.by_country(from_="2026-08-01", to="2026-08-31")
    for row in stats.data or []:
        print(row.country, row.delivery)


def whatsapp_stats_inbound_summary() -> None:
    summary = client.whatsapp.stats.inbound.summary(from_="2026-05-01", to="2026-05-31")
    print(summary.received)


def whatsapp_stats_inbound_daily() -> None:
    stats = client.whatsapp.stats.inbound.daily(from_="2026-05-01", to="2026-05-31")
    for point in stats.data or []:
        print(point.bucket, point.received)


def whatsapp_stats_inbound_hourly() -> None:
    stats = client.whatsapp.stats.inbound.hourly(
        from_="2026-05-30T00:00:00Z", to="2026-05-31T00:00:00Z"
    )
    for point in stats.data or []:
        print(point.bucket, point.received)


def whatsapp_stats_inbound_by_phone_number() -> None:
    stats = client.whatsapp.stats.inbound.by_phone_number(from_="2026-05-01", to="2026-05-31")
    for row in stats.data or []:
        print(row.phone_number, row.received)
