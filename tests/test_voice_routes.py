import pytest
from pydantic import ValidationError

from bird import (
    VoiceCallRouteRingGroup,
    VoiceCallRouteWritable,
    VoiceLeg,
    VoiceLegInboundRouteRingGroup,
    VoiceNumber,
    VoiceSettings,
)


def test_ring_group_routes_decode() -> None:
    group_id = "vrg_01krdgeqcxet5s7t44vh8rt9mg"
    route = {"type": "ring_group", "ring_group_id": group_id}
    number = VoiceNumber.model_validate({
        "id": "vnu_01krdgeqcxet5s7t44vh8rt9mg",
        "phone_number": "+14155551234",
        "country_code": "US",
        "name": None,
        "provider": {"type": "allocation", "number_id": "nda_01krdgeqcxet5s7t44vh8rt9mg"},
        "directions": {"inbound": True, "outbound": False},
        "inbound_configuration": {"route": route},
        "created_at": "2026-08-01T12:00:00Z",
    })
    settings = VoiceSettings.model_validate({"inbound_configuration": {"route": route}, "daily_spend_limit": None})
    leg = VoiceLeg.model_validate({
        "id": "vcl_01krdgeqcxet5s7t44vh8rt9mg",
        "workspace_id": "ws_01krdgeqcxet5s7t44vh8rt9mg",
        "direction": "inbound",
        "from": "+14155551234",
        "to": "+16505559876",
        "status": "in_progress",
        "started_at": "2026-08-01T12:00:00Z",
        "route": route,
        "answered_by": {
            "type": "user",
            "user_id": "usr_01krdgeqcxet5s7t44vh8rt9mg",
            "registration_id": "vur_01krdgeqcxet5s7t44vh8rt9mg",
        },
    })
    assert number.inbound_configuration.route is not None
    for value in (number.inbound_configuration.route.root, settings.inbound_configuration.route.root):
        assert isinstance(value, VoiceCallRouteRingGroup)
        assert value.ring_group_id == group_id
    assert leg.route is not None
    assert isinstance(leg.route.root, VoiceLegInboundRouteRingGroup)
    assert leg.route.root.ring_group_id == group_id
    assert leg.answered_by is not None
    assert leg.answered_by.root.user_id == "usr_01krdgeqcxet5s7t44vh8rt9mg"
    assert leg.answered_by.root.registration_id == "vur_01krdgeqcxet5s7t44vh8rt9mg"
    payload = leg.model_dump(mode="json", by_alias=True)
    assert payload["answered_by"] == {
        "type": "user",
        "user_id": "usr_01krdgeqcxet5s7t44vh8rt9mg",
        "registration_id": "vur_01krdgeqcxet5s7t44vh8rt9mg",
    }
    payload["answered_by"] = None
    assert VoiceLeg.model_validate(payload).answered_by is None


def test_public_writable_route_excludes_sequence() -> None:
    with pytest.raises(ValidationError):
        VoiceCallRouteWritable.model_validate(
            {"type": "sequence", "sequence_id": "vsq_01krdgeqcxet5s7t44vh8rt9mg", "entry_node_id": "main"}
        )
