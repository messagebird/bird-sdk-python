"""Example source for the generated mailbox_thread methods.

Each bird:snippet region is harvested for the docs site + README; the keys match
the surface catalog (mailbox_thread.<leaf>). Hand-written and type-checked
(pyright includes examples/); nothing regenerates over it.
"""

from bird import Bird

client = Bird()


def mailbox_thread_list() -> None:
    for thread in client.mailbox_thread.list(mailbox_id="mbx_01krdgeqcxet5s7t44vh8rt9mg"):
        print(thread.id, thread.subject)


def mailbox_thread_get() -> None:
    thread = client.mailbox_thread.get("thr_01krdgeqcxet5s7t44vh8rt9mg")
    print(thread.subject)


def mailbox_thread_update() -> None:
    thread = client.mailbox_thread.update(
        "thr_01krdgeqcxet5s7t44vh8rt9mg", labels={"add": ["archive"]}
    )
    print(thread.id)


def mailbox_thread_delete() -> None:
    client.mailbox_thread.delete("thr_01krdgeqcxet5s7t44vh8rt9mg", permanent=True)
