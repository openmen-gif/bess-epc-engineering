"""Offline spatial viewer adapters. Numerical solvers remain the source of truth.

Coordinates are x=east, y=north, z=up in metres; JS maps these to Three Y-up.
Equipment embellishments are illustrative, not manufacturer CAD geometry.
"""
import json
from pathlib import Path

import numpy as np

from utils import site_layout as SL
from utils import engineering_params as EP
from utils.sim_physics import RACK_W, plume_particles

_ROOT = Path(__file__).resolve().parent.parent


def _numbers(value):
    a = np.asarray(value, dtype=float)
    if not np.isfinite(a).all():
        raise ValueError("3D result contains non-finite values")
    return np.round(a, 3).tolist()


def _base(mode, size, language):
    if min(size) <= 0:
        raise ValueError("3D dimensions must be positive")
    return dict(mode=mode, size=_numbers(size), language=language, boxes=[], times=[],
                fields=[], unit="°C", pads=[], trench=[], vents=[], grid=[])


def site_payload(layout, pad_l, pad_w, trench_d, language="KO", baseline=None):
    d = _base("site", [*layout["site"], max(b["dz"] for b in layout["boxes"])], language)
    d.update(boxes=layout["boxes"], pads=SL.pad_boxes(layout, pad_l, pad_w),
             trench=layout["trench"], trenchWidth=layout["trench_w"], trenchDepth=trench_d,
             fence=layout["fence"], fenceHeight=EP.FENCE_HEIGHT_M,
             baseline=baseline["boxes"] if baseline else [],
             metrics=layout["metrics"])
    return d


def thermal_payload(length, width, height, times, snapshots, sources, vents,
                    language="KO", airflow=None, cell_centers=True, intake=()):
    fields = _numbers(snapshots)
    if len(fields) != len(times) or not fields:
        raise ValueError("Thermal frames and times must match")
    ny, nx = np.asarray(fields[0]).shape
    d = _base("thermal", [length, width, height], language)
    d.update(times=_numbers(times), fields=fields, grid=[nx, ny])
    offset = 0.5 if cell_centers else 0.0
    # Keep narrow-container racks inside the enclosure at boundary grid cells.
    for i, cell in enumerate(sources):
        x, y = (cell[0] + offset) * length / nx, (cell[1] + offset) * width / ny
        rack_w = min(0.6, 2*x, 2*y, 2*(length-x), 2*(width-y))
        d["boxes"].append(dict(kind="rack", label=f"RACK-{i+1:02d}",
                               x=x-rack_w/2, y=y-rack_w/2, dx=rack_w, dy=rack_w,
                               dz=min(2.2, height * 0.78), cell=[int(cell[0]), int(cell[1])]))
    d["vents"] = [dict(x=(v[0]+offset)*length/nx, y=(v[1]+offset)*width/ny,
                       intake=tuple(v[:2]) in {tuple(p[:2]) for p in intake}) for v in vents]
    if airflow is not None:
        d["airflow"] = {k: _numbers(airflow[k]) for k in ("x", "y", "z", "speed")}
        d["airflowDt"] = 0.35
    return d


def fire_payload(times, states, temperatures, spacing, language="KO", agent="None", response=0):
    rows, cols = np.asarray(states[0]).shape
    pitch = RACK_W + spacing
    d = _base("fire", [cols*pitch+1, rows*pitch+1, 3.2], language)
    d.update(times=_numbers(times), fields=_numbers(temperatures),
             states=np.asarray(states, dtype=int).tolist(), grid=[cols, rows],
             agent=agent, response=response)
    if len(d["times"]) != len(d["states"]) or len(d["times"]) != len(d["fields"]):
        raise ValueError("Fire frames and times must match")
    for r in range(rows):
        for c in range(cols):
            d["boxes"].append(dict(kind="rack", label=f"RACK-{r+1:02d}-{c+1:02d}",
                                   x=0.5+c*pitch, y=0.5+r*pitch, dx=RACK_W, dy=RACK_W,
                                   dz=2.2, cell=[c, r]))
    return d


def smoke_payload(result, length, width, height, language="KO", q_mw=5.0, u_fan=5.5):
    d = _base("smoke", [length, width, height], language)
    d.update(times=_numbers(result["times"]), layers=_numbers(result["z_layer"]),
             layerTemps=_numbers(result["T_layer_C"]), extraction=float(result["Q_extract_m3s"]))
    d["boxes"] = [dict(kind="rack", label="FIRE-SOURCE", x=length/2-0.5,
                       y=width/2-0.5, dx=1, dy=1, dz=2.2)]
    # Same seeded plume sampling used by the analytical page, not a new solver.
    d["plume"] = []
    for i, (z, temp) in enumerate(zip(result["z_layer"], result["T_layer_C"])):
        px, py, pz, pt = plume_particles(z, temp, q_mw, height, dom_x=length, dom_y=width,
                                       fire_x=length/2, fire_y=width/2, u_fan=u_fan,
                                       frame_seed=i, n_col=100, n_layer_max=250)
        d["plume"].append(_numbers(np.column_stack([px, py, pz, pt])))
    return d


def structural_payload(length, width, times, pressures, eccentricities, language="KO"):
    d = _base("structure", [length, width, 3.0], language)
    ny, nx = np.asarray(pressures[0]).shape
    d.update(times=_numbers(times), fields=_numbers(pressures), grid=[nx, ny],
             eccentricities=_numbers(eccentricities), unit="kN/m²")
    d["boxes"] = [dict(kind="enc", label="BESS-01", x=length*0.05, y=width*0.05,
                       dx=length*0.9, dy=width*0.9, dz=2.7)]
    return d


def viewer_html(data):
    # Escape script terminators even for imported project/equipment labels.
    raw = json.dumps(data, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
    raw = raw.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    template = (_ROOT / "frontend/engineering-viewer.html").read_text(encoding="utf-8")
    bundle = (_ROOT / "frontend/engineering-viewer.bundle.js").read_text(encoding="utf-8")
    return template.replace("__SCENE_DATA__", raw).replace("__VIEWER_BUNDLE__", bundle)


def render_viewer(data, height=650):
    import streamlit.components.v1 as components
    components.html(viewer_html(data), height=height, scrolling=False)
