from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from reels.batch import plan_batch, run_batch

DEFAULT_OUTPUT_ROOT = "outputs/queue"


def load_queue_input(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"queue input file not found: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("queue input must be an object")
    return payload


def validate_queue_payload(payload: dict[str, Any]) -> list[dict[str, Any]]:
    runs = payload.get("runs")
    if not isinstance(runs, list) or not runs:
        raise ValueError("runs must be a non-empty list")

    seen: set[str] = set()
    for idx, run in enumerate(runs):
        if not isinstance(run, dict):
            raise ValueError(f"runs[{idx}] must be an object")
        run_id = str(run.get("run_id", "")).strip()
        if not run_id:
            raise ValueError(f"runs[{idx}].run_id must be non-empty")
        if run_id in seen:
            raise ValueError(f"duplicate run_id detected: {run_id}")
        seen.add(run_id)

        items = run.get("items")
        if not isinstance(items, list) or not items:
            raise ValueError(f"runs[{idx}].items must be a non-empty list")
    return runs


def _resolve_output_root(payload: dict[str, Any]) -> Path:
    output_root = payload.get("output_root", DEFAULT_OUTPUT_ROOT)
    return Path(str(output_root))


def _build_batch_payload(payload: dict[str, Any], run: dict[str, Any]) -> dict[str, Any]:
    batch_payload = dict(payload.get("batch_defaults", {}))
    batch_payload["items"] = run["items"]
    return batch_payload


def _select_run(runs: list[dict[str, Any]], run_id: str) -> dict[str, Any]:
    for run in runs:
        if run["run_id"] == run_id:
            return run
    raise ValueError(f"selected run_id not found: {run_id}")


def _find_next_pending_run(payload: dict[str, Any], runs: list[dict[str, Any]]) -> dict[str, Any] | None:
    output_root = _resolve_output_root(payload)
    for run in runs:
        summary_path = output_root / run["run_id"] / "summary.json"
        if not summary_path.exists():
            return run
    return None


def run_queue(payload: dict[str, Any], *, run_id: str, dry_run: bool = False) -> dict[str, Any] | None:
    runs = validate_queue_payload(payload)
    run = _select_run(runs, run_id)
    batch_payload = _build_batch_payload(payload, run)
    output_dir = _resolve_output_root(payload) / run_id
    if dry_run:
        plan = plan_batch(batch_payload, output_dir)
        print(f"dry_run=true run_id={run_id} output_dir={plan['output_dir']} item_count={plan['item_count']}")
        for item in plan["items"]:
            print(f"planned_item slug={item['slug']} json_path={item['json_path']}")
        return None
    return run_batch(batch_payload, output_dir)


def main() -> int:
    parser = argparse.ArgumentParser(description="Local queue scheduler for reels batch runs")
    parser.add_argument("--input", required=True, help="Queue JSON input path")
    parser.add_argument("--run-id", help="Run ID to execute")
    parser.add_argument("--list-runs", action="store_true", help="List available run IDs")
    parser.add_argument("--dry-run", action="store_true", help="Validate and print selected run without writing output")
    parser.add_argument("--next", dest="next_pending", action="store_true", help="Execute the next pending run")
    args = parser.parse_args()

    if sum([bool(args.list_runs), bool(args.run_id), bool(args.next_pending)]) != 1:
        print("ERROR: choose exactly one mode: --list-runs, --run-id, or --next")
        return 2

    try:
        payload = load_queue_input(Path(args.input))
        runs = validate_queue_payload(payload)

        if args.list_runs:
            for run in runs:
                print(f"{run['run_id']} ({len(run['items'])} items)")
            return 0

        if args.next_pending:
            run = _find_next_pending_run(payload, runs)
            if run is None:
                print("All queue runs already completed (summary.json exists for every run).")
                return 0
            result = run_queue(payload, run_id=run["run_id"], dry_run=False)
            print(f"executed_run_id={run['run_id']}")
            print(f"summary_path={_resolve_output_root(payload) / run['run_id'] / 'summary.json'}")
            return 0 if isinstance(result, dict) else 2

        if not args.run_id:
            raise ValueError("--run-id is required when not using --list-runs or --next")

        result = run_queue(payload, run_id=args.run_id, dry_run=args.dry_run)
        if args.dry_run:
            return 0

        print(f"executed_run_id={args.run_id}")
        print(f"summary_path={_resolve_output_root(payload) / args.run_id / 'summary.json'}")
        return 0 if isinstance(result, dict) else 2
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
