"""Runtime behavior of the contacts facade: the generated create/get/delete
(contacts_gen) reach the right verb + path + body, and the hand override methods
ride the same client. Sync and async share the generated base, so one async case
guards the mirror."""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from bird import AsyncBird, Bird
from bird._generated import Contact

BASE = "https://eu1.platform.bird.com"
CID = "con_01krdgeqcxet5s7t44vh8rt9mg"


def _contact(email: str = "jane@acme.com") -> dict:
    return {
        "id": CID, "email": email, "phone": None, "first_name": "Jane",
        "created_at": "2026-01-01T00:00:00Z", "updated_at": "2026-01-01T00:00:00Z",
    }


def client() -> Bird:
    return Bird(api_key="bk_eu1_secret")


@respx.mock
def test_create_posts_body_and_auto_idempotency() -> None:
    route = respx.post(f"{BASE}/v1/contacts").mock(return_value=httpx.Response(200, json=_contact()))
    contact = client().contacts.create(email="jane@acme.com", first_name="Jane")
    assert isinstance(contact, Contact)
    assert contact.id == CID
    sent = route.calls.last.request
    body = json.loads(sent.content)
    assert body == {"email": "jane@acme.com", "first_name": "Jane"}  # unset fields omitted
    assert sent.headers.get("idempotency-key")  # POST gets an auto key


@respx.mock
def test_get_reads_by_id_path() -> None:
    route = respx.get(f"{BASE}/v1/contacts/{CID}").mock(return_value=httpx.Response(200, json=_contact()))
    contact = client().contacts.get(CID)
    assert contact.email == "jane@acme.com"
    assert route.calls.last.request.method == "GET"


@respx.mock
def test_delete_issues_delete_on_id_path() -> None:
    route = respx.delete(f"{BASE}/v1/contacts/{CID}").mock(return_value=httpx.Response(204))
    assert client().contacts.delete(CID) is None
    assert route.calls.last.request.method == "DELETE"


@respx.mock
def test_list_auto_paginates_and_advances_cursor() -> None:
    # Page 1 carries next_cursor; page 2 ends it. The generated list must walk both,
    # echoing next_cursor into the second request's starting_after.
    def page(request: httpx.Request) -> httpx.Response:
        after = request.url.params.get("starting_after")
        if after is None:
            return httpx.Response(200, json={"data": [_contact("a@x.com")], "next_cursor": "cur1"})
        assert after == "cur1"
        return httpx.Response(200, json={"data": [_contact("b@x.com")], "next_cursor": None})

    respx.get(f"{BASE}/v1/contacts").mock(side_effect=page)
    emails = [c.email for c in client().contacts.list(q="x.com")]
    assert emails == ["a@x.com", "b@x.com"]


@respx.mock
@pytest.mark.asyncio
async def test_async_create_mirrors_sync() -> None:
    route = respx.post(f"{BASE}/v1/contacts").mock(return_value=httpx.Response(200, json=_contact()))
    async with AsyncBird(api_key="bk_eu1_secret") as bird:
        contact = await bird.contacts.create(email="jane@acme.com")
    assert contact.id == CID
    assert json.loads(route.calls.last.request.content) == {"email": "jane@acme.com"}
