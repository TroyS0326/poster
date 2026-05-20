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
