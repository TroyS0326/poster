import json
from pathlib import Path

import pytest

from reels.backgrounds import generate_background_png
from reels.config import load_reel_config
from reels.storyboard import generate_storyboard
from reels.visuals import (
    DEFAULT_VISUAL_STYLE_BY_BRAND,
    REQUIRED_NEGATIVE_TERMS,
    SUPPORTED_VISUAL_STYLES,
    build_visual_prompt,
    resolve_visual_style,
)



def test_each_visual_style_produces_prompt_data() -> None:
    for style in SUPPORTED_VISUAL_STYLES:
        prompt = build_visual_prompt(style=style, brand="generic", topic="Why rules matter")
        assert prompt.image_prompt
        assert prompt.negative_prompt


def test_brand_default_visual_styles() -> None:
    assert resolve_visual_style("xeanvi", None) == DEFAULT_VISUAL_STYLE_BY_BRAND["xeanvi"]
    assert resolve_visual_style("generic", None) == DEFAULT_VISUAL_STYLE_BY_BRAND["generic"]


def test_unsupported_visual_style_rejected() -> None:
    with pytest.raises(ValueError, match="unsupported visual_style"):
        resolve_visual_style("generic", "invalid_style")


def test_unsupported_visual_brand_rejected() -> None:
    with pytest.raises(ValueError, match="unsupported brand: fakebrand"):
        resolve_visual_style("fakebrand", "fintech_dark")


def test_build_visual_prompt_rejects_unsupported_brand() -> None:
    with pytest.raises(ValueError, match="unsupported brand: fakebrand"):
        build_visual_prompt(style="fintech_dark", brand="fakebrand", topic="Rules matter")


def test_build_visual_prompt_rejects_banned_topic_phrase() -> None:
    with pytest.raises(ValueError, match="image_prompt contains prohibited marketing/compliance phrase: buy now"):
        build_visual_prompt(style="fintech_dark", brand="xeanvi", topic="Buy now to win")


def test_background_generator_rejects_unsupported_brand(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="unsupported brand: fakebrand"):
        generate_background_png(style="fintech_dark", brand="fakebrand", output=tmp_path / "bg.png")


def test_storyboard_output_includes_visual_field() -> None:
    payload = generate_storyboard(topic="Process over hype", brand="xeanvi")
    assert "visual" in payload
    assert payload["visual"]["image_prompt"]
    assert payload["visual"]["negative_prompt"]


def test_visual_prompts_do_not_contain_banned_marketing_terms() -> None:
    prompt = build_visual_prompt(style="fintech_dark", brand="xeanvi", topic="Rules over motivation")
    bad = ["guaranteed", "passive income", "easy money", "buy now"]
    assert not any(term in prompt.image_prompt.lower() for term in bad)


def test_xeanvi_negative_prompt_includes_required_safety_terms() -> None:
    prompt = build_visual_prompt(style="market_grid", brand="xeanvi", topic="Checklist discipline")
    lower = prompt.negative_prompt.lower()
    for term in REQUIRED_NEGATIVE_TERMS:
        assert term in lower


def test_background_generator_rejects_unsupported_style(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="unsupported visual_style"):
        generate_background_png(style="invalid", brand="generic", output=tmp_path / "bg.png")


def test_background_generator_creates_png(tmp_path: Path) -> None:
    out = tmp_path / "bg.png"
    generate_background_png(style="fintech_dark", brand="xeanvi", output=out)
    assert out.exists()
    assert out.suffix == ".png"


def test_storyboard_with_visual_still_loads_config(tmp_path: Path) -> None:
    payload = generate_storyboard(topic="Rules protect capital", brand="xeanvi", visual_style="market_grid")
    path = tmp_path / "storyboard_visual.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    cfg = load_reel_config(path)
    assert cfg.title
