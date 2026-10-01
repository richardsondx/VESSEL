"""Identity utilities shared by invocation and scoring; no gold/provider dependencies."""

from urllib.parse import urlsplit, urlunsplit


def canonical_url(url: object | None) -> str | None:
    if url is None:
        return None
    p = urlsplit(str(url))
    # Preserve query parameters: IDs, vintages and chart configuration can live there.
    return urlunsplit((p.scheme.lower(), p.netloc.lower(), p.path or "/", p.query, ""))
