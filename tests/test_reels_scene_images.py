from pathlib import Path
from PIL import Image

from reels.scene_images import scene_prompt, generate_scene_images


def test_scene_prompt_specific():
    p = scene_prompt('revenge trading','Title','stop emotional entries','premium_editorial_trading').lower()
    assert 'revenge trading' in p and 'emotional tone' in p and 'no embedded text' in p and 'text-safe' in p


def test_scene_image_fallback_reuse(tmp_path, monkeypatch):
    storyboard={"title":"T","scenes":[{"text":"one"},{"text":"two"}]}
    img = tmp_path/'src.png'
    Image.new('RGB',(16,16),(10,10,10)).save(img)
    calls={"n":0}
    def fake_generate(*args, **kwargs):
        calls['n'] += 1
        if calls['n']==1:
            return {"local_path": str(img)}
        return None
    monkeypatch.setattr('reels.scene_images.generate_image', fake_generate)
    out = generate_scene_images(storyboard, tmp_path)
    assert len(out)==2
    assert Path(out[1]).exists()
