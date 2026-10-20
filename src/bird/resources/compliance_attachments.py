"""Compliance attachments: ``client.compliance_attachments``. List and delete
are generated; the upload and the byte read are written here because one sends
a multipart body and the other returns raw bytes.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import IO
from urllib.parse import quote, unquote

import httpx

from bird._generated import Attachment as ComplianceAttachment
from bird._resource import _opts
from bird._types import RequestOptions
from bird.resources.compliance_attachments_gen import (
    AsyncComplianceAttachmentsBase,
    ComplianceAttachmentsBase,
)

_PATH = "/v1/compliance/attachments"
_MAX_FILE_BYTES = 10 << 20


@dataclass(frozen=True)
class ComplianceFile:
    """A file downloaded from the compliance API: an uploaded attachment or a
    blank form. ``content_type`` and ``filename`` are what the server declared
    for it."""

    data: bytes
    content_type: str
    filename: str | None


_EXTENDED_FILENAME = re.compile(r"filename\*\s*=\s*UTF-8''([^;]+)", re.IGNORECASE)
_PLAIN_FILENAME = re.compile(r'filename\s*=\s*(?:"([^"]*)"|([^;]+))', re.IGNORECASE)


def _disposition_filename(header: str | None) -> str | None:
    # The server sends an ASCII ``filename`` fallback and the RFC 5987
    # ``filename*`` original; the original wins when it is there.
    if not header:
        return None
    extended = _EXTENDED_FILENAME.search(header)
    if extended:
        try:
            return unquote(extended.group(1).strip(), errors="strict")
        except UnicodeDecodeError:
            pass
    plain = _PLAIN_FILENAME.search(header)
    if not plain:
        return None
    return (plain.group(1) if plain.group(1) is not None else plain.group(2).strip()) or None


def _compliance_file(response: httpx.Response) -> ComplianceFile:
    return ComplianceFile(
        data=response.content,
        content_type=response.headers.get("Content-Type") or "application/octet-stream",
        filename=_disposition_filename(response.headers.get("Content-Disposition")),
    )


def _upload(
    file: bytes | IO[bytes], filename: str, description: str | None
) -> tuple[dict[str, tuple[str, bytes]], dict[str, object] | None]:
    if isinstance(file, bytes):
        content = file
    else:
        chunks = bytearray()
        while len(chunks) <= _MAX_FILE_BYTES:
            chunk = file.read(min(65536, _MAX_FILE_BYTES + 1 - len(chunks)))
            if not chunk:
                break
            chunks.extend(chunk)
        content = bytes(chunks)
    if len(content) > _MAX_FILE_BYTES:
        raise ValueError("Compliance attachment exceeds 10 MiB")
    fields: dict[str, object] | None = None if description is None else {"description": description}
    return {"file": (filename, content)}, fields


class ComplianceAttachments(ComplianceAttachmentsBase):
    """Documents uploaded for registrations. Reach it via ``client.compliance_attachments``."""

    def create(
        self,
        *,
        file: bytes | IO[bytes],
        filename: str,
        description: str | None = None,
        options: RequestOptions | None = None,
    ) -> ComplianceAttachment:
        """Upload a supporting document for a registration and get back the
        attachment to cite by id in a submission's answers. PNG, JPEG, and PDF
        files up to 10 MB are accepted; the contents determine the type.

        Uploading bytes identical to an existing attachment returns that
        attachment instead of a second one, so retrying an upload whose outcome
        is unknown is safe. An attachment no registration cites expires after
        seven days.

        ```python
        with open("proof-of-address.pdf", "rb") as f:
            attachment = client.compliance_attachments.create(
                file=f,
                filename="proof-of-address.pdf",
                description="Utility bill for the registered address",
            )
        # Cite this id as the answer's attachment_id in a submission.
        print(attachment.id, attachment.content_type)
        ```
        """
        files, fields = _upload(file, filename, description)
        response = self._client.request("POST", _PATH, body=fields, files=files, **_opts(options))
        return ComplianceAttachment.model_validate(response.json())

    def get(self, attachment_id: str, *, options: RequestOptions | None = None) -> ComplianceFile:
        """Download the bytes of an uploaded registration attachment, with the
        content type and filename it was stored under.

        ```python
        file = client.compliance_attachments.get("tca_01krdgeqcxet5s7t44vh8rt9mg")
        print(file.filename, file.content_type, len(file.data))
        ```
        """
        response = self._client.request("GET", f"{_PATH}/{quote(attachment_id, safe='')}", **_opts(options))
        return _compliance_file(response)


class AsyncComplianceAttachments(AsyncComplianceAttachmentsBase):
    """Async mirror of `ComplianceAttachments`."""

    async def create(
        self,
        *,
        file: bytes | IO[bytes],
        filename: str,
        description: str | None = None,
        options: RequestOptions | None = None,
    ) -> ComplianceAttachment:
        """Upload a supporting document; see :meth:`ComplianceAttachments.create`."""
        files, fields = _upload(file, filename, description)
        response = await self._client.request("POST", _PATH, body=fields, files=files, **_opts(options))
        return ComplianceAttachment.model_validate(response.json())

    async def get(self, attachment_id: str, *, options: RequestOptions | None = None) -> ComplianceFile:
        """Download an attachment's bytes; see :meth:`ComplianceAttachments.get`."""
        response = await self._client.request("GET", f"{_PATH}/{quote(attachment_id, safe='')}", **_opts(options))
        return _compliance_file(response)
