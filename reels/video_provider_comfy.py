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


def _set_prompt_value(node: dict, prompt_value: str) -> None:
    inputs = node.setdefault("inputs", {})
    if "text" in inputs:
        inputs["text"] = prompt_value
    elif "value" in inputs:
        inputs["value"] = prompt_value
    else:
        inputs["text"] = prompt_value


def _set_seed_value(node: dict, seed_value: int) -> None:
    inputs = node.setdefault("inputs", {})
    if "seed" in inputs:
        inputs["seed"] = seed_value
    elif "noise_seed" in inputs:
        inputs["noise_seed"] = seed_value
    else:
        inputs["seed"] = seed_value


def _download_if_present(node: dict, key: str, api_url: str, output_path: Path) -> bool:
    for item in node.get(key, []):
        filename = item.get("filename")
        subfolder = item.get("subfolder", "")
        typ = item.get("type", "output")
        if not filename:
            continue
        view = requests.get(
            f"{api_url.rstrip('/')}/view",
            params={"filename": filename, "subfolder": subfolder, "type": typ},
            timeout=120,
        )
        view.raise_for_status()
        if not view.content:
            raise ComfyUIVideoError(f"ComfyUI returned empty content for {key} output: {filename}")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(view.content)
        return True
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

    _set_prompt_value(workflow[prompt_node_id], prompt)
    if negative_prompt_node_id:
        if negative_prompt_node_id not in workflow:
            raise ComfyUIVideoError(f"Configured COMFYUI_NEGATIVE_PROMPT_NODE_ID not found in workflow: {negative_prompt_node_id}")
        _set_prompt_value(workflow[negative_prompt_node_id], "no readable text, no logos, no broker UI, no financial advice")
    if seed_node_id:
        if seed_node_id not in workflow:
            raise ComfyUIVideoError(f"Configured COMFYUI_SEED_NODE_ID not found in workflow: {seed_node_id}")
        _set_seed_value(workflow[seed_node_id], random.randint(1, 2**31 - 1))

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
            if _download_if_present(node, "videos", api_url, output_path):
                return output_path
            if _download_if_present(node, "gifs", api_url, output_path):
                return output_path
            if _download_if_present(node, "images", api_url, output_path):
                return output_path
        if outputs:
            output_keys = sorted({key for node in outputs.values() for key in node.keys()})
            raise ComfyUIVideoError(f"ComfyUI outputs had no downloadable entries; output keys: {output_keys}")
        time.sleep(poll_seconds)
    raise ComfyUIVideoError(f"Timed out waiting for ComfyUI generation after {timeout_seconds}s")
