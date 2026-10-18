import httpx
import pytest

from vessel.freeze import IDENTIFIER_FIELDS, check_freeze

ATTESTATION = {
    "corpus_hash": "sha256:aaa",
    "index_hash": "sha256:bbb",
    "index_version": "idx-42",
    "code_commit": "deadbee",
    "retrieval_settings": {"reporting_period_behavior": "exact period match, no fallback"},
    "frozen_at": "2026-10-18T00:00:00Z",
    "attested_by": "Richardson Dackam",
}


def _client(served: dict | None, status: int = 200) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/version"
        if served is None:
            return httpx.Response(404)
        return httpx.Response(status, json=served)

    return httpx.Client(transport=httpx.MockTransport(handler))


def test_freeze_match():
    client = _client({k: ATTESTATION[k] for k in IDENTIFIER_FIELDS})
    result = check_freeze(ATTESTATION, "http://127.0.0.1:8787", client)
    assert result["verdict"] == "match"
    assert all(f["match"] is True for f in result["fields"].values())


def test_freeze_mismatch_blocks():
    served = {k: ATTESTATION[k] for k in IDENTIFIER_FIELDS}
    served["index_hash"] = "sha256:changed"
    client = _client(served)
    result = check_freeze(ATTESTATION, "http://127.0.0.1:8787", client)
    assert result["verdict"] == "mismatch"
    assert result["fields"]["index_hash"]["match"] is False
    assert result["fields"]["index_hash"]["observed"] == "sha256:changed"


def test_freeze_missing_endpoint_is_unverifiable():
    client = _client(None)
    result = check_freeze(ATTESTATION, "http://127.0.0.1:8787", client)
    assert result["verdict"] == "unverifiable"
    assert all(f["match"] == "unknown" for f in result["fields"].values())


def test_freeze_partial_identifiers_is_unverifiable():
    served = {"index_version": ATTESTATION["index_version"]}
    client = _client(served)
    result = check_freeze(ATTESTATION, "http://127.0.0.1:8787", client)
    assert result["verdict"] == "unverifiable"
    assert result["fields"]["index_version"]["match"] is True
    assert result["fields"]["corpus_hash"]["match"] == "unknown"


def test_freeze_unreachable_service_is_unverifiable():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    result = check_freeze(ATTESTATION, "http://127.0.0.1:8787", client)
    assert result["verdict"] == "unverifiable"
    assert "ConnectError" in result["error"]
