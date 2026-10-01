import hashlib
import socket

import httpx
import pymupdf
import pytest

from vessel.extraction import FetchRejected, download, extract_document, extract_pdf, public_url
from vessel.models import FetchLimits, Source


@pytest.fixture
def public_network(monkeypatch):
    monkeypatch.setattr("vessel.extraction.public_url", lambda url: None)


def test_blocks_private_network(monkeypatch):
    monkeypatch.setattr(
        socket, "getaddrinfo", lambda *a: [(None, None, None, None, ("127.0.0.1", 80))]
    )
    with pytest.raises(FetchRejected):
        public_url("https://example.org")


@pytest.mark.parametrize(
    "url", ["file:///etc/passwd", "http://user:password@example.org", "http://example.org:8787"]
)
def test_blocks_unsafe_url(url):
    with pytest.raises(FetchRejected):
        public_url(url)


def test_download_byte_limit(context, public_network):
    context.client = httpx.Client(
        transport=httpx.MockTransport(lambda r: httpx.Response(200, content=b"123456"))
    )
    content, _, _, truncated = download("https://example.org", context, FetchLimits(max_bytes=3))
    assert content == b"123" and truncated
    assert context.budget.requests == 1


def test_redirect_targets_checked(context, monkeypatch):
    called = []

    def guard(url):
        called.append(url)
        if "127.0.0.1" in url:
            raise FetchRejected("private")

    monkeypatch.setattr("vessel.extraction.public_url", guard)
    context.client = httpx.Client(
        transport=httpx.MockTransport(
            lambda r: httpx.Response(302, headers={"location": "http://127.0.0.1/"})
        )
    )
    with pytest.raises(FetchRejected):
        download("https://example.org", context, FetchLimits())
    assert len(called) == 2


def test_html_image_data_and_locator(context, public_network):
    html = (
        b'<figure id="fig1"><img src="/chart.png"><figcaption>Figure 1 Test</figcaption>'
        b'<a href="/data.csv">data</a></figure>'
    )

    def handler(r):
        return httpx.Response(
            200,
            content=html if r.url.path == "/" else b"image",
            headers={"content-type": "text/html" if r.url.path == "/" else "image/png"},
        )

    context.client = httpx.Client(transport=httpx.MockTransport(handler))
    bundles, obs = extract_document("https://example.org/", context, FetchLimits())
    assert bundles[0].location.locator == "#fig1"
    assert bundles[0].visual.sha256 == hashlib.sha256(b"image").hexdigest()
    assert str(bundles[0].datasets[0].url) == "https://example.org/data.csv"
    assert obs[0].status == "ok"


def test_truncated_pdf_not_parsed(context, public_network):
    context.client = httpx.Client(
        transport=httpx.MockTransport(
            lambda r: httpx.Response(
                200, content=b"%PDF-invalid", headers={"content-type": "application/pdf"}
            )
        )
    )
    bundles, obs = extract_document(
        "https://example.org/doc.pdf", context, FetchLimits(max_bytes=5)
    )
    assert bundles == [] and obs[0].truncated


def test_pdf_page_and_asset_limits(context):
    pdf = pymupdf.open()
    for _ in range(3):
        page = pdf.new_page()
        page.draw_rect(pymupdf.Rect(50, 50, 200, 200), color=(1, 0, 0), fill=(0.5, 0.5, 0.5))
    content = pdf.tobytes()
    pdf.close()
    bundles, obs = extract_pdf(
        content,
        Source(document_url="https://example.org/doc.pdf"),
        FetchLimits(max_pages=1),
        context,
    )
    assert bundles[0].location.page_index == 0
    assert bundles[0].visual.rendition == "crop"
    assert any(o.status == "page_limit" for o in obs)
    assert context.artifacts.read(bundles[0].visual.sha256).startswith(b"\x89PNG")
