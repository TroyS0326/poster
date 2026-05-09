from __future__ import annotations

import json
import random
import time
from pathlib import Path

import requests


class ComfyUIVideoError(RuntimeError):
    pass


def check_comfyui_health(api_url: str) -> bool:
    try:
        r = requests.get(f"{api_url.rstrip('/')}/system_stats", timeout=5)
        return r.ok
    except Exception:
        return False


def generate_comfy_video_clip(prompt: str, output_path: Path, *, api_url: str, workflow_path: Path, prompt_node_id: str, negative_prompt_node_id: str | None, seed_node_id: str | None, width: int, height: int, frames: int, fps: int, timeout_seconds: int, poll_seconds: int) -> Path:
    del width, height, frames, fps
    if not workflow_path.exists():
        raise ComfyUIVideoError(f"ComfyUI workflow missing: {workflow_path}")
    try:
        workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ComfyUIVideoError(f"Unable to load ComfyUI workflow: {exc}") from exc
    if prompt_node_id not in workflow:
        raise ComfyUIVideoError(f"Configured COMFYUI_PROMPT_NODE_ID not found in workflow: {prompt_node_id}")

    workflow[prompt_node_id].setdefault("inputs", {})["text"] = prompt
    if negative_prompt_node_id:
        if negative_prompt_node_id not in workflow:
            raise ComfyUIVideoError(f"Configured COMFYUI_NEGATIVE_PROMPT_NODE_ID not found in workflow: {negative_prompt_node_id}")
        workflow[negative_prompt_node_id].setdefault("inputs", {})["text"] = "no readable text, no logos, no broker UI, no financial advice"
    if seed_node_id:
        if seed_node_id not in workflow:
            raise ComfyUIVideoError(f"Configured COMFYUI_SEED_NODE_ID not found in workflow: {seed_node_id}")
        workflow[seed_node_id].setdefault("inputs", {})["seed"] = random.randint(1, 2**31 - 1)

    try:
        sub = requests.post(f"{api_url.rstrip('/')}/prompt", json={"prompt": workflow}, timeout=30)
        sub.raise_for_status()
        prompt_id = sub.json().get("prompt_id")
    except requests.RequestException as exc:
        raise ComfyUIVideoError(f"ComfyUI unreachable or prompt submission failed: {exc}") from exc
    if not prompt_id:
        raise ComfyUIVideoError("ComfyUI prompt submission failed: missing prompt_id")

    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            hist = requests.get(f"{api_url.rstrip('/')}/history/{prompt_id}", timeout=30)
            hist.raise_for_status()
            payload = hist.json().get(prompt_id, {})
        except requests.RequestException as exc:
            raise ComfyUIVideoError(f"Failed polling ComfyUI history: {exc}") from exc
        if payload.get("status", {}).get("status_str") == "error":
            raise ComfyUIVideoError("ComfyUI generation failed")
        outputs = payload.get("outputs", {})
        for node in outputs.values():
            for v in node.get("videos", []):
                filename = v.get("filename")
                subfolder = v.get("subfolder", "")
                typ = v.get("type", "output")
                if filename:
                    view = requests.get(f"{api_url.rstrip('/')}/view", params={"filename": filename, "subfolder": subfolder, "type": typ}, timeout=120)
                    view.raise_for_status()
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    output_path.write_bytes(view.content)
                    return output_path
        time.sleep(poll_seconds)
    raise ComfyUIVideoError(f"Timed out waiting for ComfyUI generation after {timeout_seconds}s")
