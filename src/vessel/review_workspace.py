"""Private, provider-free human review workspace. No provider requests are made."""

import json
import threading
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit
from uuid import uuid4

from pydantic import Field, ValidationError, model_validator

from vessel.artifacts import atomic_json
from vessel.datasets import validate_dataset
from vessel.models import GoldAlternative, GoldRecord, Model, Review

CHECKS = {"source", "identity", "query", "alternatives", "requirements"}
PREPARER = "VESSEL AI preparation — no human approval"


class DraftAlternative(GoldAlternative):
    @model_validator(mode="after")
    def requirements(self):
        return self


class DraftRecord(GoldRecord):
    query: str = ""
    alternatives: list[DraftAlternative] = Field(default_factory=list)


class Event(Model):
    at: str
    kind: str
    reviewer: str
    note: str = ""
    content_sha256: str
    checks: list[str] = Field(default_factory=list)


class Task(Model):
    record: DraftRecord
    author: str
    revision: int = 1
    history: list[Event] = Field(default_factory=list)
    previous_versions: list[DraftRecord] = Field(default_factory=list)


class Workspace(Model):
    schema_version: Literal["vessel.review.v1"] = "vessel.review.v1"
    version: int = 0
    tasks: list[Task] = Field(default_factory=list, max_length=500)

    @model_validator(mode="after")
    def unique_ids(self):
        ids = [t.record.query_id for t in self.tasks]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate task IDs")
        return self


def identity(name: str) -> str:
    return " ".join(name.split()).casefold()


def readiness(task: Task) -> list[str]:
    try:
        record = GoldRecord.model_validate(task.record.model_dump(mode="json"))
    except ValidationError as error:
        return validation_messages(error)
    issues = validate_dataset([record])
    if not record.family_id.strip():
        issues.append("Add an evidence family.")
    if not record.query.strip():
        issues.append("Write a specific question.")
    ids = [a.evidence_id for a in record.alternatives]
    if any(not value.strip() for value in ids) or len(ids) != len(set(ids)):
        issues.append("Each acceptable answer needs a distinct, nonempty evidence identity.")
    for alternative in record.alternatives:
        if not alternative.verification_urls or not alternative.verification_notes.strip():
            issues.append("Each answer needs primary-source references and verification notes.")
        if not (
            alternative.document.urls or alternative.document.ids or alternative.document.sha256
        ):
            issues.append("Identify the source document.")
        if "visual" in alternative.required and not (
            alternative.visual.urls or alternative.visual.ids or alternative.visual.sha256
        ):
            issues.append("Identify the exact visual, not only its containing document.")
        if "localization" in alternative.required and not any(
            location.page_index is not None or location.figure or location.locator or location.bbox
            for location in alternative.locations
        ):
            issues.append("Add a specific figure, web locator or PDF page index.")
    if record.split == "evaluation":
        a = record.attestation
        if not (a.frozen_at and a.index_version and a.evidence_reference):
            issues.append("Evaluation tasks need a preserved index freeze reference.")
        elif a.frozen_at >= record.created_at:
            issues.append("The index freeze must precede query creation.")
    return issues


def validation_messages(error: ValidationError) -> list[str]:
    messages = []
    for issue in error.errors(include_input=False, include_url=False):
        loc = issue["loc"]
        label = " → ".join(str(v + 1) if isinstance(v, int) else v.replace("_", " ") for v in loc)
        messages.append(f"{label or 'Task'}: {issue['msg'].removeprefix('Value error, ')}")
    return messages


def task_status(task: Task) -> str:
    current = task.record.content_digest()
    decisions = [r for r in task.record.reviews if r.content_sha256 == current]
    latest = {}
    for review in sorted(decisions, key=lambda r: r.reviewed_at):
        latest[(identity(review.reviewer), review.role)] = review
    if any(r.decision == "changes_requested" for r in latest.values()):
        return "changes_requested"
    authors = {
        identity(r.reviewer)
        for r in latest.values()
        if r.role == "author" and r.decision == "approved"
    }
    independent = {
        identity(r.reviewer)
        for r in latest.values()
        if r.role == "independent" and r.decision == "approved"
    }
    if not readiness(task) and authors and independent and authors.isdisjoint(independent):
        return "approved"
    if authors:
        return "awaiting_review"
    return "draft"


def public_task(task: Task) -> dict:
    return {**task.model_dump(mode="json"), "status": task_status(task), "issues": readiness(task)}


class ReviewStore:
    def __init__(self, path: Path):
        self.path = path
        self.lock = threading.RLock()

    def read(self) -> Workspace:
        return (
            Workspace.model_validate_json(self.path.read_text())
            if self.path.exists()
            else Workspace()
        )

    def write(self, workspace: Workspace):
        workspace.version += 1
        atomic_json(self.path, workspace)

    def view(self):
        with self.lock:
            workspace = self.read()
            return {
                "schema_version": workspace.schema_version,
                "version": workspace.version,
                "tasks": [public_task(t) for t in workspace.tasks],
            }

    def load_prepared(self, records: list[DraftRecord]):
        """Add source-grounded proposals, preserving all existing tasks and decisions."""
        with self.lock:
            workspace = self.read()
            ids = {t.record.query_id for t in workspace.tasks}
            for record in records:
                if record.query_id in ids:
                    continue
                if record.reviews or record.synthetic or record.split != "development":
                    raise ValueError(
                        "Prepared proposals must be unreviewed real development tasks."
                    )
                task = Task(record=record, author=PREPARER)
                if readiness(task):
                    raise ValueError("Prepared proposal is incomplete: " + record.query_id)
                task.history.append(
                    Event(
                        at=datetime.now(UTC).isoformat(),
                        kind="prepared",
                        reviewer=PREPARER,
                        note=(
                            "AI-assisted primary-source preparation; "
                            "no human verification or approval."
                        ),
                        content_sha256=record.content_digest(),
                    )
                )
                workspace.tasks.append(task)
                ids.add(record.query_id)
            Workspace.model_validate(workspace.model_dump())
            if len(workspace.tasks) != len(self.read().tasks):
                self.write(workspace)
            return self.view()

    def mutate(self, action: str, body: dict):
        with self.lock:
            workspace = self.read()
            reviewer = str(body.get("reviewer", "")).strip()
            if not reviewer:
                raise ValueError("Enter your reviewer name first.")
            now = datetime.now(UTC)
            if action == "create":
                record = DraftRecord(
                    query_id="pilot-" + uuid4().hex[:8],
                    query="",
                    family_id="",
                    domain=body.get("domain", "economics"),
                    visual_type="chart",
                    query_type="descriptive",
                    split="development",
                    created_at=now,
                )
                task = Task(record=record, author=reviewer)
                workspace.tasks.append(task)
            else:
                task = next(
                    (t for t in workspace.tasks if t.record.query_id == body.get("task_id")), None
                )
                if not task:
                    raise ValueError("Task not found.")
                if task.revision != body.get("revision"):
                    raise ValueError("This task changed in another window. Reload before saving.")
                if action == "claim":
                    if task.author != PREPARER or task.record.reviews:
                        raise ValueError(
                            "Only unassigned prepared drafts can be taken for first review."
                        )
                    if identity(reviewer) == identity(PREPARER):
                        raise ValueError("Enter your own human reviewer name.")
                    task.author = reviewer
                elif action == "unclaim":
                    if identity(reviewer) != identity(task.author) or task.author == PREPARER:
                        raise ValueError("Only the current first reviewer can unclaim this task.")
                    if not any(event.kind == "prepared" for event in task.history):
                        raise ValueError("Only prepared tasks can return to the unassigned inbox.")
                    if task.record.reviews:
                        task.previous_versions.append(task.record.model_copy(deep=True))
                        task.record.reviews = []
                    task.author = PREPARER
                elif action == "save":
                    if identity(reviewer) != identity(task.author):
                        raise ValueError(
                            "Only this task's author can edit. Request changes instead."
                        )
                    record = DraftRecord.model_validate(body.get("record"))
                    if (
                        record.query_id != task.record.query_id
                        or record.created_at != task.record.created_at
                    ):
                        raise ValueError("Task identity and creation time cannot change.")
                    if record.content_digest() == task.record.content_digest():
                        return self.view()
                    task.previous_versions.append(task.record.model_copy(deep=True))
                    # Old decisions stay in history, never reactivate if content is restored.
                    record.reviews = []
                    task.record = record
                elif action == "decision":
                    role = body.get("role")
                    decision = body.get("decision")
                    notes = str(body.get("notes", "")).strip()
                    if role not in {"author", "independent"} or decision not in {
                        "approved",
                        "changes_requested",
                    }:
                        raise ValueError("Choose a valid review role and decision.")
                    if (role == "author") != (identity(reviewer) == identity(task.author)):
                        raise ValueError(
                            "Author and independent reviewer must be different people."
                        )
                    if not notes:
                        raise ValueError(
                            "Add source-verification notes or specific requested changes."
                        )
                    if body.get("human_attestation") is not True:
                        raise ValueError(
                            "Confirm that you personally made this human review decision."
                        )
                    if role == "independent" and not any(
                        r.role == "author"
                        and r.decision == "approved"
                        and r.content_sha256 == task.record.content_digest()
                        for r in task.record.reviews
                    ):
                        raise ValueError("The author must approve the current version first.")
                    if decision == "approved":
                        if set(body.get("checks", [])) != CHECKS:
                            raise ValueError("Complete all five evidence checks before approval.")
                        issues = readiness(task)
                        if issues:
                            raise ValueError("Task is not ready: " + "; ".join(issues))
                    task.record.reviews.append(
                        Review(
                            reviewer=reviewer,
                            role=role,
                            decision=decision,
                            content_sha256=task.record.content_digest(),
                            reviewed_at=now,
                            notes=notes,
                        )
                    )
                else:
                    raise ValueError("Unknown action.")
                task.revision += 1
            task.history.append(
                Event(
                    at=now.isoformat(),
                    kind=action if action != "decision" else body["decision"],
                    reviewer=reviewer,
                    note=str(body.get("notes", "")),
                    content_sha256=task.record.content_digest(),
                    checks=body.get("checks", []),
                )
            )
            Workspace.model_validate(workspace.model_dump())
            self.write(workspace)
            return self.view()

    def import_packet(self, body: dict):
        with self.lock:
            current = self.read()
            if body.get("version") != current.version:
                raise ValueError("Workspace changed. Reload before importing.")
            incoming = Workspace.model_validate(body["packet"])
            by_id = {t.record.query_id: t for t in current.tasks}
            for task in incoming.tasks:
                existing = by_id.get(task.record.query_id)
                if existing:
                    # A returned packet may extend our history, never overwrite divergent work.
                    history = task.history[: len(existing.history)]
                    if history != existing.history or task.revision < existing.revision:
                        raise ValueError(
                            f"Conflicting or older task {task.record.query_id}. "
                            "Keep both packets and resolve the conflict before importing."
                        )
                    if task.revision == existing.revision and task != existing:
                        raise ValueError(f"Conflicting task {task.record.query_id}.")
                by_id[task.record.query_id] = task
            merged = Workspace(tasks=list(by_id.values()), version=current.version)
            self.write(merged)
            return self.view()

    def export_dataset(self) -> str:
        with self.lock:
            tasks = self.read().tasks
            approved = [t for t in tasks if task_status(t) == "approved"]
            if not approved:
                raise ValueError("No tasks have current author and independent approval.")
            records = [
                GoldRecord.model_validate(t.record.model_dump(mode="json")) for t in approved
            ]
            issues = validate_dataset(records)
            if issues:
                raise ValueError("; ".join(issues))
            return "".join(r.model_dump_json() + "\n" for r in records)

    def export_file(self, kind: str) -> dict:
        with self.lock:
            workspace = self.read()
            if kind == "packet":
                content = workspace.model_dump_json(indent=2) + "\n"
                filename = f"vessel-review-packet-v{workspace.version}.json"
            elif kind == "dataset":
                content = self.export_dataset()
                filename = f"vessel-reviewed-gold-v{workspace.version}.jsonl"
            else:
                raise ValueError("Choose a review packet or reviewed gold export.")
            path = self.path.parent / "exports" / filename
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.with_suffix(path.suffix + ".tmp")
            tmp.write_text(content)
            tmp.replace(path)
            return {
                "file_path": str(path.resolve()),
                "filename": filename,
                "download_url": "/api/review/files/" + filename,
            }


def review_server(path: Path, assets: Path, port: int = 8788):
    store = ReviewStore(path)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def send(self, status, content, mime="application/json"):
            raw = content if isinstance(content, bytes) else content.encode()
            self.send_response(status)
            self.send_header("Content-Type", mime)
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(raw)

        def allowed(self):
            # Loopback-only plus Host/Origin checks prevent cross-site writes and rebinding.
            host = self.headers.get("Host", "")
            origin = self.headers.get("Origin")
            return host in {f"127.0.0.1:{port}", f"localhost:{port}"} and (
                not origin or origin in {f"http://127.0.0.1:{port}", f"http://localhost:{port}"}
            )

        def do_GET(self):
            if not self.allowed():
                return self.send(403, '{"error":"Local workspace access only."}')
            route = urlsplit(self.path).path
            try:
                if route == "/api/review/workspace":
                    return self.send(200, json.dumps(store.view()))
                if route == "/api/review/packet":
                    return self.send(200, store.read().model_dump_json())
                if route == "/api/review/dataset":
                    return self.send(200, store.export_dataset(), "application/x-ndjson")
                if route.startswith("/api/review/files/"):
                    directory = (store.path.parent / "exports").resolve()
                    file = (directory / route.removeprefix("/api/review/files/")).resolve()
                    if file.parent != directory or not file.is_file():
                        return self.send(404, '{"error":"Export not found."}')
                    mime = "application/x-ndjson" if file.suffix == ".jsonl" else "application/json"
                    return self.send(200, file.read_bytes(), mime)
                if route.startswith("/api/"):
                    return self.send(404, '{"error":"Not found."}')
                file = (assets / route.lstrip("/")).resolve()
                if not file.is_relative_to(assets.resolve()):
                    return self.send(403, '{"error":"Invalid path."}')
                if not file.is_file():
                    file = assets / "index.html"
                import mimetypes

                return self.send(
                    200,
                    file.read_bytes(),
                    mimetypes.guess_type(file.name)[0] or "application/octet-stream",
                )
            except (ValueError, OSError) as error:
                return self.send(400, json.dumps({"error": str(error)}))

        def do_POST(self):
            if not self.allowed():
                return self.send(403, '{"error":"Local workspace access only."}')
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 5 * 1024 * 1024:
                    return self.send(413, '{"error":"Packet exceeds the 5 MiB limit."}')
                body = json.loads(self.rfile.read(length))
                if not isinstance(body, dict):
                    raise ValueError("Expected a JSON object.")
                route = urlsplit(self.path).path
                if route == "/api/review/import":
                    result = store.import_packet(body)
                elif route == "/api/review/export":
                    result = store.export_file(body.get("kind"))
                elif route.startswith("/api/review/"):
                    result = store.mutate(route.rsplit("/", 1)[1], body)
                else:
                    return self.send(404, '{"error":"Not found."}')
                self.send(200, json.dumps(result))
            except ValidationError as error:
                self.send(400, json.dumps({"error": "\n".join(validation_messages(error))}))
            except (ValueError, TypeError, KeyError, OSError) as error:
                self.send(400, json.dumps({"error": str(error)}))

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    port = server.server_port
    return server


def serve_review(path: Path, assets: Path, port: int = 8788):
    proposals = Path(__file__).resolve().parents[2] / "data/prepared-review-development.jsonl"
    if proposals.is_file():
        ReviewStore(path).load_prepared(
            [
                DraftRecord.model_validate_json(line)
                for line in proposals.read_text().splitlines()
                if line.strip()
            ]
        )
    server = review_server(path, assets, port)
    print(f"Private review workspace: http://127.0.0.1:{server.server_port}/review", flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()
