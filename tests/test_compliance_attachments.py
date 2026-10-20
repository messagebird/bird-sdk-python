from __future__ import annotations

import io
from email.parser import BytesParser
from email.policy import HTTP

import httpx
import pytest
import respx

from bird import APIStatusError, AsyncBird, Bird, ComplianceAttachment, ComplianceFile

BASE = "https://eu1.platform.bird.com"
ATTACHMENT_ID = "tca_01krdgeqcxet5s7t44vh8rt9mg"
TEMPLATE_ID = "cmt_01krdgeqcxet5s7t44vh8rt9mg"
PDF = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\n"
ATTACHMENT = {
    "id": ATTACHMENT_ID,
    "filename": "proof.pdf",
    "content_type": "application/pdf",
    "size_bytes": len(PDF),
    "download_url": "https://files.example/proof.pdf",
    "download_url_expires_at": "2026-10-08T00:00:00Z",
    "status": "draft",
    "expires_at": None,
    "created_at": "2026-10-07T00:00:00Z",
    "updated_at": "2026-10-07T00:00:00Z",
}


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("bird._base_client.time.sleep", lambda _seconds: None)


def _parts(request: httpx.Request) -> dict[str, tuple[str | None, bytes]]:
    head = f"Content-Type: {request.headers['content-type']}\r\n\r\n".encode()
    message = BytesParser(policy=HTTP).parsebytes(head + request.content)
    parts: dict[str, tuple[str | None, bytes]] = {}
    for part in message.iter_parts():
        name = part.get_param("name", header="content-disposition")
        payload = part.get_payload(decode=True)
        assert isinstance(payload, bytes)
        parts[str(name)] = (part.get_filename(), payload)
    return parts


@respx.mock
def test_create_sends_the_file_and_description_as_multipart() -> None:
    route = respx.post(f"{BASE}/v1/compliance/attachments").mock(
        return_value=httpx.Response(201, json=ATTACHMENT)
    )
    attachment = Bird(api_key="bk_eu1_x").compliance_attachments.create(
        file=io.BytesIO(PDF), filename="proof.pdf", description="Utility bill"
    )

    request = route.calls.last.request
    assert request.headers["content-type"].startswith("multipart/form-data; boundary=")
    assert request.headers["idempotency-key"]
    parts = _parts(request)
    assert parts["file"] == ("proof.pdf", PDF)
    assert parts["description"] == (None, b"Utility bill")
    assert isinstance(attachment, ComplianceAttachment)
    assert attachment.id == ATTACHMENT_ID


@respx.mock
def test_create_omits_an_unset_description() -> None:
    route = respx.post(f"{BASE}/v1/compliance/attachments").mock(
        return_value=httpx.Response(200, json=ATTACHMENT)
    )
    Bird(api_key="bk_eu1_x").compliance_attachments.create(file=PDF, filename="proof.pdf")

    assert set(_parts(route.calls.last.request)) == {"file"}


# The server dedupes a retried upload by its key; a fresh key per attempt
# would turn an ambiguous failure into a second write.
@respx.mock
def test_create_retries_with_the_same_body_and_key() -> None:
    route = respx.post(f"{BASE}/v1/compliance/attachments").mock(
        side_effect=[
            httpx.Response(408, json={"error": {"type": "request_timeout_error", "code": "E00408", "message": "try again"}}),
            httpx.Response(201, json=ATTACHMENT),
        ]
    )
    Bird(api_key="bk_eu1_x", max_retries=1).compliance_attachments.create(
        file=io.BytesIO(PDF), filename="proof.pdf"
    )

    first, second = (call.request for call in route.calls)
    assert first.headers["idempotency-key"] == second.headers["idempotency-key"]
    assert first.content == second.content
    assert _parts(second)["file"] == ("proof.pdf", PDF)


@respx.mock
def test_get_returns_the_bytes_type_and_rfc5987_filename() -> None:
    respx.get(f"{BASE}/v1/compliance/attachments/{ATTACHMENT_ID}").mock(
        return_value=httpx.Response(
            200,
            content=PDF,
            headers={
                "Content-Type": "application/pdf",
                "Content-Disposition": "attachment; filename=\"_rbol.pdf\"; filename*=UTF-8''%C3%A1rbol.pdf",
            },
        )
    )
    file = Bird(api_key="bk_eu1_x").compliance_attachments.get(ATTACHMENT_ID)

    assert file == ComplianceFile(data=PDF, content_type="application/pdf", filename="árbol.pdf")


@respx.mock
def test_document_template_get_reads_a_word_form() -> None:
    docx = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    respx.get(f"{BASE}/v1/compliance/document-templates/{TEMPLATE_ID}").mock(
        return_value=httpx.Response(
            200,
            content=b"PK\x03\x04",
            headers={"Content-Type": docx, "Content-Disposition": 'attachment; filename="form.docx"'},
        )
    )
    form = Bird(api_key="bk_eu1_x").compliance_document_templates.get(TEMPLATE_ID)

    assert form == ComplianceFile(data=b"PK\x03\x04", content_type=docx, filename="form.docx")


@respx.mock
def test_get_maps_a_404_to_the_api_error() -> None:
    respx.get(f"{BASE}/v1/compliance/attachments/{ATTACHMENT_ID}").mock(
        return_value=httpx.Response(
            404, json={"error": {"type": "not_found_error", "code": "E12044", "message": "attachment not found"}}
        )
    )
    with pytest.raises(APIStatusError) as exc:
        Bird(api_key="bk_eu1_x").compliance_attachments.get(ATTACHMENT_ID)
    assert exc.value.status_code == 404


@respx.mock
async def test_async_upload_and_download() -> None:
    upload = respx.post(f"{BASE}/v1/compliance/attachments").mock(
        return_value=httpx.Response(201, json=ATTACHMENT)
    )
    respx.get(f"{BASE}/v1/compliance/attachments/{ATTACHMENT_ID}").mock(
        return_value=httpx.Response(200, content=PDF, headers={"Content-Type": "application/pdf"})
    )
    async with AsyncBird(api_key="bk_eu1_x") as client:
        attachment = await client.compliance_attachments.create(file=PDF, filename="proof.pdf")
        file = await client.compliance_attachments.get(attachment.id)

    assert _parts(upload.calls.last.request)["file"] == ("proof.pdf", PDF)
    assert file.data == PDF
    assert file.filename is None


@respx.mock
@pytest.mark.parametrize("as_stream", [False, True])
def test_create_rejects_oversized_upload_before_sending(as_stream: bool) -> None:
    class BoundedRead(io.BytesIO):
        def read(self, size: int | None = -1) -> bytes:
            assert size is not None
            assert 0 < size <= (10 << 20) + 1 - self.tell()
            return super().read(size)

    data = b"x" * ((10 << 20) + 1)
    with pytest.raises(ValueError, match="exceeds 10 MiB"):
        Bird(api_key="bk_eu1_x").compliance_attachments.create(
            file=BoundedRead(data) if as_stream else data, filename="proof.pdf"
        )
