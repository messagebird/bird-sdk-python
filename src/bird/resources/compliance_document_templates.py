"""Blank compliance forms: ``client.compliance_document_templates``.
Hand-written whole: its only operation returns raw bytes.
"""

from __future__ import annotations

from urllib.parse import quote

from bird._resource import AsyncResource, Resource, _opts
from bird._types import RequestOptions
from bird.resources.compliance_attachments import ComplianceFile, _compliance_file

_PATH = "/v1/compliance/document-templates"


class ComplianceDocumentTemplates(Resource):
    """The blank forms registration requirements name. Reach it via
    ``client.compliance_document_templates``."""

    def get(self, template_id: str, *, options: RequestOptions | None = None) -> ComplianceFile:
        """Download the blank form a requirement's ``template_url`` names, as a
        PDF, Word document, JPEG or PNG. Complete it and upload the result with
        ``client.compliance_attachments.create``; export a Word form to PDF
        first.

        ```python
        form = client.compliance_document_templates.get("cmt_01krdgeqcxet5s7t44vh8rt9mg")
        # Complete the form, then upload it with client.compliance_attachments.create.
        print(form.filename, form.content_type)
        ```
        """
        response = self._client.request("GET", f"{_PATH}/{quote(template_id, safe='')}", **_opts(options))
        return _compliance_file(response)


class AsyncComplianceDocumentTemplates(AsyncResource):
    """Async mirror of `ComplianceDocumentTemplates`."""

    async def get(self, template_id: str, *, options: RequestOptions | None = None) -> ComplianceFile:
        """Download a blank form; see :meth:`ComplianceDocumentTemplates.get`."""
        response = await self._client.request("GET", f"{_PATH}/{quote(template_id, safe='')}", **_opts(options))
        return _compliance_file(response)
