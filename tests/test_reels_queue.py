import json
import subprocess
import sys
from pathlib import Path

from reels.config import load_reel_config
from reels.queue import run_queue


def _queue_payload(output_root: Path) -> dict:
    return {
        "name": "test_queue",
        "output_root": str(output_root),
        "batch_defaults": {
            "brand": "xeanvi",
            "template": "mistake",
            "visual_style": "market_grid",
            "duration_seconds": 18,
            "scene_count": 4,
            "generate_background": False,
            "generate_voiceover_placeholder": False,
            "render_mp4": False,
        },
        "runs": [
            {"run_id": "day_01", "items": [{"topic": "Why rules matter", "slug": "r1"}]},
            {"run_id": "day_02", "items": [{"topic": "Why journaling helps", "slug": "r2"}]},
        ],
    }


def _write_queue(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _cmd(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, "-m", "reels.queue", *args], cwd=cwd, check=False, text=True, capture_output=True)


def test_list_runs_prints_run_ids(tmp_path: Path) -> None:
    queue_path = tmp_path / "queue.json"
    _write_queue(queue_path, _queue_payload(tmp_path / "out"))
    result = _cmd("--input", str(queue_path), "--list-runs")
    assert result.returncode == 0
    assert "day_01" in result.stdout
    assert "day_02" in result.stdout


def test_run_id_executes_selected_run_and_creates_summary(tmp_path: Path) -> None:
    queue_path = tmp_path / "queue.json"
    out_root = tmp_path / "out"
    _write_queue(queue_path, _queue_payload(out_root))
    result = _cmd("--input", str(queue_path), "--run-id", "day_01")
    assert result.returncode == 0
    assert (out_root / "day_01" / "summary.json").exists()


def test_dry_run_creates_no_files(tmp_path: Path) -> None:
    queue_path = tmp_path / "queue.json"
    out_root = tmp_path / "out"
    _write_queue(queue_path, _queue_payload(out_root))
    result = _cmd("--input", str(queue_path), "--run-id", "day_01", "--dry-run")
    assert result.returncode == 0
    assert "planned_item slug=r1" in result.stdout
    assert not out_root.exists()


def test_dry_run_bad_top_level_boolean_fails(tmp_path: Path) -> None:
    payload = _queue_payload(tmp_path / "out")
    payload["batch_defaults"]["render_mp4"] = "false"
    queue_path = tmp_path / "queue.json"
    _write_queue(queue_path, payload)
    result = _cmd("--input", str(queue_path), "--run-id", "day_01", "--dry-run")
    assert result.returncode != 0
    assert "render_mp4 must be a boolean" in result.stdout
    assert not (tmp_path / "out").exists()


def test_dry_run_bad_item_level_boolean_fails(tmp_path: Path) -> None:
    payload = _queue_payload(tmp_path / "out")
    payload["runs"][0]["items"][0]["generate_background"] = "false"
    queue_path = tmp_path / "queue.json"
    _write_queue(queue_path, payload)
    result = _cmd("--input", str(queue_path), "--run-id", "day_01", "--dry-run")
    assert result.returncode != 0
    assert "items[0].generate_background must be a boolean" in result.stdout
    assert not (tmp_path / "out").exists()


def test_dry_run_rejects_duration_seconds_bool(tmp_path: Path) -> None:
    payload = _queue_payload(tmp_path / "out")
    payload["batch_defaults"]["duration_seconds"] = True
    queue_path = tmp_path / "queue.json"
    _write_queue(queue_path, payload)
    result = _cmd("--input", str(queue_path), "--run-id", "day_01", "--dry-run")
    assert result.returncode != 0
    assert "duration_seconds must be numeric" in result.stdout
    assert not (tmp_path / "out").exists()


def test_dry_run_rejects_scene_count_bool(tmp_path: Path) -> None:
    payload = _queue_payload(tmp_path / "out")
    payload["batch_defaults"]["scene_count"] = True
    queue_path = tmp_path / "queue.json"
    _write_queue(queue_path, payload)
    result = _cmd("--input", str(queue_path), "--run-id", "day_01", "--dry-run")
    assert result.returncode != 0
    assert "scene_count must be numeric" in result.stdout
    assert not (tmp_path / "out").exists()


def test_dry_run_rejects_duration_seconds_zero(tmp_path: Path) -> None:
    payload = _queue_payload(tmp_path / "out")
    payload["batch_defaults"]["duration_seconds"] = 0
    queue_path = tmp_path / "queue.json"
    _write_queue(queue_path, payload)
    result = _cmd("--input", str(queue_path), "--run-id", "day_01", "--dry-run")
    assert result.returncode != 0
    assert "duration_seconds must be > 0" in result.stdout
    assert not (tmp_path / "out").exists()


def test_dry_run_rejects_scene_count_one(tmp_path: Path) -> None:
    payload = _queue_payload(tmp_path / "out")
    payload["batch_defaults"]["scene_count"] = 1
    queue_path = tmp_path / "queue.json"
    _write_queue(queue_path, payload)
    result = _cmd("--input", str(queue_path), "--run-id", "day_01", "--dry-run")
    assert result.returncode != 0
    assert "scene_count must be at least 2" in result.stdout
    assert not (tmp_path / "out").exists()


def test_dry_run_rejects_duration_too_short_for_scene_count(tmp_path: Path) -> None:
    payload = _queue_payload(tmp_path / "out")
    payload["batch_defaults"]["duration_seconds"] = 5
    payload["batch_defaults"]["scene_count"] = 4
    queue_path = tmp_path / "queue.json"
    _write_queue(queue_path, payload)
    result = _cmd("--input", str(queue_path), "--run-id", "day_01", "--dry-run")
    assert result.returncode != 0
    assert "duration_seconds is too short for the requested scene_count" in result.stdout
    assert not (tmp_path / "out").exists()


def test_dry_run_banned_topic_fails(tmp_path: Path) -> None:
    payload = _queue_payload(tmp_path / "out")
    payload["runs"][0]["items"][0]["topic"] = "Risk-free strategy for guaranteed profits"
    queue_path = tmp_path / "queue.json"
    _write_queue(queue_path, payload)
    result = _cmd("--input", str(queue_path), "--run-id", "day_01", "--dry-run")
    assert result.returncode != 0
    assert "contains prohibited marketing/compliance phrase" in result.stdout
    assert not (tmp_path / "out").exists()


def test_dry_run_duplicate_slug_fails(tmp_path: Path) -> None:
    payload = _queue_payload(tmp_path / "out")
    payload["runs"][0]["items"].append({"topic": "Another topic", "slug": "r1"})
    queue_path = tmp_path / "queue.json"
    _write_queue(queue_path, payload)
    result = _cmd("--input", str(queue_path), "--run-id", "day_01", "--dry-run")
    assert result.returncode != 0
    assert "duplicate slug detected: r1" in result.stdout
    assert not (tmp_path / "out").exists()


def test_dry_run_unsupported_visual_style_fails(tmp_path: Path) -> None:
    payload = _queue_payload(tmp_path / "out")
    payload["batch_defaults"]["visual_style"] = "nope_style"
    queue_path = tmp_path / "queue.json"
    _write_queue(queue_path, payload)
    result = _cmd("--input", str(queue_path), "--run-id", "day_01", "--dry-run")
    assert result.returncode != 0
    assert "unsupported visual_style" in result.stdout
    assert not (tmp_path / "out").exists()


def test_next_runs_first_missing_run(tmp_path: Path) -> None:
    queue_path = tmp_path / "queue.json"
    out_root = tmp_path / "out"
    _write_queue(queue_path, _queue_payload(out_root))
    result = _cmd("--input", str(queue_path), "--next")
    assert result.returncode == 0
    assert (out_root / "day_01" / "summary.json").exists()


def test_next_skips_completed_run(tmp_path: Path) -> None:
    queue_path = tmp_path / "queue.json"
    out_root = tmp_path / "out"
    _write_queue(queue_path, _queue_payload(out_root))
    (out_root / "day_01").mkdir(parents=True)
    (out_root / "day_01" / "summary.json").write_text("{}", encoding="utf-8")
    result = _cmd("--input", str(queue_path), "--next")
    assert result.returncode == 0
    assert "executed_run_id=day_02" in result.stdout
    assert (out_root / "day_02" / "summary.json").exists()


def test_duplicate_run_id_rejected(tmp_path: Path) -> None:
    payload = _queue_payload(tmp_path / "out")
    payload["runs"][1]["run_id"] = "day_01"
    queue_path = tmp_path / "queue.json"
    _write_queue(queue_path, payload)
    result = _cmd("--input", str(queue_path), "--list-runs")
    assert result.returncode != 0
    assert "duplicate run_id" in result.stdout


def test_missing_run_id_rejected(tmp_path: Path) -> None:
    payload = _queue_payload(tmp_path / "out")
    payload["runs"][0]["run_id"] = ""
    queue_path = tmp_path / "queue.json"
    _write_queue(queue_path, payload)
    result = _cmd("--input", str(queue_path), "--list-runs")
    assert result.returncode != 0
    assert "run_id must be non-empty" in result.stdout


def test_selected_unknown_run_id_fails(tmp_path: Path) -> None:
    queue_path = tmp_path / "queue.json"
    _write_queue(queue_path, _queue_payload(tmp_path / "out"))
    result = _cmd("--input", str(queue_path), "--run-id", "day_99")
    assert result.returncode != 0
    assert "selected run_id not found" in result.stdout


def test_queue_generated_json_loads_via_config_loader(tmp_path: Path) -> None:
    payload = _queue_payload(tmp_path / "out")
    run_queue(payload, run_id="day_01")
    cfg = load_reel_config(tmp_path / "out" / "day_01" / "r1" / "r1.json")
    assert cfg.title


def test_batch_defaults_applied(tmp_path: Path) -> None:
    payload = _queue_payload(tmp_path / "out")
    payload["batch_defaults"]["scene_count"] = 3
    payload["batch_defaults"]["duration_seconds"] = 12
    run_queue(payload, run_id="day_01")
    cfg = load_reel_config(tmp_path / "out" / "day_01" / "r1" / "r1.json")
    assert len(cfg.scenes) == 3
    assert cfg.duration_seconds == 12


def test_run_level_item_overrides_work(tmp_path: Path) -> None:
    payload = _queue_payload(tmp_path / "out")
    payload["runs"][0]["items"][0]["scene_count"] = 2
    payload["runs"][0]["items"][0]["duration_seconds"] = 8
    run_queue(payload, run_id="day_01")
    cfg = load_reel_config(tmp_path / "out" / "day_01" / "r1" / "r1.json")
    assert len(cfg.scenes) == 2
    assert cfg.duration_seconds == 8
