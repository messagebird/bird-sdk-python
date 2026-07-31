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

def mailbox_list() -> None:
    for mailbox in client.email.mailboxes.list():
        print(mailbox.id, mailbox.address)


def mailbox_create() -> None:
    mailbox = client.email.mailboxes.create(display_name="Acme Support")
    print(mailbox.id)


def mailbox_get() -> None:
    mailbox = client.email.mailboxes.get("mbx_01krdgeqcxet5s7t44vh8rt9mg")
    print(mailbox.address)


def mailbox_delete() -> None:
    client.email.mailboxes.delete("mbx_01krdgeqcxet5s7t44vh8rt9mg")


def mailbox_restore() -> None:
    mailbox = client.email.mailboxes.restore("mbx_01krdgeqcxet5s7t44vh8rt9mg")
    print(mailbox.id)


def mailbox_resume() -> None:
    mailbox = client.email.mailboxes.resume("mbx_01krdgeqcxet5s7t44vh8rt9mg")
    print(mailbox.state)


def mailbox_stats() -> None:
    stats = client.email.mailboxes.stats("mbx_01krdgeqcxet5s7t44vh8rt9mg")
    print(stats.summary)


def mailbox_labels() -> None:
    labels = client.email.mailboxes.labels("mbx_01krdgeqcxet5s7t44vh8rt9mg")
    for label in labels.data:
        print(label.name)


def mailbox_update() -> None:
    mailbox = client.email.mailboxes.update(
        "mbx_01krdgeqcxet5s7t44vh8rt9mg", display_name="Billing"
    )
    print(mailbox.display_name)

def mailbox_receive_rule_list() -> None:
    for rule in client.email.mailboxes.receive_rules.list("mbx_01krdgeqcxet5s7t44vh8rt9mg"):
        print(rule.id, rule.action)


def mailbox_receive_rule_create() -> None:
    rule = client.email.mailboxes.receive_rules.create(
        "mbx_01krdgeqcxet5s7t44vh8rt9mg", action="block", entry="spam.example.com"
    )
    print(rule.id)


def mailbox_receive_rule_delete() -> None:
    client.email.mailboxes.receive_rules.delete(
        "mbx_01krdgeqcxet5s7t44vh8rt9mg", "rrule_01krdgeqcxet5s7t44vh8rt9mg"
    )

def mailbox_thread_list() -> None:
    for thread in client.email.threads.list(mailbox_id="mbx_01krdgeqcxet5s7t44vh8rt9mg"):
        print(thread.id, thread.subject)


def mailbox_thread_get() -> None:
    thread = client.email.threads.get("thr_01krdgeqcxet5s7t44vh8rt9mg")
    print(thread.subject)


def mailbox_thread_update() -> None:
    thread = client.email.threads.update(
        "thr_01krdgeqcxet5s7t44vh8rt9mg", labels={"add": ["archive"]}
    )
    print(thread.id)


def mailbox_thread_delete() -> None:
    client.email.threads.delete("thr_01krdgeqcxet5s7t44vh8rt9mg", permanent=True)

def mailbox_thread_message_list() -> None:
    for message in client.email.threads.messages.list("thr_01krdgeqcxet5s7t44vh8rt9mg"):
        print(message.id, message.subject)


def mailbox_thread_message_get() -> None:
    message = client.email.threads.messages.get(
        "thr_01krdgeqcxet5s7t44vh8rt9mg", "msg_01krdgeqcxet5s7t44vh8rt9mg",
    )
    print(message.subject)


def mailbox_thread_message_body() -> None:
    body = client.email.threads.messages.body(
        "thr_01krdgeqcxet5s7t44vh8rt9mg", "msg_01krdgeqcxet5s7t44vh8rt9mg",
    )
    print(body.html)


def mailbox_thread_message_attachments() -> None:
    result = client.email.threads.messages.attachments(
        "thr_01krdgeqcxet5s7t44vh8rt9mg", "msg_01krdgeqcxet5s7t44vh8rt9mg",
    )
    for attachment in result.data:
        print(attachment.filename, attachment.size)


def mailbox_thread_message_reply() -> None:
    reply = client.email.threads.messages.reply(
        "thr_01krdgeqcxet5s7t44vh8rt9mg", "msg_01krdgeqcxet5s7t44vh8rt9mg",
        text="Thanks for reaching out!",
    )
    print(reply.id)
