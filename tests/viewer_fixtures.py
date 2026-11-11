"""Generate standalone viewer fixtures using production solvers (local QA only)."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
from utils.engineering_viewer import *
from utils.sim_physics import heat2d_transient, airflow_trajectories, simulate_runaway, smoke_layer_series, bearing_pressure, seismic_pulse
from utils.site_layout import build_layout

out = Path('output_reports/viewer')
out.mkdir(parents=True, exist_ok=True)
def save(name, data):
    (out / f'{name}.html').write_text(viewer_html(data), encoding='utf-8')

save('site', site_payload(build_layout(24, 6, water_m3=60), 7.05, 3.44, 1.2))
src = [(3, 4), (8, 4), (13, 4), (18, 4), (3, 15), (8, 15), (13, 15), (18, 15)]
vents = [(1, 10), (22, 10)]
times, snaps = heat2d_transient(12, 3, 2.9, 30, src, 30000, 40000, vents, 24, 20, list(range(0, 1801, 60)))
flow = airflow_trajectories(snaps[-1], [(11, 1.5)], [(.5, 1.5)], 12, 3, 2.9,
                           rack_xy=[((x+.5)*.5, (y+.5)*.15) for x,y in src], n_particles=100)
save('thermal', thermal_payload(12, 3, 2.9, times, snaps, src, vents, airflow=flow, intake=[vents[0]]))
res = simulate_runaway(3, 4, (1, 1), hrr_MW=2.5, onset_C=170, energy_MJ=2700, spacing_m=.3,
                       eta_supp=.5, q_cool_W=20000, response_s=60, t_max_s=600)
save('fire', fire_payload(res['times'], res['state_frames'], res['T_frames'], .3, agent='Water Mist', response=60))
save('smoke', smoke_payload(smoke_layer_series(5, 5.5, 400, 8), 20, 20, 8))
t = np.linspace(0,8,65)
e = .22*seismic_pulse(t)
save('structure', structural_payload(6.05, 3.44, t, [bearing_pressure(21, v, 0, 6.05, 3.44)[2] for v in e], e))
save('large', site_payload(build_layout(240, 60), 7.05, 3.44, 1.2, language='EN'))
print('6 viewer fixtures generated')
