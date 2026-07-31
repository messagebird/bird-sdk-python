"""Example source for the generated mailbox_thread_message methods.

Each bird:snippet region is harvested for the docs site + README; the keys match
the surface catalog (mailbox_thread_message.<leaf>). Hand-written and type-checked
(pyright includes examples/); nothing regenerates over it.
"""

from bird import Bird

client = Bird()


def mailbox_thread_message_list() -> None:
    for message in client.mailbox_thread_message.list("thr_01krdgeqcxet5s7t44vh8rt9mg"):
        print(message.id, message.subject)


def mailbox_thread_message_get() -> None:
    message = client.mailbox_thread_message.get(
        "thr_01krdgeqcxet5s7t44vh8rt9mg", "msg_01krdgeqcxet5s7t44vh8rt9mg",
    )
    print(message.subject)


def mailbox_thread_message_body() -> None:
    body = client.mailbox_thread_message.body(
        "thr_01krdgeqcxet5s7t44vh8rt9mg", "msg_01krdgeqcxet5s7t44vh8rt9mg",
    )
    print(body.html)


def mailbox_thread_message_attachments() -> None:
    result = client.mailbox_thread_message.attachments(
        "thr_01krdgeqcxet5s7t44vh8rt9mg", "msg_01krdgeqcxet5s7t44vh8rt9mg",
    )
    for attachment in result.data:
        print(attachment.filename, attachment.size)


def mailbox_thread_message_reply() -> None:
    reply = client.mailbox_thread_message.reply(
        "thr_01krdgeqcxet5s7t44vh8rt9mg", "msg_01krdgeqcxet5s7t44vh8rt9mg",
        text="Thanks for reaching out!",
    )
    print(reply.id)
