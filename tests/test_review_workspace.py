import json
import threading
from pathlib import Path

import httpx
import pytest

from vessel.datasets import load_dataset
from vessel.review_workspace import CHECKS, ReviewStore, Workspace, review_server


@pytest.fixture
def store(tmp_path):
    return ReviewStore(tmp_path / "workspace.json")


def create_ready(store):
    view = store.mutate("create", {"reviewer": "Alice"})
    task = view["tasks"][0]
    record = json.loads(Path("data/synthetic-pilot.jsonl").read_text().splitlines()[0])
    for alternative in record["alternatives"]:
        alternative["verification_urls"] = alternative["document"]["urls"]
        alternative["verification_notes"] = "Synthetic test reference, not actual source review."
    record.update(
        query_id=task["record"]["query_id"],
        created_at=task["record"]["created_at"],
        split="development",
        reviews=[],
        attestation={"bucket": "unknown"},
    )
    view = store.mutate(
        "save",
        {
            "reviewer": "Alice",
            "task_id": task["record"]["query_id"],
            "revision": task["revision"],
            "record": record,
        },
    )
    return view["tasks"][0]


def decision(store, task, reviewer="Alice", role="author", outcome="approved", **overrides):
    body = {
        "task_id": task["record"]["query_id"],
        "revision": task["revision"],
        "reviewer": reviewer,
        "role": role,
        "decision": outcome,
        "checks": sorted(CHECKS),
        "notes": "Synthetic workflow test; not a real human approval.",
        "human_attestation": True,
    }
    return store.mutate("decision", {**body, **overrides})["tasks"][0]


def test_review_export_matches_python_digest_and_survives_reload(store, tmp_path):
    task = create_ready(store)
    assert task["issues"] == []
    task = decision(store, task)
    assert task["status"] == "awaiting_review"
    task = decision(store, task, reviewer="Bob", role="independent")
    assert task["status"] == "approved"
    assert ReviewStore(store.path).view() == store.view()
    path = tmp_path / "gold.jsonl"
    path.write_text(store.export_dataset())
    record = load_dataset(path)[0]
    assert record.reviewed()
    assert all(r.content_sha256 == record.content_digest() for r in record.reviews)
    saved = store.export_file("dataset")
    assert Path(saved["file_path"]).read_text() == store.export_dataset()
    packet = store.export_file("packet")
    assert Workspace.model_validate_json(Path(packet["file_path"]).read_text()) == store.read()


def test_draft_can_be_saved_without_fake_gold_and_cannot_be_approved(store):
    task = store.mutate("create", {"reviewer": "Alice"})["tasks"][0]
    assert task["issues"]
    with pytest.raises(ValueError, match="not ready"):
        decision(store, task)
    with pytest.raises(ValueError, match="No tasks"):
        store.export_dataset()


@pytest.mark.parametrize("reviewer", ["Alice", " alice ", "ALICE"])
def test_author_cannot_be_own_independent_reviewer(store, reviewer):
    task = decision(store, create_ready(store))
    with pytest.raises(ValueError, match="different people"):
        decision(store, task, reviewer=reviewer, role="independent")


def test_independent_cannot_edit_or_review_before_author(store):
    task = create_ready(store)
    with pytest.raises(ValueError, match="author must approve"):
        decision(store, task, reviewer="Bob", role="independent")
    with pytest.raises(ValueError, match="Only this task's author"):
        store.mutate(
            "save",
            {
                "reviewer": "Bob",
                "task_id": task["record"]["query_id"],
                "revision": task["revision"],
                "record": task["record"],
            },
        )


def test_all_checks_notes_and_human_attestation_required(store):
    task = create_ready(store)
    for override, message in [
        ({"checks": []}, "five"),
        ({"notes": ""}, "notes"),
        ({"human_attestation": False}, "personally"),
    ]:
        with pytest.raises(ValueError, match=message):
            decision(store, task, **override)


def test_revision_invalidates_approvals_preserves_history_and_conflicts(store):
    task = decision(store, create_ready(store))
    task = decision(store, task, reviewer="Bob", role="independent")
    old = task["revision"]
    task["record"]["query"] += " Revised question."
    task = store.mutate(
        "save",
        {
            "reviewer": "Alice",
            "task_id": task["record"]["query_id"],
            "revision": old,
            "record": task["record"],
        },
    )["tasks"][0]
    assert task["status"] == "draft"
    assert task["record"]["reviews"] == []
    assert len(task["previous_versions"][-1]["reviews"]) == 2
    assert task["previous_versions"]
    with pytest.raises(ValueError, match="another window"):
        decision(store, task, revision=old)


def test_restoring_old_content_does_not_reactivate_old_approvals(store):
    task = decision(store, create_ready(store))
    task = decision(store, task, reviewer="Bob", role="independent")
    original = json.loads(json.dumps(task["record"]))
    task["record"]["query"] += " A temporary revision."
    changed = store.mutate(
        "save",
        {
            "reviewer": "Alice",
            "task_id": task["record"]["query_id"],
            "revision": task["revision"],
            "record": task["record"],
        },
    )["tasks"][0]
    restored = store.mutate(
        "save",
        {
            "reviewer": "Alice",
            "task_id": task["record"]["query_id"],
            "revision": changed["revision"],
            "record": original,
        },
    )["tasks"][0]
    assert restored["status"] == "draft"
    assert restored["record"]["reviews"] == []
    with pytest.raises(ValueError, match="No tasks"):
        store.export_dataset()


def test_requested_changes_block_then_fresh_reviews_resolve(store):
    task = decision(store, create_ready(store))
    task = decision(
        store, task, reviewer="Bob", role="independent", outcome="changes_requested", checks=[]
    )
    assert task["status"] == "changes_requested"
    task = decision(store, task, reviewer="Bob", role="independent")
    assert task["status"] == "approved"


def test_packet_transfer_and_safe_return_merge(store, tmp_path):
    decision(store, create_ready(store))
    peer = ReviewStore(tmp_path / "peer.json")
    peer.import_packet({"version": 0, "packet": store.read().model_dump(mode="json")})
    decision(peer, peer.view()["tasks"][0], reviewer="Bob", role="independent")
    view = store.import_packet(
        {"version": store.read().version, "packet": peer.read().model_dump(mode="json")}
    )
    assert view["tasks"][0]["status"] == "approved"
    with pytest.raises(ValueError, match="Workspace changed"):
        store.import_packet({"version": 0, "packet": peer.read().model_dump(mode="json")})


def test_packet_rejects_provider_results_and_duplicates(store):
    create_ready(store)
    packet = store.read().model_dump(mode="json")
    packet["tasks"][0]["record"]["provider_results"] = ["must stay blind"]
    with pytest.raises(ValueError):
        Workspace.model_validate(packet)
    packet = store.read().model_dump(mode="json")
    packet["tasks"].append(packet["tasks"][0])
    with pytest.raises(ValueError, match="Duplicate"):
        Workspace.model_validate(packet)


def test_divergent_packet_cannot_overwrite_local_work(store, tmp_path):
    task = decision(store, create_ready(store))
    peer = ReviewStore(tmp_path / "peer.json")
    peer.import_packet({"version": 0, "packet": store.read().model_dump(mode="json")})
    task["record"]["query"] += " Local edit."
    store.mutate(
        "save",
        {
            "reviewer": "Alice",
            "task_id": task["record"]["query_id"],
            "revision": task["revision"],
            "record": task["record"],
        },
    )
    decision(peer, peer.view()["tasks"][0], reviewer="Bob", role="independent")
    with pytest.raises(ValueError, match="Conflicting"):
        store.import_packet(
            {"version": store.read().version, "packet": peer.read().model_dump(mode="json")}
        )


def test_loopback_http_service_protects_writes_and_serves_review_route(tmp_path):
    assets = tmp_path / "dist"
    assets.mkdir()
    (assets / "index.html").write_text("<main>Human review</main>")
    server = review_server(tmp_path / "workspace.json", assets, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with httpx.Client(base_url=f"http://127.0.0.1:{server.server_port}") as client:
            assert client.get("/review").text == "<main>Human review</main>"
            assert client.get("/api/review/workspace").json()["tasks"] == []
            assert (
                client.get("/api/review/workspace", headers={"Host": "evil.example"}).status_code
                == 403
            )
            assert (
                client.post(
                    "/api/review/create",
                    headers={"Origin": "https://evil.example"},
                    json={"reviewer": "Alice"},
                ).status_code
                == 403
            )
            assert client.get("/api/review/workspace").json()["tasks"] == []
            assert client.post("/api/review/create", json={"reviewer": "Alice"}).status_code == 200
            assert (
                client.post("/api/review/import", json={"packet": [], "version": 1}).status_code
                == 400
            )
            assert client.get("/api/review/dataset").status_code == 400
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()
