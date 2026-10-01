import json
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from vessel.artifacts import atomic_json, sanitize
from vessel.cli import app
from vessel.datasets import save_dataset
from vessel.models import SearchResponse
from vessel.reporting import compare_reports, family_bootstrap, generate_report
from vessel.runner import run

ROOT = Path(__file__).resolve().parents[1]


def test_replay_e2e_and_deterministic_rescore(tmp_path):
    output = tmp_path / "run"
    manifest = run(
        ROOT / "data/synthetic-pilot.jsonl",
        ROOT / "configs/replay.yaml",
        output,
        ROOT / "tests/fixtures/replay.json",
    )
    assert manifest.requests == 0 and manifest.reserved_cost_usd == 0
    assert not manifest.publication_eligible
    first = generate_report(output)
    assert first == generate_report(output)
    assert all(m["10"]["median_latency_ms"] is None for m in first["summary"].values())
    assert "SYNTHETIC" in first["notice"]
    assert len(first["cells"]) == 80


def test_resume_identical(tmp_path):
    args = (
        ROOT / "data/synthetic-pilot.jsonl",
        ROOT / "configs/replay.yaml",
        tmp_path / "run",
        ROOT / "tests/fixtures/replay.json",
    )
    run(*args)
    assert run(*args, resume=True).status == "complete"
    with pytest.raises(ValueError):
        run(*args)


def test_changed_config_cannot_resume(tmp_path):
    config = tmp_path / "config.yaml"
    config.write_text((ROOT / "configs/replay.yaml").read_text())
    args = (
        ROOT / "data/synthetic-pilot.jsonl",
        config,
        tmp_path / "run",
        ROOT / "tests/fixtures/replay.json",
    )
    run(*args)
    data = yaml.safe_load(config.read_text())
    data["k"] = 5
    config.write_text(yaml.safe_dump(data))
    with pytest.raises(ValueError, match="identical"):
        run(*args, resume=True)


def test_archive_tamper_rejected(tmp_path):
    run(
        ROOT / "data/synthetic-pilot.jsonl",
        ROOT / "configs/replay.yaml",
        tmp_path / "run",
        ROOT / "tests/fixtures/replay.json",
    )
    path = next((tmp_path / "run/responses").glob("*.json"))
    data = json.loads(path.read_text())
    data["response"]["reason"] = "tampered"
    atomic_json(path, data)
    with pytest.raises(ValueError, match="integrity"):
        generate_report(tmp_path / "run")


def test_missing_credentials_dont_block_others(tmp_path, monkeypatch):
    for key in ("EXA_API_KEY", "KEENABLE_API_KEY", "SERPER_API_KEY", "EVIDENCE8_BASE_URL"):
        monkeypatch.delenv(key, raising=False)
    config = tmp_path / "config.yaml"
    config.write_text("providers:\n  - name: exa\n    request_cost_ceiling_usd: 0\n")
    manifest = run(ROOT / "data/synthetic-pilot.jsonl", config, tmp_path / "run")
    assert manifest.status == "incomplete" and manifest.requests == 0
    report = generate_report(tmp_path / "run")
    assert report["summary"]["exa"]["10"]["statuses"] == {"skipped": 20}
    assert report["paired"] == []


def test_crash_reservation_persisted(tmp_path, gold, monkeypatch):
    dataset = tmp_path / "gold.jsonl"
    save_dataset(dataset, [gold])
    config = tmp_path / "config.yaml"
    config.write_text(
        "max_cost_usd: 0.02\nproviders:\n  - name: exa\n    request_cost_ceiling_usd: 0.01\n"
    )

    class Crashing:
        def search(self, query, k, context):
            context.budget.reserve(0.01)
            raise KeyboardInterrupt()

    monkeypatch.setattr("vessel.runner.providers_for", lambda *a: {"exa": Crashing()})
    with pytest.raises(KeyboardInterrupt):
        run(dataset, config, tmp_path / "run")
    assert json.loads((tmp_path / "run/manifest.json").read_text())["requests"] == 1

    class Recovering:
        def search(self, query, k, context):
            context.budget.reserve(0.01)
            return SearchResponse(status="no_match", requests=1, reserved_cost_usd=0.01)

    monkeypatch.setattr("vessel.runner.providers_for", lambda *a: {"exa": Recovering()})
    assert run(dataset, config, tmp_path / "run", resume=True).requests == 2


def test_comparison_mismatch(tmp_path):
    run(
        ROOT / "data/synthetic-pilot.jsonl",
        ROOT / "configs/replay.yaml",
        tmp_path / "run",
        ROOT / "tests/fixtures/replay.json",
    )
    report = generate_report(tmp_path / "run")
    other = json.loads(json.dumps(report))
    other["manifest"]["dataset_sha256"] = "a" * 64
    with pytest.raises(ValueError, match="dataset_sha256"):
        compare_reports(report, other)


def test_bootstrap_family_deterministic():
    items = [("a", 1), ("a", 0), ("b", 1), ("c", 0)]
    assert family_bootstrap(items) == family_bootstrap(items)
    assert family_bootstrap([("a", 1)]) is None


def test_publication_cli_rejects_synthetic(tmp_path):
    run(
        ROOT / "data/synthetic-pilot.jsonl",
        ROOT / "configs/replay.yaml",
        tmp_path / "run",
        ROOT / "tests/fixtures/replay.json",
    )
    result = CliRunner().invoke(
        app, ["export", str(tmp_path / "run"), str(tmp_path / "published.json"), "--public-release"]
    )
    assert result.exit_code == 1
    assert not (tmp_path / "published.json").exists()
    assert "Publication rejected" in result.output


def test_redaction():
    clean = sanitize(
        {
            "Authorization": "secret",
            "link": "https://example.org/?api_key=secret",
            "value": "secret",
        },
        ("secret",),
    )
    assert "secret" not in json.dumps(clean)


def test_review_digest_stable_between_processes():
    import os
    import subprocess

    command = [
        str(ROOT / ".venv/bin/python"),
        "-c",
        "from pathlib import Path; from vessel.datasets import load_dataset; "
        'print(load_dataset(Path("data/synthetic-pilot.jsonl"))[0].content_digest())',
    ]
    values = [
        subprocess.check_output(command, cwd=ROOT, env={**os.environ, "PYTHONHASHSEED": seed})
        for seed in ["1", "42"]
    ]
    assert values[0] == values[1]


def test_provider_scoring_firewall():
    for path in (ROOT / "src/vessel/adapters").glob("*.py"):
        content = path.read_text()
        assert "GoldRecord" not in content
        assert "vessel.scoring" not in content


def test_human_audit_binds_exact_receipts(tmp_path):
    from vessel.auditing import audit_valid, record_audit
    from vessel.models import GoldRecord, RunManifest

    output = tmp_path / "run"
    run(
        ROOT / "data/synthetic-pilot.jsonl",
        ROOT / "configs/replay.yaml",
        output,
        ROOT / "tests/fixtures/replay.json",
    )
    record_audit(output, "actual-human-example", "Test-only audit binding, not a real release")
    manifest = RunManifest.model_validate_json((output / "manifest.json").read_text())
    records = [
        GoldRecord.model_validate(r) for r in json.loads((output / "dataset.json").read_text())
    ]
    assert audit_valid(output, manifest, records)
    assert not manifest.publication_eligible
    path = next((output / "responses").glob("*.json"))
    receipt = json.loads(path.read_text())
    receipt.pop("sha256")
    receipt["response"]["reason"] = "changed"
    from vessel.models import digest

    receipt["sha256"] = digest(receipt)
    atomic_json(path, receipt)
    assert not audit_valid(output, manifest, records)


def test_report_verifies_dataset_digest(tmp_path):
    output = tmp_path / "run"
    run(
        ROOT / "data/synthetic-pilot.jsonl",
        ROOT / "configs/replay.yaml",
        output,
        ROOT / "tests/fixtures/replay.json",
    )
    data = json.loads((output / "dataset.json").read_text())
    data[0]["query"] = "tampered"
    atomic_json(output / "dataset.json", data)
    with pytest.raises(ValueError, match="dataset digest"):
        generate_report(output)


def test_archived_code_and_lock_are_reproducible_and_verified(tmp_path):
    from vessel.artifacts import ArtifactStore
    from vessel.models import digest

    root = tmp_path / "run"
    manifest = run(
        ROOT / "data/synthetic-pilot.jsonl",
        ROOT / "configs/replay.yaml",
        root,
        ROOT / "tests/fixtures/replay.json",
    )
    store = ArtifactStore(root / "objects")
    assert digest(json.loads(store.read(manifest.code_artifact_sha256))) == manifest.code_sha256
    assert store.read(manifest.dependency_lock_sha256) == (ROOT / "uv.lock").read_bytes()
    path = root / "objects" / manifest.code_artifact_sha256[:2] / manifest.code_artifact_sha256
    path.write_text("tampered")
    with pytest.raises(ValueError, match="integrity"):
        generate_report(root)


def test_changed_dependency_lock_cannot_resume(tmp_path, monkeypatch):
    args = (
        ROOT / "data/synthetic-pilot.jsonl",
        ROOT / "configs/replay.yaml",
        tmp_path / "run",
        ROOT / "tests/fixtures/replay.json",
    )
    run(*args)
    monkeypatch.setattr("vessel.runner.dependency_lock_digest", lambda: "a" * 64)
    with pytest.raises(ValueError, match="dependency lock"):
        run(*args, resume=True)


def test_doctor_loads_local_env_without_secrets_or_network(tmp_path, monkeypatch):
    import os

    import httpx

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(os, "environ", dict(os.environ))
    for name in (
        "EVIDENCE8_BASE_URL",
        "EVIDENCE8_API_KEY",
        "KEENABLE_API_KEY",
        "EXA_API_KEY",
        "SERPER_API_KEY",
    ):
        os.environ.pop(name, None)
    (tmp_path / ".env").write_text(
        "EVIDENCE8_BASE_URL=http://127.0.0.1:8787\nEXA_API_KEY=fixture-secret-value\n"
    )
    monkeypatch.setattr(
        httpx.Client, "request", lambda *a, **k: pytest.fail("doctor made a request")
    )
    result = CliRunner().invoke(app, ["doctor", "--config", str(ROOT / "configs/live.yaml")])
    assert result.exit_code == 0, result.output
    assert "EXA_API_KEY: set" in result.output
    assert "SERPER_API_KEY: not set" in result.output
    assert "skipped until request cost ceilings" in result.output
    assert "fixture-secret-value" not in result.output and "127.0.0.1" not in result.output
    assert os.environ["EXA_API_KEY"] == "fixture-secret-value"


def test_doctor_preserves_exported_env_and_redacts_bad_config(tmp_path, monkeypatch):
    import os

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("EXA_API_KEY", "exported-fixture-secret")
    (tmp_path / ".env").write_text("EXA_API_KEY=file-fixture-secret\n")
    result = CliRunner().invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert os.environ["EXA_API_KEY"] == "exported-fixture-secret"
    assert "fixture-secret" not in result.output
    bad = tmp_path / "bad.yaml"
    bad.write_text("api_key: bad-config-fixture-secret\n")
    result = CliRunner().invoke(app, ["doctor", "--config", str(bad)])
    assert result.exit_code == 1
    assert "bad-config-fixture-secret" not in result.output


def test_doctor_redacts_malformed_yaml(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    path = tmp_path / "config.yaml"
    path.write_text("providers: [\napi_key: malformed-fixture-secret\n")
    result = CliRunner().invoke(app, ["doctor", "--config", str(path)])
    assert result.exit_code == 1
    assert "malformed-fixture-secret" not in result.output
    assert "RunConfig schema" in result.output
