"""Example source for the generated voice methods.

Each bird:snippet region is harvested for the docs site + README, and the
surfacegen Python writer injects it (marker-free) as the docstring example on
the generated method. Hand-written and type-checked (pyright includes
examples/); nothing regenerates over it. Calls are placed by your own SIP
equipment rather than through the API, so the call log is a read surface.
"""

from bird import Bird

client = Bird()


def voice_get() -> None:
    call = client.voice.get("vcl_01k0p3v9wera3v6q6xw3e9y2mh")
    # A call still ringing or connected carries no economics yet.
    print(call.status, call.duration_ms, call.cost)


def voice_list() -> None:
    for call in client.voice.list(status=["ringing", "in_progress"]):
        print(call.id, call.status)
