"""Example source for the generated sms methods.

Each bird:snippet region is harvested for the docs site + README, and the
surfacegen Python writer injects it (marker-free) as the docstring example on
the generated method. Hand-written and type-checked (pyright includes
examples/); nothing regenerates over it. The sends stay hand-written, so their
examples stay inline in src/bird/resources/sms.py.
"""

from bird import Bird

client = Bird()


def sms_get() -> None:
    message = client.sms.get("sms_abc123")
    print(message.id, message.status)


def sms_list() -> None:
    for message in client.sms.list(direction="outbound"):
        print(message.id, message.status)


def sms_list_events() -> None:
    events = client.sms.list_events("sms_abc123")
    for event in events.data:
        print(event.type, event.occurred_at)


def sms_stats_summary() -> None:
    summary = client.sms.stats.summary(from_="2026-05-01", to="2026-05-31")
    print(summary.delivery, summary.latency)


def sms_stats_daily() -> None:
    stats = client.sms.stats.daily(from_="2026-05-01", to="2026-05-31")
    for point in stats.data or []:
        print(point.bucket, point.delivery)


def sms_stats_hourly() -> None:
    stats = client.sms.stats.hourly(from_="2026-05-30T00:00:00Z", to="2026-05-31T00:00:00Z")
    for point in stats.data or []:
        print(point.bucket, point.delivery)


def sms_stats_by_country() -> None:
    stats = client.sms.stats.by_country(from_="2026-05-01", to="2026-05-31", sort="delivery_rate")
    for row in stats.data or []:
        print(row.country, row.delivery)


def sms_stats_by_carrier() -> None:
    stats = client.sms.stats.by_carrier(from_="2026-05-01", to="2026-05-31")
    for row in stats.data or []:
        print(row.carrier, row.delivery)


def sms_stats_by_category() -> None:
    stats = client.sms.stats.by_category(from_="2026-05-01", to="2026-05-31")
    for row in stats.data or []:
        print(row.category, row.delivery)


def sms_stats_by_originator() -> None:
    stats = client.sms.stats.by_originator(from_="2026-05-01", to="2026-05-31")
    for row in stats.data or []:
        print(row.originator, row.delivery)


def sms_stats_by_status() -> None:
    stats = client.sms.stats.by_status(from_="2026-05-01", to="2026-05-31")
    for row in stats.data or []:
        print(row.status, row.count)


def sms_stats_by_error_code() -> None:
    stats = client.sms.stats.by_error_code(from_="2026-05-01", to="2026-05-31")
    for row in stats.data or []:
        # The same value as the error_code filter on client.sms.list.
        print(row.error_code, row.delivery)


def sms_stats_by_tag() -> None:
    stats = client.sms.stats.by_tag(from_="2026-05-01", to="2026-05-31")
    for row in stats.data or []:
        # A message carrying several tags counts once under each, so rows do not
        # sum to the period total.
        print(row.tag, row.delivery)


def sms_stats_inbound_summary() -> None:
    summary = client.sms.stats.inbound.summary(from_="2026-05-01", to="2026-05-31")
    print(summary.received)


def sms_stats_inbound_daily() -> None:
    stats = client.sms.stats.inbound.daily(from_="2026-05-01", to="2026-05-31")
    for point in stats.data or []:
        print(point.bucket, point.received)


def sms_stats_inbound_hourly() -> None:
    stats = client.sms.stats.inbound.hourly(
        from_="2026-05-30T00:00:00Z", to="2026-05-31T00:00:00Z"
    )
    for point in stats.data or []:
        print(point.bucket, point.received)


def sms_stats_inbound_by_country() -> None:
    stats = client.sms.stats.inbound.by_country(from_="2026-05-01", to="2026-05-31")
    for row in stats.data or []:
        print(row.country, row.received)


def sms_stats_inbound_by_operator() -> None:
    stats = client.sms.stats.inbound.by_operator(from_="2026-05-01", to="2026-05-31")
    for row in stats.data or []:
        # Messages whose operator the carrier did not report are excluded, so these
        # rows can sum to less than the inbound summary for the same period.
        print(row.mcc_mnc, row.received)


def sms_stats_inbound_by_number() -> None:
    stats = client.sms.stats.inbound.by_number(from_="2026-05-01", to="2026-05-31")
    for row in stats.data or []:
        print(row.number, row.received)


def sms_suppressions_list() -> None:
    for suppression in client.sms_suppressions.list():
        print(suppression.originator, suppression.destination, suppression.reason)


def sms_suppressions_get() -> None:
    suppression = client.sms_suppressions.get("sup_abc123")
    print(suppression.reason, suppression.blocking)


def sms_suppressions_add() -> None:
    # A suppression covers one sender and one subscriber, so stopping every sender
    # means one call per sender.
    suppression = client.sms_suppressions.add(
        destination="+15550001234", originator="+15557654321"
    )
    print(suppression.id)


def sms_suppressions_remove() -> None:
    # Only a `manual` suppression can be ended: a subscriber's own stop keyword and
    # a carrier's opt-out are refused.
    client.sms_suppressions.remove("sup_abc123")
def sms_keyword_rules_list() -> None:
    rules = client.sms_keyword_rules.list(country="NL")
    for rule in rules.data:
        print(rule.operation, rule.keywords)


def sms_keyword_rules_get() -> None:
    rule = client.sms_keyword_rules.get("skr_abc123")
    print(rule.operation, rule.reply)


def sms_keyword_rules_create() -> None:
    rule = client.sms_keyword_rules.create(
        operation="stop",
        country="NL",
        reply="You are unsubscribed from MyBrand. Reply START to resume.",
    )
    # effective_keywords is Bird's set plus any of your own.
    print(rule.id, rule.effective_keywords)


def sms_keyword_rules_update() -> None:
    # Omitting keywords leaves the set alone; an empty list clears your additions
    # back to Bird's.
    rule = client.sms_keyword_rules.update(
        "skr_abc123", reply="You are unsubscribed. Reply START to resume."
    )
    print(rule.reply)


def sms_keyword_rules_delete() -> None:
    client.sms_keyword_rules.delete("skr_abc123")
