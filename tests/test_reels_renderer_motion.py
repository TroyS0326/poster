from pathlib import Path
from PIL import Image

from reels.config import BackgroundConfig, ReelConfig, SceneConfig, VoiceoverConfig
from reels.generate import _scene_for_time
from reels.motion_styles import choose_motion
from reels.design_system import choose_layout


def test_motion_style_selection_scene_aware():
    assert choose_motion('panic revenge trading').transition == 'whip'
    assert choose_motion('risk discipline checklist').transition == 'push'


def test_layout_template_selection_varies():
    a = choose_layout(0, 'Short hook')
    b = choose_layout(1, 'This is a longer supporting explanation line for execution discipline')
    assert a == 'bold_center_statement'
    assert b != a


def test_scene_index_progression():
    cfg = ReelConfig(
        title='T', duration_seconds=8, size=(1080,1920), fps=24,
        background=BackgroundConfig(type='solid', color='#111111', color_end='#222222', path=None),
        scenes=[SceneConfig(text='one', duration=4), SceneConfig(text='two', duration=4)],
        voiceover=VoiceoverConfig(),
    )
    idx1, _, _ = _scene_for_time(cfg, 1.0)
    idx2, _, _ = _scene_for_time(cfg, 5.0)
    assert idx1 == 0 and idx2 == 1
