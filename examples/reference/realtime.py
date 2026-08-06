"""Example source for the generated realtime methods.

Each bird:snippet region is harvested for the docs site + README; the keys match
the surface catalog (realtime.<leaf>, realtime.channels.<leaf>, …). Hand-written
and type-checked (pyright includes examples/); nothing regenerates over it.
"""

from bird import Bird

client = Bird()


def realtime_publish() -> None:
    result = client.realtime.publish(
        "rap_01krdgeqcxet5s7t44vh8rt9mg",
        event="order.updated",
        channels=["orders", "presence-lobby"],
        data={"order_id": "ord_123", "status": "shipped"},
    )
    print(result.data)


def realtime_publish_batch() -> None:
    client.realtime.publish_batch(
        "rap_01krdgeqcxet5s7t44vh8rt9mg",
        events=[
            {"event": "order.created", "channel": "orders", "data": {"id": 1}},
            {"event": "order.updated", "channel": "orders", "data": {"id": 2}},
        ],
    )


def realtime_channels_list() -> None:
    channels = client.realtime.channels.list(
        "rap_01krdgeqcxet5s7t44vh8rt9mg", prefix="presence-", include=["member_count"]
    )
    for channel in channels.data:
        print(channel.name, channel.member_count)


def realtime_channels_get() -> None:
    channel = client.realtime.channels.get(
        "rap_01krdgeqcxet5s7t44vh8rt9mg", "presence-lobby", include=["member_count"]
    )
    print(channel.occupied, channel.member_count)


def realtime_channels_members() -> None:
    members = client.realtime.channels.members(
        "rap_01krdgeqcxet5s7t44vh8rt9mg", "presence-lobby"
    )
    for member in members.members:
        print(member.member_id)


def realtime_members_send() -> None:
    client.realtime.members.send(
        "rap_01krdgeqcxet5s7t44vh8rt9mg",
        "user_42",
        event="order-shipped",
        data={"order_id": "ord_123"},
    )


def realtime_members_disconnect() -> None:
    client.realtime.members.disconnect("rap_01krdgeqcxet5s7t44vh8rt9mg", "user_42")
