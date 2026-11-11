import json
import re

import numpy as np

from utils import site_layout as SL
from utils.engineering_viewer import site_payload, thermal_payload, fire_payload, viewer_html


def test_site_preserves_geometry_and_counts():
    layout = SL.build_layout(24, 6, water_m3=60)
    before = json.dumps(layout)
    data = site_payload(layout, 7.05, 3.44, 1.2, language="EN")
    assert data["boxes"] == layout["boxes"]
    assert data["size"][:2] == list(layout["site"])
    assert len(data["pads"]) == 24
    assert data["trench"] == layout["trench"]
    assert json.dumps(layout) == before


def test_thermal_preserves_frame_grid_and_source_centers():
    frames = [np.arange(12).reshape(3, 4) + 20, np.arange(12).reshape(3, 4) + 35]
    data = thermal_payload(8, 3, 2.9, [0, 60], frames, [(1, 2)], [(0, 1)])
    assert data["times"] == [0, 60]
    assert data["fields"][1] == frames[1].tolist()
    assert data["boxes"][0]["x"] + data["boxes"][0]["dx"] / 2 == 3
    assert data["boxes"][0]["y"] + data["boxes"][0]["dy"] / 2 == 2.5
    assert data["grid"] == [4, 3]


def test_fire_preserves_suppression_and_burnout_states():
    states = [np.array([[0, 3], [4, 5]]), np.array([[1, 4], [5, 5]])]
    temps = [np.full((2, 2), 300), np.full((2, 2), 150)]
    data = fire_payload([0, 15], states, temps, 0.9)
    assert data["states"] == [s.tolist() for s in states]
    assert data["fields"] == [s.tolist() for s in temps]
    assert len(data["boxes"]) == 4
    assert data["boxes"][1]["x"] - data["boxes"][0]["x"] == 1.5


def test_payload_is_safe_and_offline():
    data = site_payload(SL.build_layout(1, 1), 7, 3, 1)
    data["boxes"][0]["label"] = '</script><script>alert("x")</script>'
    html = viewer_html(data)
    assert '</script><script>alert' not in html
    match = re.search(r'<script id="scene-data" type="application/json">(.*?)</script>', html, re.S)
    assert json.loads(match[1])["boxes"][0]["label"] == data["boxes"][0]["label"]
    assert 'src="https://' not in html


def test_invalid_numeric_payload_rejected():
    import pytest
    with pytest.raises(ValueError):
        thermal_payload(8, 3, 3, [0], [np.full((2, 2), np.nan)], [], [])
