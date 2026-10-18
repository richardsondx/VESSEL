"""Identity utilities shared by invocation and scoring; no gold/provider dependencies."""

from urllib.parse import urlsplit, urlunsplit


def canonical_url(url: object | None) -> str | None:
    if url is None:
        return None
    p = urlsplit(str(url))
    # Preserve query parameters: IDs, vintages and chart configuration can live there.
    # Normalize trailing slashes: /series/UNRATE and /series/UNRATE/ name the same resource.
    path = (p.path or "/").rstrip("/") or "/"
    return urlunsplit((p.scheme.lower(), p.netloc.lower(), path, p.query, ""))
