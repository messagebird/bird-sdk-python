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


def voice_ring_groups_list() -> None:
    groups = client.voice.ring_groups.list()
    for group in groups.data:
        print(group.id, group.name, group.online_member_count)


def voice_ring_groups_get() -> None:
    group = client.voice.ring_groups.get("RING_GROUP_ID")
    print(group.id, group.name, group.online_member_count)


def voice_ring_groups_create() -> None:
    group = client.voice.ring_groups.create(name="Support")
    print(group.id, group.name)


def voice_ring_groups_update() -> None:
    group = client.voice.ring_groups.update("RING_GROUP_ID", name="Tier 2 support")
    print(group.id, group.name)


def voice_ring_groups_delete() -> None:
    client.voice.ring_groups.delete("RING_GROUP_ID")


def voice_ring_groups_members_list() -> None:
    members = client.voice.ring_groups.members.list("RING_GROUP_ID")
    for member in members.data:
        print(member.user_id)


def voice_ring_groups_members_create() -> None:
    member = client.voice.ring_groups.members.create("RING_GROUP_ID", user_id="USER_ID")
    print(member.user_id)


def voice_ring_groups_members_delete() -> None:
    client.voice.ring_groups.members.delete("RING_GROUP_ID", "USER_ID")


def voice_numbers_list() -> None:
    for number in client.voice.numbers.list():
        print(number.id, number.phone_number, number.country_code)

def voice_numbers_get() -> None:
    number = client.voice.numbers.get("number-id")
    print(number.phone_number, number.directions)

def voice_numbers_update() -> None:
    number = client.voice.numbers.update("number-id", name="Support line")
    print(number.id, number.name)

def voice_settings_get() -> None:
    settings = client.voice.settings.get()
    print(settings.inbound_configuration.route.root.type)

def voice_settings_update() -> None:
    from bird import VoiceCallRouteTrunk, VoiceCallRouteWritable, VoiceSettingsInboundConfigurationPut

    settings = client.voice.settings.update(
        inbound_configuration=VoiceSettingsInboundConfigurationPut(
            route=VoiceCallRouteWritable(
                VoiceCallRouteTrunk(type="trunk", trunk_id="spt_01krdgeqcxet5s7t44vh8rt9mg")
            ),
        ),
    )
    print(settings.inbound_configuration.route.root.type)

def voice_verified_numbers_list() -> None:
    for verified_number in client.voice.verified_numbers.list():
        print(verified_number.id, verified_number.phone_number, verified_number.status)

def voice_verified_numbers_get() -> None:
    verified_number = client.voice.verified_numbers.get("vvn_01krdgeqcxet5s7t44vh8rt9mg")
    print(verified_number.phone_number, verified_number.status, verified_number.verified_at)


def voice_verified_numbers_verify() -> None:
    verified_number = client.voice.verified_numbers.verify("vvn_01krdgeqcxet5s7t44vh8rt9mg", code="123456")
    print(verified_number.id, verified_number.status)


def voice_verified_numbers_create() -> None:
    # This places a verification call to the number that reads out a code.
    verified_number = client.voice.verified_numbers.create(phone_number="+14155551234", name="Support line")
    print(verified_number.id, verified_number.status)


def voice_verified_numbers_update() -> None:
    verified_number = client.voice.verified_numbers.update("vvn_01krdgeqcxet5s7t44vh8rt9mg", name="Sales line")
    print(verified_number.name)


def voice_verified_numbers_delete() -> None:
    client.voice.verified_numbers.delete("vvn_01krdgeqcxet5s7t44vh8rt9mg")


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


def voice_call_recordings() -> None:
    inventory = client.voice.calls.recordings.list("vcs_01krdgeqcxet5s7t44vh8rt9mg")
    for recording in inventory.recordings:
        print(recording.leg_id, recording.id)


def voice_call_transcript() -> None:
    transcript = client.voice.calls.transcript("vcs_01krdgeqcxet5s7t44vh8rt9mg")
    for cue in transcript.cues:
        print(cue.text)
