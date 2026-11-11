"""Exercise result-bearing Streamlit pages, including branches hidden by default."""
import json
import re
from pathlib import Path

import numpy as np
import pytest
from streamlit.testing.v1 import AppTest


def page(name, lang="KO"):
    a = AppTest.from_file(f"pages/{name}", default_timeout=120)
    a.session_state["auth_user"] = "tester"
    a.session_state["auth_role"] = "admin"
    a.session_state["lang"] = lang
    return a.run()


def scene(a, name):
    assert not a.exception, [e.value for e in a.exception]
    html = next(i.proto.srcdoc for i in a.get("iframe") if 'id="scene-data"' in i.proto.srcdoc)
    Path("output_reports/viewer").mkdir(parents=True, exist_ok=True)
    Path(f"output_reports/viewer/page-{name}.html").write_text(html, encoding="utf-8")
    return json.loads(re.search(r'<script id="scene-data" type="application/json">(.*?)</script>', html, re.S)[1])


@pytest.mark.parametrize("role,expected", [(0,"thermal"),(1,"structure"),(2,"smoke")])
def test_analysis_result_branches(role, expected):
    a = page("03_3D_Simulation.py", "EN")
    a.selectbox[0].select_index(role).run()
    data = scene(a, expected)
    assert data["mode"] == expected
    assert len(data["times"]) >= 31
    if expected == "structure":
        assert max(abs(v) for v in data["eccentricities"]) > .1
        assert not np.allclose(data["fields"][0], data["fields"][1])
    if expected == "smoke":
        assert len(data["plume"]) == len(data["times"])
        assert data["layers"][-1] < data["size"][2]


def test_container_after_actual_solver_run():
    a = page("09_Container_Thermal.py")
    next(b for b in a.button if "시뮬레이션 실행" in b.label).click().run()
    data = scene(a, "container")
    assert data["mode"] == "thermal" and data["airflow"]
    np.testing.assert_allclose(data["fields"][-1], a.session_state["thermal_snapshots"][-1], atol=.001)
    assert len(data["boxes"]) == len(a.session_state["thermal_sources"])


def test_fire_after_actual_solver_run():
    a = page("10_Fire_Spread.py")
    next(b for b in a.button if "시뮬레이션 실행" in b.label).click().run()
    data = scene(a, "fire")
    assert data["mode"] == "fire"
    assert data["states"] == np.asarray(a.session_state["fire_result"]["state_frames"]).tolist()
    np.testing.assert_allclose(data["fields"], a.session_state["fire_result"]["T_frames"], atol=.001)
