from __future__ import annotations
import argparse, json, os, time
from pathlib import Path

from reels.autopost import run_autopost
from reels.queue import load_queue_input, validate_queue_payload, _resolve_output_root


def _state_path() -> Path:
    return Path(os.getenv("REELS_SCHEDULER_STATE_PATH", "outputs/reels_scheduler_state.json"))


def _load_state(path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_text(encoding='utf-8'))
    return {"posted": {}, "failed": {}}


def _save_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2), encoding='utf-8')


def _iter_items(payload: dict):
    for run in validate_queue_payload(payload):
        for item in run["items"]:
            yield run["run_id"], str(item.get("slug") or item.get("topic","")).strip().lower().replace(" ","_")


def _next_pending(payload: dict, state: dict, force_retry_failed: bool):
    posted = set(state.get("posted", {}).keys())
    failed = set(state.get("failed", {}).keys())
    for run_id, slug in _iter_items(payload):
        key=f"{run_id}:{slug}"
        if key in posted:
            continue
        if key in failed and not force_retry_failed:
            continue
        return run_id, slug, key
    return None


def run_scheduler(queue: Path, public_base_url: str, interval_hours: float = 8, once: bool = False, dry_run: bool = False, force_retry_failed: bool = False):
    payload = load_queue_input(queue)
    state_file = _state_path()
    while True:
        state = _load_state(state_file)
        nxt = _next_pending(payload, state, force_retry_failed)
        if not nxt:
            if once:
                return {"processed": 0}
            time.sleep(max(60, interval_hours * 3600))
            continue
        run_id, slug, key = nxt
        result = run_autopost(queue, run_id, public_base_url, limit=1, dry_run=dry_run)
        item = result.get("items", [{}])[0] if result.get("items") else {}
        ok = dry_run or item.get("publish") is not None
        if ok:
            state.setdefault("posted", {})[key] = {"run_id": run_id, "slug": slug, "ts": time.time()}
            state.get("failed", {}).pop(key, None)
        else:
            state.setdefault("failed", {})[key] = {"run_id": run_id, "slug": slug, "ts": time.time(), "status": item.get("status")}
        _save_state(state_file, state)
        if once:
            return {"processed": 1, "run_id": run_id, "slug": slug}
        time.sleep(interval_hours * 3600)


def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument('--queue', required=True)
    p.add_argument('--public-base-url', required=True)
    p.add_argument('--interval-hours', type=float, default=float(os.getenv('REELS_POST_INTERVAL_HOURS','8')))
    p.add_argument('--once', action='store_true')
    p.add_argument('--dry-run', action='store_true')
    p.add_argument('--force-retry-failed', action='store_true')
    a=p.parse_args()
    run_scheduler(Path(a.queue), a.public_base_url, a.interval_hours, a.once, a.dry_run, a.force_retry_failed)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
