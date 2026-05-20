"""ComfyUI / LTX-Video provider — generates portrait mp4 clips via local RTX 3090."""
import json, logging, os, random, subprocess, tempfile, time
from pathlib import Path
import requests

logger = logging.getLogger(__name__)

COMFYUI_URL   = os.getenv("COMFYUI_API_URL",      "http://127.0.0.1:8189")
WORKFLOW_PATH = os.getenv("COMFYUI_WORKFLOW_PATH", "workflows/ltx_t2v.json")
FPS           = 25
GEN_TIMEOUT   = int(os.getenv("COMFYUI_TIMEOUT",  "300"))


def _frames_for_duration(seconds: float) -> int:
    """Closest valid num_frames (must be n*8+1) to target duration."""
    n = max(0, round((int(seconds * FPS) - 1) / 8))
    return n * 8 + 1   # 4s→97  5s→121  8s→193


def _load_workflow() -> dict:
    path = Path(WORKFLOW_PATH)
    if not path.is_absolute():
        path = Path(__file__).parent.parent / WORKFLOW_PATH
    with open(path) as f:
        return json.load(f)


def generate_video(prompt: str, duration_secs: float = 5.0, seed: int | None = None) -> str:
    """Generate a clip with LTX Video. Returns path to local mp4."""
    if seed is None:
        seed = random.randint(0, 2**32 - 1)

    num_frames = _frames_for_duration(duration_secs)
    logger.info("ComfyUI: %d frames (%.1fs) seed=%d", num_frames, duration_secs, seed)

    wf = _load_workflow()
    wf["3"]["inputs"]["text"]        = prompt
    wf["10"]["inputs"]["noise_seed"] = seed
    wf["11"]["inputs"]["num_frames"] = num_frames

    try:
        resp = requests.post(f"{COMFYUI_URL}/prompt", json={"prompt": wf}, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(f"ComfyUI submit failed: {e}") from e

    prompt_id = resp.json()["prompt_id"]
    logger.info("ComfyUI: queued %s", prompt_id)

    deadline, output_info = time.time() + GEN_TIMEOUT, None
    while time.time() < deadline:
        time.sleep(3)
        try:
            hist = requests.get(f"{COMFYUI_URL}/history/{prompt_id}", timeout=10).json()
        except requests.RequestException:
            continue
        if prompt_id in hist:
            job = hist[prompt_id]
            if job.get("status", {}).get("status_str") == "error":
                raise RuntimeError(f"ComfyUI error: {job['status'].get('messages')}")
            node_out = job.get("outputs", {}).get("13", {})
            videos = node_out.get("gifs", node_out.get("videos", []))
            if videos:
                output_info = videos[0]
                break

    if not output_info:
        raise TimeoutError(f"ComfyUI timed out after {GEN_TIMEOUT}s (id={prompt_id})")

    # Use fullpath if available (ComfyUI on same host), else download
    fullpath = output_info.get("fullpath")
    if fullpath and Path(fullpath).exists():
        raw_path = fullpath
        suffix = Path(fullpath).suffix
    else:
        fn  = output_info["filename"]
        url = f"{COMFYUI_URL}/view?filename={fn}&subfolder={output_info.get('subfolder','')}&type={output_info.get('type','output')}"
        dl  = requests.get(url, timeout=120)
        dl.raise_for_status()
        suffix = Path(fn).suffix
        tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        tmp.write(dl.content); tmp.close()
        raw_path = tmp.name

    if suffix.lower() != ".mp4":
        mp4 = raw_path.replace(suffix, ".mp4")
        r = subprocess.run(
            ["ffmpeg", "-y", "-i", raw_path,
             "-c:v", "libx264", "-crf", "23", "-preset", "fast",
             "-pix_fmt", "yuv420p", "-movflags", "+faststart", mp4],
            capture_output=True, text=True)
        if raw_path != fullpath:
            os.unlink(raw_path)
        if r.returncode != 0:
            raise RuntimeError(f"ffmpeg failed:\n{r.stderr}")
        logger.info("ComfyUI: saved %s", mp4)
        return mp4

    return raw_path


# ── compatibility layer for video_clip_generation.py ────────────────────────

class ComfyUIVideoError(RuntimeError):
    """Raised when ComfyUI generation fails."""


def check_comfyui_health(api_url: str = COMFYUI_URL) -> bool:
    """Return True if ComfyUI is reachable and responsive."""
    try:
        r = requests.get(f"{api_url}/system_stats", timeout=5)
        return r.status_code == 200
    except requests.RequestException:
        return False


def generate_comfy_video_clip(
    prompt: str,
    output_path,
    *,
    api_url: str = COMFYUI_URL,
    workflow_path=WORKFLOW_PATH,
    prompt_node_id: str = "3",
    negative_prompt_node_id: str | None = "4",
    seed_node_id: str | None = "10",
    width: int = 512,
    height: int = 896,
    frames: int = 97,
    fps: int = 25,
    timeout_seconds: int = GEN_TIMEOUT,
    poll_seconds: float = 3.0,
) -> Path:
    """
    Generate a video clip and save to output_path.
    Matches the signature expected by video_clip_generation.py.
    Returns Path to the saved mp4.
    """
    import random
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Load + patch workflow
    wf_path = Path(workflow_path)
    if not wf_path.is_absolute():
        wf_path = Path(__file__).parent.parent / wf_path
    with open(wf_path) as f:
        wf = json.load(f)

    seed = random.randint(0, 2**32 - 1)
    wf[prompt_node_id]["inputs"]["text"] = prompt
    if negative_prompt_node_id and negative_prompt_node_id in wf:
        wf[negative_prompt_node_id]["inputs"]["text"] = (
            "worst quality, inconsistent motion, blurry, jittery, distorted, watermark, text"
        )
    if seed_node_id and seed_node_id in wf:
        wf[seed_node_id]["inputs"]["noise_seed"] = seed

    # Patch dimensions + frames
    sampler_node = next((k for k,v in wf.items() if v.get("class_type") == "LTXVBaseSampler"), None)
    if sampler_node:
        wf[sampler_node]["inputs"].update({"width": width, "height": height, "num_frames": frames})

    logger.info("ComfyUI clip: %dx%d %d frames seed=%d", width, height, frames, seed)

    # Submit
    try:
        resp = requests.post(f"{api_url}/prompt", json={"prompt": wf}, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        raise ComfyUIVideoError(f"Submit failed: {e}") from e

    prompt_id = resp.json()["prompt_id"]
    logger.info("ComfyUI: queued %s", prompt_id)

    # Poll
    deadline = time.time() + timeout_seconds
    output_info = None
    while time.time() < deadline:
        time.sleep(poll_seconds)
        try:
            hist = requests.get(f"{api_url}/history/{prompt_id}", timeout=10).json()
        except requests.RequestException:
            continue
        if prompt_id in hist:
            job = hist[prompt_id]
            if job.get("status", {}).get("status_str") == "error":
                raise ComfyUIVideoError(f"Generation error: {job['status'].get('messages')}")
            vhs_out = job.get("outputs", {})
            for node_out in vhs_out.values():
                vids = node_out.get("gifs", node_out.get("videos", []))
                if vids:
                    output_info = vids[0]
                    break
            if output_info:
                break

    if not output_info:
        raise ComfyUIVideoError(f"Timed out after {timeout_seconds}s (id={prompt_id})")

    # Grab file
    fullpath = output_info.get("fullpath")
    if fullpath and Path(fullpath).exists():
        raw_path = Path(fullpath)
    else:
        fn  = output_info["filename"]
        url = f"{api_url}/view?filename={fn}&subfolder={output_info.get('subfolder','')}&type={output_info.get('type','output')}"
        dl  = requests.get(url, timeout=120)
        dl.raise_for_status()
        suffix = Path(fn).suffix
        tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        tmp.write(dl.content); tmp.close()
        raw_path = Path(tmp.name)

    # Convert + save to requested output_path
    if raw_path.suffix.lower() != ".mp4":
        result = subprocess.run(
            ["ffmpeg", "-y", "-i", str(raw_path),
             "-c:v", "libx264", "-crf", "23", "-preset", "fast",
             "-pix_fmt", "yuv420p", "-movflags", "+faststart",
             str(output_path)],
            capture_output=True, text=True
        )
        if str(raw_path) != fullpath:
            os.unlink(raw_path)
        if result.returncode != 0:
            raise ComfyUIVideoError(f"ffmpeg failed:\n{result.stderr}")
    else:
        import shutil
        shutil.copy2(raw_path, output_path)
        if str(raw_path) != fullpath:
            os.unlink(raw_path)

    logger.info("ComfyUI: saved clip → %s", output_path)
    return output_path
