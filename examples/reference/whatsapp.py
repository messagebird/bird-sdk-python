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


def whatsapp_groups_create() -> None:
    group = client.whatsapp.groups.create(
        whatsapp_number_id="wan_01krdgeqcxet5s7t44vh8rt9mg",
        subject="Norwood Fleet — Tuesday route",
    )
    print(group.id, group.status)  # pending; read it back for the invite link


def whatsapp_groups_list() -> None:
    for group in client.whatsapp.groups.list():
        print(group.id, group.subject, group.participant_count)


def whatsapp_groups_get() -> None:
    group = client.whatsapp.groups.get("wag_01krdgeqcxet5s7t44vh8rt9mg")
    print(group.status, group.invite_link)


def whatsapp_groups_update() -> None:
    group = client.whatsapp.groups.update(
        "wag_01krdgeqcxet5s7t44vh8rt9mg",
        subject="Norwood Fleet — Wednesday route",
    )
    print(group.last_operation)  # pending until WhatsApp reports back


def whatsapp_groups_delete() -> None:
    group = client.whatsapp.groups.delete("wag_01krdgeqcxet5s7t44vh8rt9mg")
    if group.last_operation:
        print(group.last_operation.status)  # pending until WhatsApp confirms it


def whatsapp_groups_invite_link_rotate() -> None:
    link = client.whatsapp.groups.invite_link.rotate("wag_01krdgeqcxet5s7t44vh8rt9mg")
    print(link.invite_link)  # every earlier link has stopped working


def whatsapp_groups_participants_remove() -> None:
    group = client.whatsapp.groups.participants.remove(
        "wag_01krdgeqcxet5s7t44vh8rt9mg",
        "BR.1566655121691972",
    )
    print(len(group.participants or []))


def whatsapp_groups_join_requests_list() -> None:
    for request in client.whatsapp.groups.join_requests.list("wag_01krdgeqcxet5s7t44vh8rt9mg"):
        print(request.id, request.bsuid)


def whatsapp_groups_join_requests_approve() -> None:
    result = client.whatsapp.groups.join_requests.approve(
        "wag_01krdgeqcxet5s7t44vh8rt9mg",
        join_request_ids=["wgj_01krdgeqcxet5s7t44vh8rt9mg"],
    )
    print(len(result.decided), len(result.failed))


def whatsapp_groups_join_requests_reject() -> None:
    result = client.whatsapp.groups.join_requests.reject(
        "wag_01krdgeqcxet5s7t44vh8rt9mg",
        join_request_ids=["wgj_01krdgeqcxet5s7t44vh8rt9mg"],
    )
    for failure in result.failed:
        print(failure.join_request_id, failure.error.description)


def whatsapp_groups_pins_create() -> None:
    pin = client.whatsapp.groups.pins.create(
        "wag_01krdgeqcxet5s7t44vh8rt9mg",
        message_id="wam_01kya19eknftrs2s6p82asmvnh",
    )
    print(pin.pinned_until)


def whatsapp_groups_pins_delete() -> None:
    group = client.whatsapp.groups.pins.delete(
        "wag_01krdgeqcxet5s7t44vh8rt9mg",
        "wam_01kya19eknftrs2s6p82asmvnh",
    )
    print(len(group.pinned_messages or []))


def whatsapp_keyword_rules_list() -> None:
    rules = client.whatsapp.keyword_rules.list(operation="opt_out")
    for rule in rules.data or []:
        print(rule.scope, rule.effective_keywords)


def whatsapp_keyword_rules_get() -> None:
    # Bird's rules and yours share the wkr_ id space; scope tells them apart.
    rule = client.whatsapp.keyword_rules.get("wkr_01m2kj8x4te9p0rr7e5w2n1abc")
    print(rule.scope, rule.reply)


def whatsapp_keyword_rules_create() -> None:
    rule = client.whatsapp.keyword_rules.create(
        operation="opt_out",
        country="US",  # the SENDER's country, from their own number
        reply="You're off the list. ACME Courier won't message you again.",
    )
    # effective_keywords is Bird's set plus any of your own.
    print(rule.id, rule.effective_keywords)


def whatsapp_keyword_rules_update() -> None:
    # Omitting keywords leaves the set alone; an empty list clears your additions
    # back to Bird's.
    rule = client.whatsapp.keyword_rules.update(
        "wkr_01m2kj8x4te9p0rr7e5w2n1abc", keywords=["no more texts", "remove me"]
    )
    print(rule.effective_keywords)


def whatsapp_keyword_rules_delete() -> None:
    # The next rule in the ladder answers the scope, which is another rule of yours if you hold a less specific one; STOP never stops working.
    client.whatsapp.keyword_rules.delete("wkr_01m2kj8x4te9p0rr7e5w2n1abc")


def whatsapp_suppressions_list() -> None:
    # address is a prefix, so a partial value matches every address under it.
    suppressions = client.whatsapp.suppressions.list(address="+1555")
    for suppression in suppressions.data or []:
        print(suppression.address, suppression.waba or "every account")


def whatsapp_suppressions_get() -> None:
    # Resolves a record that has already ended, which the list leaves out.
    suppression = client.whatsapp.suppressions.get("was_01krdgeqcxet5s7t44vh8rt9mg")
    print(suppression.reason, suppression.ended_at or "still in force")


def whatsapp_suppressions_add() -> None:
    # Omit waba to block the address for the whole workspace, whichever account
    # sends. With it, your other accounts keep reaching them, and the same
    # address for two accounts is two records.
    suppression = client.whatsapp.suppressions.add(
        address="+15550001234",
        waba="102290129340398",
    )
    print(suppression.id, suppression.applies_to)


def whatsapp_suppressions_remove() -> None:
    # Only a manual suppression can be ended; a recipient's own opt-out is
    # theirs to reverse. The record is kept and still reads back by id.
    client.whatsapp.suppressions.remove("was_01krdgeqcxet5s7t44vh8rt9mg")
