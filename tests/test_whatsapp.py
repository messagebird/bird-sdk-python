from __future__ import annotations

import json

import httpx
import respx

from bird import Bird, WhatsAppMessage

BASE = "https://eu1.platform.bird.com"
ID1 = "wam_01krdgeqcxet5s7t44vh8rt9mg"


def _message(content: dict) -> dict:
    return {
        "id": ID1,
        "direction": "outbound",
        "from": {"phone_number": "+14155552672"},
        "to": {"phone_number": "+14155552671"},
        "status": "accepted",
        "created_at": "2026-07-08T12:00:00Z",
        **content,
    }


def client() -> Bird:
    return Bird(api_key="bk_eu1_secret")


@respx.mock
def test_send_free_form_text_carries_from_and_no_template() -> None:
    text = {"body": "Your driver is 2 minutes away."}
    route = respx.post(f"{BASE}/v1/whatsapp/messages").mock(
        return_value=httpx.Response(202, json=_message({"text": text}))
    )
    message = client().whatsapp.send(to="+14155552671", from_="+14155552672", text=text)
    assert isinstance(message, WhatsAppMessage)
    body = json.loads(route.calls.last.request.content)
    assert body["from"] == "+14155552672"  # from_ -> "from" alias
    assert body["text"] == text
    assert "template" not in body


@respx.mock
def test_send_media_arms_reach_the_wire_verbatim() -> None:
    document = {
        "url": "https://cdn.example.com/invoices/a1b2c3.pdf",
        "caption": "Your invoice for order A1B2C3",
        "filename": "invoice-a1b2c3.pdf",
    }
    route = respx.post(f"{BASE}/v1/whatsapp/messages").mock(
        return_value=httpx.Response(202, json=_message({"document": document}))
    )
    client().whatsapp.send(to="+14155552671", from_="+14155552672", document=document)
    body = json.loads(route.calls.last.request.content)
    assert body["document"] == document
    assert "image" not in body  # unset arms are omitted, not sent as null


@respx.mock
def test_send_template_still_sugars_the_handle_and_carries_tags() -> None:
    route = respx.post(f"{BASE}/v1/whatsapp/messages").mock(
        return_value=httpx.Response(202, json=_message({}))
    )
    client().whatsapp.send(
        to="+14155552671",
        template="bird_otp",
        tags=[{"name": "campaign", "value": "spring_sale"}],
        metadata={"order_id": "A1B2C3"},
    )
    body = json.loads(route.calls.last.request.content)
    assert body["template"] == {"slug": "bird_otp"}
    assert body["tags"] == [{"name": "campaign", "value": "spring_sale"}]
    assert body["metadata"] == {"order_id": "A1B2C3"}
    assert "from" not in body
