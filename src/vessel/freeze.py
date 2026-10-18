"""Served-artifact freeze verification.

The frozen Evidence8 instance must expose its build/index identifiers so
the harness can verify the served artifact matches the attestation before
and after a run. Service contract (see docs/providers/evidence8.md):

    GET {base}/v1/version -> {
        "corpus_hash": "sha256:…",
        "index_hash": "sha256:…",
        "index_version": "…",
        "code_commit": "…"
    }

``check_freeze`` compares the served identifiers against the attestation
and reports per-field match/mismatch/unknown. Unknown means the service
did not expose an attested field: verification is impossible, which
blocks the run just like a mismatch does.
"""

import httpx

IDENTIFIER_FIELDS = ("corpus_hash", "index_hash", "index_version", "code_commit")
VERSION_PATH = "/v1/version"


def check_freeze(attestation: dict, base_url: str, client: httpx.Client) -> dict:
    """Compare served identifiers against the attestation.

    Returns {"fields": {name: {"expected", "observed", "match"}}, "verdict"}.
    ``match`` is True/False, or "unknown" when the service did not expose
    the field. Verdict is "match", "mismatch", or "unverifiable".
    """
    url = base_url.rstrip("/") + VERSION_PATH
    try:
        response = client.get(url, timeout=30)
        response.raise_for_status()
        served = response.json()
        if not isinstance(served, dict):
            raise ValueError("version endpoint returned a non-object")
    except Exception as exc:  # noqa: BLE001 - reported, not raised
        return {
            "fields": {
                name: {"expected": attestation.get(name), "observed": None, "match": "unknown"}
                for name in IDENTIFIER_FIELDS
            },
            "verdict": "unverifiable",
            "error": f"{type(exc).__name__}: {exc}",
        }

    fields = {}
    for name in IDENTIFIER_FIELDS:
        expected = attestation.get(name)
        observed = served.get(name)
        if observed is None:
            match = "unknown"
        else:
            match = observed == expected
        fields[name] = {"expected": expected, "observed": observed, "match": match}

    verdict = "match"
    if any(f["match"] is False for f in fields.values()):
        verdict = "mismatch"
    elif any(f["match"] == "unknown" for f in fields.values()):
        verdict = "unverifiable"
    return {"fields": fields, "verdict": verdict}
