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
    })
    assert number.inbound_configuration.route is not None
    for value in (number.inbound_configuration.route.root, settings.inbound_configuration.route.root):
        assert isinstance(value, VoiceCallRouteRingGroup)
        assert value.ring_group_id == group_id
    assert leg.route is not None
    assert isinstance(leg.route.root, VoiceLegInboundRouteRingGroup)
    assert leg.route.root.ring_group_id == group_id


def test_public_writable_route_excludes_sequence() -> None:
    with pytest.raises(ValidationError):
        VoiceCallRouteWritable.model_validate(
            {"type": "sequence", "sequence_id": "vsq_01krdgeqcxet5s7t44vh8rt9mg", "entry_node_id": "main"}
        )
