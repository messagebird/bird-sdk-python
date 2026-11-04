from __future__ import annotations

import http.server
import io
import re
import ssl
import subprocess
import threading
from pathlib import Path
from typing import Iterator, NamedTuple

import httpx
import pytest

from bird import AsyncBird, Bird, BirdError


class PKI(NamedTuple):
    ca: Path
    server_cert: Path
    server_key: Path
    client_cert: Path
    client_key: Path
    other_key: Path
    encrypted_key: Path


def _openssl(*args: str, cwd: Path) -> None:
    subprocess.run(["openssl", *args], cwd=cwd, check=True, capture_output=True)


@pytest.fixture(scope="module")
def pki(tmp_path_factory: pytest.TempPathFactory) -> PKI:
    d = tmp_path_factory.mktemp("pki")
    ec = ["-newkey", "ec", "-pkeyopt", "ec_paramgen_curve:prime256v1", "-nodes"]
    (d / "ca.ext").write_text(
        "basicConstraints=critical,CA:TRUE\nkeyUsage=critical,keyCertSign\nsubjectKeyIdentifier=hash\n"
    )
    _openssl("req", *ec, "-keyout", "ca.key", "-out", "ca.csr", "-subj", "/CN=test CA", cwd=d)
    _openssl("x509", "-req", "-in", "ca.csr", "-signkey", "ca.key", "-out", "ca.pem", "-days", "1",
             "-extfile", "ca.ext", cwd=d)
    for name, usage in (("server", "serverAuth"), ("client", "clientAuth")):
        (d / f"{name}.ext").write_text(
            "basicConstraints=CA:FALSE\nauthorityKeyIdentifier=keyid\n"
            f"subjectAltName=IP:127.0.0.1\nextendedKeyUsage={usage}\n"
        )
        _openssl("req", *ec, "-keyout", f"{name}.key", "-out", f"{name}.csr", "-subj", f"/CN=sdk {name}", cwd=d)
        _openssl("x509", "-req", "-in", f"{name}.csr", "-CA", "ca.pem", "-CAkey", "ca.key", "-CAcreateserial",
                 "-out", f"{name}.pem", "-days", "1", "-extfile", f"{name}.ext", cwd=d)
    _openssl("genpkey", "-algorithm", "EC", "-pkeyopt", "ec_paramgen_curve:prime256v1", "-out", "other.key", cwd=d)
    _openssl("pkcs8", "-topk8", "-in", "client.key", "-out", "encrypted.key", "-passout", "pass:secret", cwd=d)
    return PKI(d / "ca.pem", d / "server.pem", d / "server.key", d / "client.pem", d / "client.key",
               d / "other.key", d / "encrypted.key")


@pytest.fixture
def mtls_server(pki: PKI) -> Iterator[tuple[str, list[str]]]:
    seen: list[str] = []

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            cert = self.connection.getpeercert()  # type: ignore[attr-defined]
            seen.append(dict(field[0] for field in cert["subject"])["commonName"])
            body = b"{}"
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: object) -> None:
            pass

    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(pki.server_cert, pki.server_key)
    ctx.load_verify_locations(pki.ca)
    ctx.verify_mode = ssl.CERT_REQUIRED
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.socket = ctx.wrap_socket(server.socket, server_side=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"https://127.0.0.1:{server.server_address[1]}", seen
    finally:
        server.shutdown()
        server.server_close()


def test_certificate_presented_sync(pki: PKI, mtls_server: tuple[str, list[str]], monkeypatch: pytest.MonkeyPatch) -> None:
    url, seen = mtls_server
    monkeypatch.setenv("SSL_CERT_FILE", str(pki.ca))
    with Bird(api_key="bk_eu1_x", base_url=url, client_cert=pki.client_cert, client_key=pki.client_key) as client:
        assert client.base_url == url
        client.get("/v1/workspace")
    assert seen == ["sdk client"]


async def test_certificate_presented_async(pki: PKI, mtls_server: tuple[str, list[str]], monkeypatch: pytest.MonkeyPatch) -> None:
    url, seen = mtls_server
    monkeypatch.setenv("SSL_CERT_FILE", str(pki.ca))
    async with AsyncBird(api_key="bk_eu1_x", base_url=url, client_cert=pki.client_cert, client_key=pki.client_key) as client:
        await client.get("/v1/workspace")
    assert seen == ["sdk client"]


def test_certificate_selects_mtls_host(pki: PKI) -> None:
    assert Bird(api_key="bk_us1_x", client_cert=pki.client_cert, client_key=pki.client_key).base_url == (
        "https://mtls.us1.platform.bird.com"
    )
    assert AsyncBird(api_key="bk_us1_x", region="eu1", client_cert=pki.client_cert, client_key=pki.client_key).base_url == (
        "https://mtls.eu1.platform.bird.com"
    )


def test_certificate_from_env(pki: PKI, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BIRD_CLIENT_CERT", str(pki.client_cert))
    monkeypatch.setenv("BIRD_CLIENT_KEY", str(pki.client_key))
    assert Bird(api_key="bk_us1_x").base_url == "https://mtls.us1.platform.bird.com"


def test_certificate_trusts_the_httpx_default_roots(pki: PKI, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SSL_CERT_FILE", raising=False)
    monkeypatch.delenv("SSL_CERT_DIR", raising=False)

    def roots(client: httpx.Client) -> list[str]:
        context = client._transport._pool._ssl_context  # type: ignore[attr-defined]
        return sorted(str(cert["serialNumber"]) for cert in context.get_ca_certs())

    sdk = Bird(api_key="bk_eu1_x", client_cert=pki.client_cert, client_key=pki.client_key)
    assert roots(sdk._client) == roots(httpx.Client())  # type: ignore[arg-type]


def test_unreadable_key_names_the_file(pki: PKI, tmp_path: Path) -> None:
    key = tmp_path / "unreadable.key"
    key.write_bytes(pki.client_key.read_bytes())
    key.chmod(0)
    with pytest.raises(BirdError, match=re.escape(str(key))):
        Bird(api_key="bk_eu1_x", client_cert=pki.client_cert, client_key=key)


@pytest.mark.parametrize("http_client", [None, "custom"])
def test_with_options_refuses_replacing_the_certificate_client(pki: PKI, http_client: str | None) -> None:
    client = Bird(api_key="bk_eu1_x", client_cert=pki.client_cert, client_key=pki.client_key)
    with pytest.raises(BirdError, match="http_client"):
        client.with_options(http_client=httpx.Client() if http_client else None)


def test_with_options_keeps_mtls(pki: PKI) -> None:
    client = Bird(api_key="bk_us1_x", client_cert=pki.client_cert, client_key=pki.client_key)
    derived = client.with_options(api_key="bk_eu1_y")
    assert derived.base_url == "https://mtls.eu1.platform.bird.com"
    assert derived._client is client._client


@pytest.mark.parametrize("client_cls", [Bird, AsyncBird])
@pytest.mark.parametrize(
    "case",
    ["key without certificate", "certificate without key", "missing file", "mismatched key", "encrypted key", "custom http_client"],
)
def test_certificate_refusals(pki: PKI, case: str, client_cls: type, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # An encrypted key must be refused, never answered with a passphrase prompt.
    monkeypatch.setattr("sys.stdin", io.StringIO(""))
    missing = tmp_path / "missing.pem"
    kwargs, named = {
        "key without certificate": ({"client_key": pki.client_key}, "client_cert"),
        "certificate without key": ({"client_cert": pki.client_cert}, "client_key"),
        "missing file": ({"client_cert": missing, "client_key": pki.client_key}, str(missing)),
        "mismatched key": ({"client_cert": pki.client_cert, "client_key": pki.other_key}, str(pki.other_key)),
        "encrypted key": ({"client_cert": pki.client_cert, "client_key": pki.encrypted_key}, str(pki.encrypted_key)),
        "custom http_client": (
            {
                "client_cert": pki.client_cert,
                "client_key": pki.client_key,
                "http_client": httpx.Client() if client_cls is Bird else httpx.AsyncClient(),
            },
            "http_client",
        ),
    }[case]
    with pytest.raises(BirdError, match=re.escape(named)):
        client_cls(api_key="bk_eu1_x", **kwargs)
