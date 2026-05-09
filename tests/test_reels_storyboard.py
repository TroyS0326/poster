import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from reels.config import load_reel_config
from reels.compliance import BANNED_MARKETING_TERMS
from reels.storyboard import BRAND_PACKS, _allocate_scene_durations, _safe_background_basename, _validate_inputs, generate_storyboard


def test_duration_allocation_count_matches_scene_count() -> None:
    durations = _allocate_scene_durations(18, 4)
    assert len(durations) == 4


def test_duration_allocation_sum_never_exceeds_total() -> None:
    durations = _allocate_scene_durations(20, 3)
    assert sum(durations) <= 20


def test_20_seconds_3_scenes_loadable_by_config_loader(tmp_path: Path) -> None:
    payload = generate_storyboard(topic="Why traders need rules", duration_seconds=20, scene_count=3)
    path = tmp_path / "storyboard_20_3.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    cfg = load_reel_config(path)
    assert len(cfg.scenes) == 3
    assert sum(scene.duration for scene in cfg.scenes) <= cfg.duration_seconds


def test_10_seconds_3_scenes_loadable_by_config_loader(tmp_path: Path) -> None:
    payload = generate_storyboard(topic="Why traders need rules", duration_seconds=10, scene_count=3)
    path = tmp_path / "storyboard_10_3.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    cfg = load_reel_config(path)
    assert len(cfg.scenes) == 3
    assert sum(scene.duration for scene in cfg.scenes) <= cfg.duration_seconds


def test_default_storyboard_still_works() -> None:
    payload = generate_storyboard(topic="Why traders need rules, not motivation")
    assert payload["duration_seconds"] == 18
    assert len(payload["scenes"]) == 4


def test_generated_scene_durations_are_all_positive() -> None:
    payload = generate_storyboard(topic="Rule-based execution beats emotional trading")
    assert all(scene["duration"] > 0 for scene in payload["scenes"])


def test_generated_json_can_be_loaded_by_config_loader(tmp_path: Path) -> None:
    payload = generate_storyboard(topic="Rule-based execution beats emotional trading")
    path = tmp_path / "storyboard.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    cfg = load_reel_config(path)
    assert cfg.title
    assert len(cfg.scenes) == 4


def test_local_storyboard_generation_creates_valid_json() -> None:
    payload = generate_storyboard(topic="Why traders need rules, not motivation")
    assert payload["title"]
    assert isinstance(payload["scenes"], list)
    assert len(payload["scenes"]) == 4
    assert payload["background"]["type"] in {"solid", "gradient"}
    assert payload["duration_seconds"] == 18
    assert payload["fps"] == 24
    assert payload["size"] == [1080, 1920]


def test_empty_topic_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="topic must not be empty"):
        _validate_inputs("", 18, 4, "gradient", tmp_path / "out.json")


def test_invalid_scene_count_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="scene_count"):
        _validate_inputs("topic", 18, 1, "gradient", tmp_path / "out.json")


def test_invalid_duration_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="too short"):
        _validate_inputs("topic", 5, 4, "gradient", tmp_path / "out.json")


def test_unsupported_background_type_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="background_type"):
        _validate_inputs("topic", 18, 4, "image", tmp_path / "out.json")


def test_output_structure_fields_present() -> None:
    payload = generate_storyboard(topic="Paper testing builds confidence")
    expected_fields = {"title", "scenes", "background", "duration_seconds", "fps", "size"}
    assert expected_fields.issubset(payload.keys())


@pytest.mark.parametrize("template", ["discipline", "mistake", "checklist", "myth", "before-after"])
def test_each_template_produces_loadable_config(tmp_path: Path, template: str) -> None:
    payload = generate_storyboard(topic="Why rules matter", template=template)
    path = tmp_path / f"{template}.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    cfg = load_reel_config(path)
    assert len(cfg.scenes) == 4


@pytest.mark.parametrize("brand", ["generic", "xeanvi"])
def test_each_brand_produces_loadable_config(tmp_path: Path, brand: str) -> None:
    payload = generate_storyboard(topic="Risk controls first", brand=brand)
    path = tmp_path / f"{brand}.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    cfg = load_reel_config(path)
    assert cfg.title


def test_unsupported_template_rejected() -> None:
    with pytest.raises(ValueError, match="unsupported template"):
        generate_storyboard(topic="Topic", template="unknown")


def test_unsupported_brand_rejected() -> None:
    with pytest.raises(ValueError, match="unsupported brand"):
        generate_storyboard(topic="Topic", brand="unknown")


def test_generic_brand_default_cta_is_generic() -> None:
    payload = generate_storyboard(topic="Why rules matter", brand="generic")
    combined = " ".join(scene["text"] for scene in payload["scenes"]).lower()
    assert BRAND_PACKS["generic"]["default_cta"].lower() in combined
    assert "xeanvi" not in combined
    assert "playbook" not in combined
    assert "command center" not in combined


def test_xeanvi_brand_uses_safe_language() -> None:
    payload = generate_storyboard(topic="Why rules matter", brand="xeanvi", template="mistake")
    combined = " ".join(scene["text"] for scene in payload["scenes"]).lower()
    assert "rule-based" in combined
    assert any(term in combined for term in ["playbook", "command center", "validation", "rule-based execution"])


def test_brand_defaults_applied_when_omitted() -> None:
    payload = generate_storyboard(topic="Risk controls first", brand="xeanvi", audience=None, call_to_action=None)
    assert payload["scenes"][0]["text"].lower().startswith(BRAND_PACKS["xeanvi"]["default_audience"])
    assert BRAND_PACKS["xeanvi"]["default_cta"] in " ".join(scene["text"] for scene in payload["scenes"])


def test_custom_audience_overrides_default() -> None:
    payload = generate_storyboard(topic="Risk controls first", brand="xeanvi", audience="swing traders")
    assert payload["scenes"][0]["text"].lower().startswith("swing traders")


def test_custom_compliant_cta_overrides_default() -> None:
    cta = "Save this and review your rules before market open."
    payload = generate_storyboard(topic="Risk controls first", brand="generic", call_to_action=cta)
    assert cta in " ".join(scene["text"] for scene in payload["scenes"])


@pytest.mark.parametrize("topic,bad_phrase", [("guaranteed profits from trading", "guaranteed profit"), ("passive income with charts", "passive income")])
def test_banned_topic_rejected(topic: str, bad_phrase: str) -> None:
    with pytest.raises(ValueError, match=f"topic contains prohibited marketing/compliance phrase: {bad_phrase}"):
        generate_storyboard(topic=topic)


def test_banned_cta_rejected() -> None:
    with pytest.raises(ValueError, match="call_to_action contains prohibited marketing/compliance phrase: buy now"):
        generate_storyboard(topic="Risk controls first", call_to_action="Buy now and never miss out")


def test_generated_scene_text_has_no_banned_terms() -> None:
    payload = generate_storyboard(topic="Why rules matter", brand="xeanvi", template="checklist")
    combined = " ".join(scene["text"].lower() for scene in payload["scenes"])
    assert not any(term in combined for term in BANNED_MARKETING_TERMS)


@pytest.mark.parametrize("scene_count", [2, 3, 4, 6])
def test_generated_scene_count_matches_request(scene_count: int) -> None:
    payload = generate_storyboard(topic="Topic", template="checklist", scene_count=scene_count)
    assert len(payload["scenes"]) == scene_count
    assert all(scene["text"].strip() for scene in payload["scenes"])


def test_default_cli_compatible_behavior_still_works(tmp_path: Path) -> None:
    output = tmp_path / "storyboard_cli.json"
    result = subprocess.run(
        [sys.executable, "-m", "reels.storyboard", "--topic", "Why most traders need rules, not motivation", "--output", str(output)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr + result.stdout
    cfg = load_reel_config(output)
    assert cfg.title


def test_safe_background_basename_slug() -> None:
    slug = _safe_background_basename("Xeanvi", "mistake", "market_grid", "The cost of breaking your own trading rules!!!")
    assert slug.startswith("xeanvi_mistake_market_grid_the_cost_of_breaking_your_own_trading_rules")
    assert "!" not in slug


def test_storyboard_background_image_path_override() -> None:
    payload = generate_storyboard(topic="Rules matter", background_image_path="outputs/backgrounds/a.png")
    assert payload["background"]["type"] == "image"
    assert payload["background"]["path"] == "outputs/backgrounds/a.png"


def test_storyboard_background_image_path_non_png_rejected() -> None:
    with pytest.raises(ValueError, match="background_image_path must end with .png"):
        generate_storyboard(topic="Rules matter", background_image_path="outputs/backgrounds/a.jpg")


def test_image_background_storyboard_loads_config(tmp_path: Path) -> None:
    bg = tmp_path / "bg.png"
    bg.write_bytes(b"fake")
    payload = generate_storyboard(topic="Rules matter", background_image_path=str(bg))
    path = tmp_path / "storyboard_image.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    cfg = load_reel_config(path)
    assert cfg.background.type == "image"
    assert cfg.background.path == str(bg)


def test_cli_generate_background_creates_json_and_png(tmp_path: Path) -> None:
    output = tmp_path / "storyboard.json"
    bg_out = tmp_path / "custom.png"
    result = subprocess.run(
        [
            sys.executable, "-m", "reels.storyboard",
            "--brand", "xeanvi",
            "--template", "mistake",
            "--visual-style", "market_grid",
            "--generate-background",
            "--background-output", str(bg_out),
            "--topic", "The cost of breaking your own trading rules",
            "--output", str(output),
        ],
        check=False, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr + result.stdout
    assert output.exists()
    assert bg_out.exists()
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["background"]["type"] == "image"
    assert payload["background"]["path"] == str(bg_out)


def test_cli_generate_background_default_path(tmp_path: Path) -> None:
    output = tmp_path / "storyboard.json"
    repo_root = Path(__file__).resolve().parents[1]
    env = dict(os.environ)
    env["PYTHONPATH"] = str(repo_root) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    result = subprocess.run(
        [sys.executable, "-m", "reels.storyboard", "--brand", "xeanvi", "--template", "mistake", "--visual-style", "market_grid", "--generate-background", "--topic", "Topic", "--output", str(output)],
        check=False, capture_output=True, text=True, cwd=tmp_path, env=env,
    )
    assert result.returncode == 0, result.stderr + result.stdout
    payload = json.loads(output.read_text(encoding="utf-8"))
    bg_path = Path(payload["background"]["path"])
    assert payload["background"]["type"] == "image"
    assert str(bg_path).startswith("outputs/backgrounds/")
    assert (tmp_path / bg_path).exists()


def test_cli_background_output_requires_generate_background(tmp_path: Path) -> None:
    output = tmp_path / "storyboard.json"
    result = subprocess.run(
        [sys.executable, "-m", "reels.storyboard", "--topic", "Topic", "--background-output", str(tmp_path / "out.png"), "--output", str(output)],
        check=False, capture_output=True, text=True,
    )
    assert result.returncode != 0
    assert "background-output requires --generate-background" in (result.stdout + result.stderr)


def test_cli_background_output_non_png_fails(tmp_path: Path) -> None:
    output = tmp_path / "storyboard.json"
    result = subprocess.run(
        [sys.executable, "-m", "reels.storyboard", "--topic", "Topic", "--generate-background", "--background-output", str(tmp_path / "bad.jpg"), "--output", str(output)],
        check=False, capture_output=True, text=True,
    )
    assert result.returncode != 0


def test_no_duplicate_banned_terms_constant_in_modules() -> None:
    storyboard_text = Path("reels/storyboard.py").read_text(encoding="utf-8")
    visuals_text = Path("reels/visuals.py").read_text(encoding="utf-8")
    assert "BANNED_MARKETING_TERMS = [" not in storyboard_text
    assert "BANNED_MARKETING_TERMS = [" not in visuals_text
