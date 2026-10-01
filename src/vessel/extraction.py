"""Shared, bounded extraction. This module never receives queries or gold."""

import ipaddress
import re
import socket
import time
from datetime import UTC, datetime
from urllib.parse import urljoin, urlsplit

import httpx
import pymupdf
from bs4 import BeautifulSoup

from vessel.adapters.base import BudgetExceeded, Context
from vessel.models import Asset, Bundle, Dataset, FetchLimits, Location, Observation, Source


class FetchRejected(ValueError):
    pass


def public_url(url: str):
    p = urlsplit(url)
    if p.scheme not in {"http", "https"} or not p.hostname or p.username or p.password:
        raise FetchRejected("only anonymous public HTTP(S) URLs are fetchable")
    if p.port not in {None, 80, 443}:
        raise FetchRejected("nonstandard fetch port")
    addresses = socket.getaddrinfo(p.hostname, p.port or (443 if p.scheme == "https" else 80))
    if not addresses or any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses):
        raise FetchRejected("nonpublic network address")


def download(url: str, context: Context, limits: FetchLimits, byte_limit: int | None = None):
    cap = min(byte_limit or limits.max_bytes, limits.max_bytes)
    started = time.monotonic()
    for _ in range(6):
        public_url(url)
        context.budget.reserve(0)
        with context.client.stream(
            "GET", url, timeout=limits.timeout_seconds, follow_redirects=False
        ) as response:
            if response.is_redirect:
                url = urljoin(url, response.headers["location"])
                continue
            response.raise_for_status()
            output = bytearray()
            truncated = False
            for chunk in response.iter_bytes():
                if time.monotonic() - started > limits.timeout_seconds:
                    raise FetchRejected("total fetch timeout exceeded")
                remaining = cap - len(output)
                output.extend(chunk[:remaining])
                if len(chunk) > remaining:
                    truncated = True
                    break
            return bytes(output), response.headers.get("content-type", ""), url, truncated
    raise FetchRejected("redirect limit exceeded")


def extract_pdf(content: bytes, source: Source, limits: FetchLimits, context: Context):
    bundles = []
    observations = []
    with pymupdf.open(stream=content, filetype="pdf") as pdf:
        text_count = 0
        for index in range(min(len(pdf), limits.max_pages)):
            page = pdf[index]
            text = page.get_text()
            if text_count + len(text) > limits.max_text_chars:
                observations.append(
                    Observation(kind="pdf_text", status="character_limit", truncated=True)
                )
                break
            text_count += len(text)
            rectangles = []
            for image in page.get_images(full=True):
                rectangles.extend(page.get_image_rects(image[0]))
            rectangles.extend(page.cluster_drawings())
            seen = set()
            for rect in rectangles:
                rect = rect & page.rect
                if rect.width < 36 or rect.height < 36 or tuple(rect) in seen:
                    continue
                seen.add(tuple(rect))
                # Respect a rendering pixel ceiling as well as download limits.
                if rect.width * rect.height > 8_000_000:
                    observations.append(
                        Observation(kind="pdf_visual", status="pixel_limit", truncated=True)
                    )
                    continue
                rendered = page.get_pixmap(clip=rect, matrix=pymupdf.Matrix(1, 1)).tobytes("png")
                sha = context.artifacts.put_bytes(rendered)
                bbox = (
                    rect.x0 / page.rect.width,
                    rect.y0 / page.rect.height,
                    rect.x1 / page.rect.width,
                    rect.y1 / page.rect.height,
                )
                caption_area = pymupdf.Rect(
                    rect.x0, rect.y1, rect.x1, min(page.rect.height, rect.y1 + 50)
                )
                caption = page.get_text(clip=caption_area)
                figure_match = re.search(r"\b(?:Figure|Fig\.|Table)\s+([\w.\-]+)", caption)
                location = Location(
                    page_index=index,
                    page_label=page.get_label() or None,
                    bbox=bbox,
                    figure=figure_match[1].rstrip(".") if figure_match else None,
                )
                bundles.append(
                    Bundle(
                        source=source,
                        visual=Asset(sha256=sha, rendition="crop", media_type="image/png"),
                        location=location,
                    )
                )
                if len(bundles) >= limits.max_assets:
                    observations.append(
                        Observation(kind="pdf_visual", status="asset_limit", truncated=True)
                    )
                    return bundles, observations
        if len(pdf) > limits.max_pages:
            observations.append(Observation(kind="pdf", status="page_limit", truncated=True))
    return bundles, observations


def extract_html(content: bytes, source: Source, limits: FetchLimits, context: Context):
    soup = BeautifulSoup(content, "html.parser")
    text = soup.get_text(" ", strip=True)
    observations = []
    if len(text) > limits.max_text_chars:
        observations.append(Observation(kind="html_text", status="character_limit", truncated=True))
    bundles = []
    byte_remaining = limits.max_bytes - len(content)
    seen = set()
    base = str(source.document_url)
    for element in soup.find_all(["img", "svg"]):
        if len(bundles) >= limits.max_assets:
            observations.append(
                Observation(kind="html_visual", status="asset_limit", truncated=True)
            )
            break
        if element.name == "svg":
            data = str(element).encode()
            sha = context.artifacts.put_bytes(data)
            visual = Asset(sha256=sha, rendition="publisher", media_type="image/svg+xml")
            asset_url = None
        else:
            src = element.get("src") or element.get("data-src")
            if not src or src.startswith("data:"):
                continue
            asset_url = urljoin(base, src)
            if asset_url in seen:
                continue
            seen.add(asset_url)
            if byte_remaining <= 0:
                observations.append(
                    Observation(kind="html_visual", status="byte_limit", truncated=True)
                )
                break
            try:
                data, mime, _, truncated = download(asset_url, context, limits, byte_remaining)
                byte_remaining -= len(data)
                if truncated or not mime.startswith("image/"):
                    observations.append(
                        Observation(
                            kind="html_visual", status="unusable_asset", truncated=truncated
                        )
                    )
                    continue
                sha = context.artifacts.put_bytes(data)
                visual = Asset(url=asset_url, sha256=sha, rendition="publisher", media_type=mime)
            except (FetchRejected, httpx.HTTPError, OSError, BudgetExceeded) as e:
                observations.append(Observation(kind="html_visual", status=type(e).__name__))
                continue
        figure = element.find_parent("figure")
        identifier = element.get("id") or (figure.get("id") if figure else None)
        # Asset URL is a precise web locator even without a figure label.
        locator = f"#{identifier}" if identifier else asset_url
        caption = (
            figure.find("figcaption").get_text(" ", strip=True)
            if figure and figure.find("figcaption")
            else ""
        )
        match = re.search(r"\b(?:Figure|Fig\.|Table)\s+([\w.\-]+)", caption)
        datasets = []
        if figure:
            for link in figure.find_all("a", href=True):
                if urlsplit(link["href"]).path.lower().endswith((".csv", ".xlsx", ".json")):
                    datasets.append(Dataset(url=urljoin(base, link["href"])))
        bundles.append(
            Bundle(
                source=source,
                visual=visual,
                location=Location(locator=locator, figure=match[1] if match else None)
                if locator or match
                else None,
                datasets=datasets,
            )
        )
    return bundles, observations


def extract_document(url: str, context: Context, limits: FetchLimits):
    try:
        content, mime, final_url, truncated = download(url, context, limits)
        sha = context.artifacts.put_bytes(content)
        observation = Observation(
            kind="document_fetch",
            status="ok",
            bytes=len(content),
            artifact_sha256=sha,
            truncated=truncated,
        )
        source = Source(document_url=final_url, document_sha256=sha, retrieved_at=datetime.now(UTC))
        # Keep truncated bytes for diagnosis, never parse incomplete PDFs or pretend full hashes.
        if truncated:
            return [], [observation]
        if content.startswith(b"%PDF") or "application/pdf" in mime:
            bundles, observations = extract_pdf(content, source, limits, context)
        elif "html" in mime:
            bundles, observations = extract_html(content, source, limits, context)
        elif mime.startswith("image/"):
            bundles = [
                Bundle(
                    source=source,
                    visual=Asset(url=final_url, sha256=sha, rendition="publisher", media_type=mime),
                    location=Location(locator=final_url),
                )
            ]
            observations = []
        else:
            bundles, observations = [], [Observation(kind="document", status="unsupported_content")]
        return bundles, [observation, *observations]
    except (
        FetchRejected,
        httpx.HTTPError,
        OSError,
        ValueError,
        RuntimeError,
        BudgetExceeded,
    ) as error:
        return [], [Observation(kind="document_fetch", status=type(error).__name__)]
