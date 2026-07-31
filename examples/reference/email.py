"""Example source for the generated email and email.stats methods.

Each bird:snippet region is harvested for the docs site + README; the keys
match the surface catalog (email.<leaf>, email.stats.<leaf>). Hand-written and type-checked
(pyright includes examples/); nothing regenerates over it.
"""

from bird import Bird

client = Bird()


def email_get() -> None:
    message = client.email.get("em_abc123")
    print(message.id, message.status, message.delivered_count)


def email_cancel() -> None:
    client.email.cancel("em_abc123")


def email_list() -> None:
    for message in client.email.list(status="delivered"):
        print(message.id)
    page = client.email.list(status="delivered")  # page.data, page.next_cursor
    print(len(page.data), page.next_cursor)

def email_stats_summary() -> None:
    summary = client.email.stats.summary(from_="2026-05-01", to="2026-05-25")
    print(summary.sends_accepted, summary.delivery)


def email_stats_daily() -> None:
    stats = client.email.stats.daily(from_="2026-05-01", to="2026-05-25")
    for point in stats.data:
        print(point.bucket, point.sends_accepted)


def email_stats_hourly() -> None:
    stats = client.email.stats.hourly(
        from_="2026-05-25T00:00:00Z",
        to="2026-05-25T23:59:59Z",
    )
    for point in stats.data:
        print(point.bucket, point.delivery)


def email_stats_byTag() -> None:
    stats = client.email.stats.by_tag(from_="2026-05-01", to="2026-05-25", sort="delivered")
    for row in stats.data:
        print(row)
    print(stats.total)


def email_stats_byCategory() -> None:
    stats = client.email.stats.by_category(from_="2026-05-01", to="2026-05-25")
    for row in stats.data:
        print(row)


def email_stats_bySendingIp() -> None:
    stats = client.email.stats.by_sending_ip(
        from_="2026-05-01", to="2026-05-25", sort="bounces.block",
    )
    for row in stats.data:
        print(row)


def email_stats_bySendingDomain() -> None:
    stats = client.email.stats.by_sending_domain(from_="2026-05-01", to="2026-05-25")
    for row in stats.data:
        print(row)


def email_stats_byRecipientDomain() -> None:
    stats = client.email.stats.by_recipient_domain(from_="2026-05-01", to="2026-05-25")
    for row in stats.data:
        print(row)


def email_stats_byMailboxProvider() -> None:
    stats = client.email.stats.by_mailbox_provider(from_="2026-05-01", to="2026-05-25")
    for row in stats.data:
        print(row)


def email_stats_byMailboxProviderRegion() -> None:
    stats = client.email.stats.by_mailbox_provider_region(from_="2026-05-01", to="2026-05-25")
    for row in stats.data:
        print(row)


def email_stats_byTemplate() -> None:
    stats = client.email.stats.by_template(from_="2026-05-01", to="2026-05-25")
    for row in stats.data:
        print(row)


def email_stats_byLocation() -> None:
    stats = client.email.stats.by_location(
        from_="2026-05-01", to="2026-05-25", group_by="country",
    )
    for row in stats.data:
        print(row)


def email_stats_byClient() -> None:
    stats = client.email.stats.by_client(
        from_="2026-05-01", to="2026-05-25", group_by="email_client",
    )
    for row in stats.data:
        print(row)


def email_stats_byBounceCode() -> None:
    stats = client.email.stats.by_bounce_code(from_="2026-05-01", to="2026-05-25")
    for row in stats.data:
        print(row)


def email_stats_byComplaintType() -> None:
    stats = client.email.stats.by_complaint_type(from_="2026-05-01", to="2026-05-25")
    for row in stats.data:
        print(row)


def email_stats_byBroadcast() -> None:
    stats = client.email.stats.by_broadcast(from_="2026-05-01", to="2026-05-25")
    for row in stats.data:
        print(row)

