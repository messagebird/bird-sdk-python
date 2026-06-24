from __future__ import annotations

import json

import httpx
import pytest
import respx

from bird import AsyncBird, Bird, BirdError, EmailMessage

BASE = "https://eu1.platform.bird.com"
ID1 = "em_01krdgeqcxet5s7t44vh8rt9mg"
ID2 = "em_02krdgeqcxet5s7t44vh8rt9mg"


def _message(message_id: str = ID1) -> dict:
    return {
        "id": message_id, "from": {"email": "a@b.com"}, "to": [{"email": "c@d.com"}], "subject": "Hi",
        "category": "transactional", "status": "accepted",
        "accepted_count": 1, "processed_count": 0, "delivered_count": 0, "bounced_count": 0,
        "complained_count": 0, "deferred_count": 0, "rejected_count": 0,
        "open_count": 0, "click_count": 0, "track_opens": True, "track_clicks": True,
        "created_at": "2026-01-01T00:00:00Z",
    }


def client() -> Bird:
    return Bird(api_key="bk_eu1_secret")


@respx.mock
def test_send_aliases_from_omits_unset_and_auto_idempotency() -> None:
    route = respx.post(f"{BASE}/v1/email/messages").mock(return_value=httpx.Response(200, json=_message()))
    message = client().email.send(from_="a@b.com", to=["c@d.com"], subject="Hi", html="<p>x</p>")
    assert isinstance(message, EmailMessage)
    assert message.id == ID1
    sent = route.calls.last.request
    body = json.loads(sent.content)
    assert body["from"] == "a@b.com"  # from_ -> "from" alias
    assert "track_opens" not in body  # unset -> omitted, server applies its default
    assert sent.headers.get("idempotency-key")  # POST gets an auto idempotency key


def _batch_item(message_id: str = ID1) -> dict:
    return {"id": message_id, "status": "accepted", "category": "transactional"}


@respx.mock
def test_send_batch_serializes_each_message_and_returns_data() -> None:
    route = respx.post(f"{BASE}/v1/email/batches").mock(
        return_value=httpx.Response(202, json={"data": [_batch_item(ID1), _batch_item(ID2)]})
    )
    batch = client().email.send_batch(
        messages=[
            {"from_": "a@b.com", "to": ["c@d.com"], "subject": "Hi", "html": "<p>x</p>"},
            {"from_": "a@b.com", "to": ["e@f.com"], "subject": "Hi 2", "text": "y"},
        ]
    )
    assert [item.id for item in batch.data] == [ID1, ID2]
    sent = route.calls.last.request
    body = json.loads(sent.content)
    assert isinstance(body, list) and len(body) == 2
    assert body[0]["from"] == "a@b.com"  # from_ -> "from" alias, per item
    assert "track_opens" not in body[0]  # unset -> omitted
    assert sent.headers.get("idempotency-key")  # POST gets an auto idempotency key


@respx.mock
def test_send_batch_applies_email_defaults() -> None:
    route = respx.post(f"{BASE}/v1/email/batches").mock(
        return_value=httpx.Response(202, json={"data": [_batch_item()]})
    )
    bird = Bird(api_key="bk_eu1_s", email_defaults={"from_": "default@acme.com"})
    bird.email.send_batch(messages=[{"to": ["c@d.com"], "subject": "Hi", "text": "x"}])
    body = json.loads(route.calls.last.request.content)
    assert body[0]["from"] == "default@acme.com"  # default fills unset from_ per item


def test_send_batch_invalid_message_raises_bird_error() -> None:
    with pytest.raises(BirdError):
        client().email.send_batch(
            messages=[{"from_": "ab", "to": ["c@d.com"], "subject": "Hi", "text": "x"}]  # from_ < min_length
        )


@respx.mock
async def test_async_send_batch_returns_data() -> None:
    respx.post(f"{BASE}/v1/email/batches").mock(
        return_value=httpx.Response(202, json={"data": [_batch_item(ID1), _batch_item(ID2)]})
    )
    async with AsyncBird(api_key="bk_eu1_secret") as bird:
        batch = await bird.email.send_batch(
            messages=[
                {"from_": "a@b.com", "to": ["c@d.com"], "subject": "Hi", "text": "x"},
                {"from_": "a@b.com", "to": ["e@f.com"], "subject": "Hi 2", "text": "y"},
            ]
        )
    assert [item.id for item in batch.data] == [ID1, ID2]


@respx.mock
def test_get_returns_model() -> None:
    respx.get(f"{BASE}/v1/email/messages/{ID1}").mock(return_value=httpx.Response(200, json=_message()))
    assert client().email.get(ID1).subject == "Hi"


@respx.mock
def test_status_compares_as_plain_string() -> None:
    data = {**_message(), "status": "delivered"}
    respx.get(f"{BASE}/v1/email/messages/{ID1}").mock(return_value=httpx.Response(200, json=data))
    msg = client().email.get(ID1)
    assert msg.status == "delivered"  # str-subclass enum compares equal to the wire string


@respx.mock
def test_list_auto_paginates_with_cursor() -> None:
    route = respx.get(f"{BASE}/v1/email/messages").mock(
        side_effect=[
            httpx.Response(200, json={"data": [_message(ID1)], "next_cursor": "cur2"}),
            httpx.Response(200, json={"data": [_message(ID2)], "next_cursor": None}),
        ]
    )
    ids = [m.id for m in client().email.list(limit=1)]
    assert ids == [ID1, ID2]
    assert route.call_count == 2
    assert "starting_after=cur2" in str(route.calls[1].request.url)


@respx.mock
def test_list_exposes_first_page_without_iterating() -> None:
    respx.get(f"{BASE}/v1/email/messages").mock(
        return_value=httpx.Response(200, json={"data": [_message()], "next_cursor": None})
    )
    page = client().email.list()
    assert len(page.data) == 1
    assert not page.has_next_page()


def test_invalid_send_input_raises_bird_error_without_leaking_values() -> None:
    # A client-side validation failure surfaces as BirdError, never a raw
    # pydantic.ValidationError; the message names the field + reason but not the value.
    import pydantic

    with pytest.raises(BirdError) as exc:
        client().email.send(from_="ab", to=["c@d.com"], subject="Hi", text="x")  # from_ < min_length
    msg = str(exc.value)
    assert not isinstance(exc.value, pydantic.ValidationError)
    assert "from" in msg  # the failing field is named
    assert "input" not in msg  # but pydantic's input_value=... echo is redacted


@respx.mock
def test_email_send_params_dict_splat() -> None:
    # EmailSendParams must stay splat-compatible with email.send's kwargs.
    from bird import EmailSendParams

    respx.post(f"{BASE}/v1/email/messages").mock(return_value=httpx.Response(200, json=_message()))
    params: EmailSendParams = {"from_": "a@b.com", "to": ["c@d.com"], "subject": "Hi", "text": "x"}
    assert client().email.send(**params).id == ID1


@respx.mock
async def test_async_has_next_page_requires_load() -> None:
    respx.get(f"{BASE}/v1/email/messages").mock(
        return_value=httpx.Response(200, json={"data": [_message(ID1)], "next_cursor": "cur2"})
    )
    async with AsyncBird(api_key="bk_eu1_secret") as bird:
        page = bird.email.list()  # not awaited — first page not loaded
        with pytest.raises(BirdError):
            page.has_next_page()  # must not silently answer "no more pages"
        loaded = await page
        assert loaded.has_next_page() is True


@respx.mock
async def test_async_page_await_then_iterate_fetches_first_page_once() -> None:
    route = respx.get(f"{BASE}/v1/email/messages").mock(
        return_value=httpx.Response(200, json={"data": [_message(ID1)], "next_cursor": None})
    )
    async with AsyncBird(api_key="bk_eu1_secret") as bird:
        page = await bird.email.list()
        assert page.has_next_page() is False
        ids = [m.id async for m in page]
    assert ids == [ID1]
    assert route.call_count == 1  # await + iterate must not re-fetch page 1


@respx.mock
async def test_async_list_iterates_directly_without_await() -> None:
    respx.get(f"{BASE}/v1/email/messages").mock(
        return_value=httpx.Response(200, json={"data": [_message(ID1), _message(ID2)], "next_cursor": None})
    )
    async with AsyncBird(api_key="bk_eu1_secret") as bird:
        ids = [m.id async for m in bird.email.list()]  # no await — the page is directly iterable
    assert ids == [ID1, ID2]


@respx.mock
async def test_async_send_and_auto_paginate() -> None:
    respx.post(f"{BASE}/v1/email/messages").mock(return_value=httpx.Response(200, json=_message()))
    respx.get(f"{BASE}/v1/email/messages").mock(
        return_value=httpx.Response(200, json={"data": [_message(ID1), _message(ID2)], "next_cursor": None})
    )
    async with AsyncBird(api_key="bk_eu1_secret") as bird:
        message = await bird.email.send(from_="a@b.com", to=["c@d.com"], subject="Hi", text="x")
        assert message.id == ID1
        page = await bird.email.list()
        ids = [m.id async for m in page]
    assert ids == [ID1, ID2]


@respx.mock
def test_send_with_attachment_serializes_to_wire() -> None:
    import base64

    route = respx.post(f"{BASE}/v1/email/messages").mock(return_value=httpx.Response(200, json=_message()))
    content = base64.b64encode(b"%PDF-1.4 fake").decode()
    client().email.send(
        from_="a@b.com", to=["c@d.com"], subject="Invoice", text="see attached",
        attachments=[{"filename": "invoice.pdf", "content": content, "content_type": "application/pdf"}],
    )
    body = json.loads(route.calls.last.request.content)
    assert body["attachments"][0]["filename"] == "invoice.pdf"
    assert body["attachments"][0]["content"] == content


def test_send_with_malformed_attachment_raises_bird_error() -> None:
    # A bad attachment (non-base64 content) is a client-side validation failure → BirdError.
    with pytest.raises(BirdError):
        client().email.send(
            from_="a@b.com", to=["c@d.com"], subject="Hi", text="x",
            attachments=[{"filename": "x.pdf", "content": "!!! not base64 !!!"}],
        )


@respx.mock
def test_client_is_thread_safe_for_concurrent_requests() -> None:
    from concurrent.futures import ThreadPoolExecutor

    respx.get(f"{BASE}/v1/email/messages/{ID1}").mock(return_value=httpx.Response(200, json=_message()))
    bird = client()
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _: bird.email.get(ID1), range(24)))
    assert all(r.id == ID1 for r in results)  # one shared client, many threads


@respx.mock
async def test_async_client_is_task_safe_for_concurrent_requests() -> None:
    import asyncio

    respx.get(f"{BASE}/v1/email/messages/{ID1}").mock(return_value=httpx.Response(200, json=_message()))
    async with AsyncBird(api_key="bk_eu1_secret") as bird:
        results = await asyncio.gather(*[bird.email.get(ID1) for _ in range(24)])
    assert all(r.id == ID1 for r in results)  # one shared client, many tasks


@respx.mock
def test_send_mailbox_string_passes_through_on_wire() -> None:
    # An address string is sent verbatim — including RFC 5322 mailbox form. The
    # wire's string arm accepts it and the server parses; the SDK does not convert.
    route = respx.post(f"{BASE}/v1/email/messages").mock(return_value=httpx.Response(200, json=_message()))
    client().email.send(
        from_="Acme Support <hello@acme.com>",
        to=["Jane Doe <jane@example.com>", "bob@example.com"],
        subject="Hi",
        text="hello",
    )
    body = json.loads(route.calls.last.request.content)
    assert body["from"] == "Acme Support <hello@acme.com>"
    assert body["to"][0] == "Jane Doe <jane@example.com>"
    assert body["to"][1] == "bob@example.com"


@respx.mock
def test_send_plain_string_stays_plain_on_wire() -> None:
    # A plain address with no display name must stay a string, not be wrapped in an object.
    route = respx.post(f"{BASE}/v1/email/messages").mock(return_value=httpx.Response(200, json=_message()))
    client().email.send(from_="hello@acme.com", to=["c@d.com"], subject="Hi", text="x")
    body = json.loads(route.calls.last.request.content)
    assert body["from"] == "hello@acme.com"
    assert body["to"] == ["c@d.com"]


@respx.mock
def test_response_round_trips_name() -> None:
    # When the server returns a display name, msg.from_.name and msg.to[0].name are set.
    data = {
        **_message(),
        "from": {"email": "hello@acme.com", "name": "Acme"},
        "to": [{"email": "jane@example.com", "name": "Jane Doe"}, {"email": "bob@example.com"}],
    }
    respx.get(f"{BASE}/v1/email/messages/{ID1}").mock(return_value=httpx.Response(200, json=data))
    msg = client().email.get(ID1)
    assert msg.from_.email == "hello@acme.com"
    assert msg.from_.name == "Acme"
    assert msg.to[0].email == "jane@example.com"
    assert msg.to[0].name == "Jane Doe"
    assert msg.to[1].email == "bob@example.com"
    assert msg.to[1].name is None
