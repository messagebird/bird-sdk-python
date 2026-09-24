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


def voice_trunks_list() -> None:
    for trunk in client.voice.trunks.list():
        # A trunk with no allow list and no session credentials admits nothing.
        print(trunk.id, trunk.domain, trunk.inbound_enabled)

def voice_trunks_update() -> None:
    trunk = client.voice.trunks.update(
        "spt_01krdgeqcxet5s7t44vh8rt9mg",
        # Each list replaces the previous one, so send what you want to end up with.
        ip_acls=[{"cidr": "203.0.113.0/24", "description": "Amsterdam PBX"}],
    )
    print(trunk.ip_acls)

def voice_destinations_list() -> None:
    destinations = client.voice.destinations.list()
    for destination in destinations.data:
        print(destination.country_code, destination.enabled, destination.status)

def voice_session_credentials_create() -> None:
    credential = client.voice.session_credentials.create()
    # The password is returned once. Until expires_at it can place billed calls.
    print(credential.username, credential.realm, credential.expires_at)

def voice_trunks_create() -> None:
    trunk = client.voice.trunks.create(
        name="Lisbon office", outbound_enabled=True, inbound_enabled=True
    )
    print(trunk.id, trunk.domain)

def voice_trunks_get() -> None:
    trunk = client.voice.trunks.get("trunk-id")
    print(trunk.name, trunk.inbound_enabled, trunk.outbound_enabled)

def voice_trunks_delete() -> None:
    client.voice.trunks.delete("trunk-id")


def voice_trunks_gateways_list() -> None:
    gateways = client.voice.trunks.gateways.list("TRUNK_ID")
    for gateway in gateways.data:
        print(gateway.id, gateway.priority)


def voice_trunks_gateways_get() -> None:
    gateway = client.voice.trunks.gateways.get("TRUNK_ID", "GATEWAY_ID")
    print(gateway.id, gateway.priority)


def voice_trunks_gateways_create() -> None:
    gateway = client.voice.trunks.gateways.create(
        "TRUNK_ID",
        sip_uri="sip:pbx.example.com:5060",
        priority=0,
        destination_format="1234#{number}",
    )
    print(gateway.id, gateway.priority)


def voice_trunks_gateways_update() -> None:
    gateway = client.voice.trunks.gateways.update("TRUNK_ID", "GATEWAY_ID", priority=10)
    print(gateway.id, gateway.priority)


def voice_trunks_gateways_delete() -> None:
    client.voice.trunks.gateways.delete("TRUNK_ID", "GATEWAY_ID")


def voice_numbers_list() -> None:
    for number in client.voice.numbers.list():
        print(number.id, number.phone_number, number.country_code)

def voice_numbers_get() -> None:
    number = client.voice.numbers.get("number-id")
    print(number.phone_number, number.directions)

def voice_numbers_update() -> None:
    number = client.voice.numbers.update("number-id", name="Support line")
    print(number.id, number.name)

def voice_caller_ids_list() -> None:
    for caller_id in client.voice.caller_ids.list():
        print(caller_id.id, caller_id.phone_number, caller_id.status)

def voice_caller_ids_get() -> None:
    caller_id = client.voice.caller_ids.get("caller-id")
    print(caller_id.phone_number, caller_id.status, caller_id.verified_at)


def voice_caller_ids_verify() -> None:
    caller_id = client.voice.caller_ids.verify("CALLER_ID", code="123456")
    print(caller_id.id, caller_id.status)


def voice_destinations_update() -> None:
    destinations = client.voice.destinations.update(
        destinations=[{"country_code": "PT", "enabled": True}]
    )
    print(len(destinations.data))

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
