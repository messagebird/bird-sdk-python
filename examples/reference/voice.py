# Publishing constraints: see ../../../AGENTS.md (Cross-SDK example catalog).

from bird import Bird

client = Bird()


def voice_get() -> None:
    call = client.voice.legs.get("vcl_01k0p3v9wera3v6q6xw3e9y2mh")
    # A call still ringing or connected carries no economics yet.
    print(call.status, call.duration_ms, call.cost)


def voice_list() -> None:
    for leg in client.voice.legs.list():
        print(leg.id, leg.status)


def voice_create_call() -> None:
    call = client.voice.calls.create(
        from_="+12025550100",
        to="+12025550101",
        sequence={
            "id": "vsq_01krdgeqcxet5s7t44vh8rt9mg",
            "entry_node_id": "start",
            "trigger_data": {},
        },
    )
    print(call.id, call.initial_leg_id)
