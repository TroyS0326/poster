from pathlib import Path

ALLOWED_OUTPUT_SUFFIXES = {".mp4", ".mov", ".jpg", ".jpeg", ".png", ".wav", ".mp3", ".json", ".md"}


def _repo_root() -> Path:
    return Path.cwd().resolve()


def _outputs_root() -> Path:
    return (_repo_root() / "outputs").resolve()


def _resolve_output_path(output_path: str | Path) -> Path:
    candidate = Path(output_path)
    if not candidate.is_absolute():
        candidate = (_repo_root() / candidate).resolve()
    else:
        candidate = candidate.resolve()

    outputs_root = _outputs_root()
    try:
        candidate.relative_to(outputs_root)
    except ValueError as exc:
        raise ValueError("output_path must be under outputs/") from exc

    if candidate.suffix.lower() not in ALLOWED_OUTPUT_SUFFIXES:
        raise ValueError(f"unsupported output suffix: {candidate.suffix}")

    if not candidate.exists() or not candidate.is_file():
        raise FileNotFoundError(f"output file does not exist: {candidate}")

    return candidate


def build_public_output_url(public_base: str, output_path: str | Path) -> str:
    base = public_base.strip().rstrip("/")
    if not base:
        raise ValueError("public_base is required")

    resolved = _resolve_output_path(output_path)
    relative = resolved.relative_to(_repo_root()).as_posix()
    return f"{base}/reels/{relative}"
