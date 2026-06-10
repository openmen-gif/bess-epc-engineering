# -*- coding: utf-8 -*-
"""
utils/sim_physics.py
────────────────────────────────────────────────────────────────────────────
Reduced-order physics models + Plotly animation builders for the BESS
engineering dashboard (pages 03 / 09 / 10).

⚠ These are ANALYTICAL SURROGATE models (energy balance, FDM diffusion,
NFPA 92 plume correlations, point-source radiation). They are intended for
parametric screening and visual communication — NOT a substitute for full
CFD (OpenFOAM/ANSYS Fluent), FEA (STAAD/ANSYS) or FDS fire simulation.

Self-contained: depends only on numpy + plotly.graph_objects.
"""
import numpy as np
import plotly.graph_objects as go

# ── Physical constants (SI) ────────────────────────────────────────────────
AIR_RHO = 1.15        # kg/m³  (air, ~35 °C)
AIR_CP  = 1006.0      # J/(kg·K)
G_ACC   = 9.81        # m/s²
T_K0    = 273.15


# ═══════════════════════════════════════════════════════════════════════════
# 1. 2-D depth-averaged transient heat solver (conduction–convection FDM)
#
#    ρ·cp·H · ∂T/∂t = k_eff·H·∇²T + q″_src − G_hvac·(T − T_sup) − h_env·(T − T_amb)
#
#    - k_eff/(ρcp) = α_eff : effective TURBULENT mixing diffusivity (m²/s)
#    - HVAC modelled as a thermal conductance G = Q_rated / ΔT_design at the
#      duct cells (sensible cooling, self-limiting with (T − T_supply))
#    - Envelope loss U_env spread over (roof + walls) per unit floor area
#    - Explicit FTCS diffusion + semi-implicit sink terms (unconditionally
#      stable w.r.t. the sink, CFL-limited dt for diffusion)
# ═══════════════════════════════════════════════════════════════════════════
def heat2d_transient(Lx, Ly, H, T_amb, src_cells, q_src_W,
                     hvac_W, vent_cells, nx, ny, snap_times_s,
                     alpha_eff=0.08, U_env=2.5, dT_design=12.0,
                     T_supply=None, src_sigma_m=0.6, hvac_local_frac=0.35):
    """Return (times_s, snapshots) — snapshots are (ny, nx) °C arrays.

    src_cells / vent_cells : list of (ix, iy) grid indices.
    q_src_W  : TOTAL heat release of all sources [W], split evenly and spread
               over a Gaussian footprint of std-dev src_sigma_m.
    hvac_W   : rated HVAC sensible cooling capacity [W]. Total conductance
               G = hvac_W/ΔT_design; (1−hvac_local_frac) acts on the whole
               recirculated air volume (forced-air mixing), hvac_local_frac
               is concentrated at the duct cells (locally cooler zones).
    """
    if T_supply is None:
        T_supply = T_amb
    snap_times_s = sorted(set(float(t) for t in snap_times_s))
    dx, dy = Lx / nx, Ly / ny
    cell_A = dx * dy
    C = AIR_RHO * AIR_CP * H                      # J/(K·m²) areal heat capacity

    xg = (np.arange(nx) + 0.5) * dx
    yg = (np.arange(ny) + 0.5) * dy
    Xg, Yg = np.meshgrid(xg, yg)

    # source heat flux map [W/m²] — Gaussian footprint per source
    q_map = np.zeros((ny, nx))
    if src_cells and q_src_W > 0:
        q_each = q_src_W / len(src_cells)
        s2 = 2.0 * max(src_sigma_m, min(dx, dy)) ** 2
        for (ix, iy) in src_cells:
            cx = (min(max(int(ix), 0), nx - 1) + 0.5) * dx
            cy = (min(max(int(iy), 0), ny - 1) + 0.5) * dy
            ker = np.exp(-((Xg - cx) ** 2 + (Yg - cy) ** 2) / s2)
            ker_sum = ker.sum() * cell_A
            if ker_sum > 0:
                q_map += q_each * ker / ker_sum

    # HVAC conductance map [W/(K·m²)]
    A_floor_tot = Lx * Ly
    G_total = hvac_W / max(dT_design, 1.0) if hvac_W > 0 else 0.0
    loc_frac = hvac_local_frac if vent_cells else 0.0
    g_vent = np.full((ny, nx), G_total * (1.0 - loc_frac) / A_floor_tot)
    if vent_cells and G_total > 0:
        g_each = G_total * loc_frac / len(vent_cells)
        for (ix, iy) in vent_cells:
            g_vent[min(max(int(iy), 0), ny - 1),
                   min(max(int(ix), 0), nx - 1)] += g_each / cell_A

    # Envelope conductance per floor area (roof + walls referenced to floor)
    A_floor = Lx * Ly
    A_env = A_floor + 2.0 * H * (Lx + Ly)
    h_env = U_env * (A_env / A_floor)             # W/(K·m²)

    # time stepping
    t_end = snap_times_s[-1] if snap_times_s else 0.0
    dt = 0.2 * min(dx, dy) ** 2 / max(alpha_eff, 1e-6)
    if t_end > 0 and t_end / dt > 60000:          # runtime guard
        dt = t_end / 60000.0

    T = np.full((ny, nx), float(T_amb))
    times, snaps = [], []
    t = 0.0
    si = 0
    # capture t = 0 if requested
    while si < len(snap_times_s) and snap_times_s[si] <= 1e-9:
        times.append(0.0)
        snaps.append(T.copy())
        si += 1

    inv_dx2, inv_dy2 = 1.0 / dx ** 2, 1.0 / dy ** 2
    while si < len(snap_times_s):
        t += dt
        Tp = np.pad(T, 1, mode="edge")            # adiabatic walls (env loss separate)
        lap = ((Tp[1:-1, 2:] + Tp[1:-1, :-2] - 2.0 * T) * inv_dx2 +
               (Tp[2:, 1:-1] + Tp[:-2, 1:-1] - 2.0 * T) * inv_dy2)
        s = (g_vent + h_env) / C                  # sink rate [1/s]
        T_ref = (g_vent * T_supply + h_env * T_amb) / np.maximum(g_vent + h_env, 1e-12)
        T = (T + dt * (alpha_eff * lap + q_map / C + s * T_ref)) / (1.0 + dt * s)
        while si < len(snap_times_s) and t >= snap_times_s[si] - 1e-9:
            times.append(round(snap_times_s[si], 1))
            snaps.append(T.copy())
            si += 1
    return times, snaps


def stratification_profile(z, H, ratio=2.0):
    """Linear vertical weighting p(z): depth-average = 1.0, ceiling/floor = ratio.
    T(x,y,z) = T_amb + p(z)·(T_2D(x,y) − T_amb)  — buoyant stratification surrogate."""
    a = 2.0 / (1.0 + ratio)
    b = 2.0 * (ratio - 1.0) / (1.0 + ratio)
    return a + b * (np.asarray(z, dtype=float) / max(H, 1e-9))


# ═══════════════════════════════════════════════════════════════════════════
# 2. Rigid-pad bearing-pressure distribution (foundation, linear soil spring)
#
#    q(x,y) = P/A · (1 + 12·e_x·x/L² + 12·e_y·y/B²),  clipped at 0 (no tension)
#    Classic eccentric-footing pressure (Meyerhof). Valid while resultant is
#    near the kern (e ≤ L/6); uplift shown as q = 0 zone.
# ═══════════════════════════════════════════════════════════════════════════
def bearing_pressure(q_avg, e_x, e_y, L, B, nx=30, ny=30):
    """Return (x, y, q) with x∈[0,L], y∈[0,B]; q in same unit as q_avg (kN/m²)."""
    x = np.linspace(0.0, L, nx)
    y = np.linspace(0.0, B, ny)
    X, Y = np.meshgrid(x - L / 2.0, y - B / 2.0)
    q = q_avg * (1.0 + 12.0 * e_x * X / L ** 2 + 12.0 * e_y * Y / B ** 2)
    return x, y, np.clip(q, 0.0, None)


def seismic_pulse(times, f_hz=2.0, decay=0.5):
    """Normalized damped-sine ground acceleration history a(t)/a_max ∈ [−1, 1]."""
    t = np.asarray(times, dtype=float)
    return np.sin(2.0 * np.pi * f_hz * t) * np.exp(-decay * t)


# ═══════════════════════════════════════════════════════════════════════════
# 3. Buoyant smoke plume + smoke-layer filling (NFPA 92 axisymmetric plume)
#
#    Mass entrainment:  m_p = 0.071·Qc^(1/3)·z^(5/3) + 0.0018·Qc     [kg/s, Qc kW]
#    (below flame tip:  m_p = 0.0056·Qc·z/L_f)
#    Flame height:      L_f = 0.235·Q^(2/5) − 1.02·D                 [m, Q kW]
#    Centerline ΔT:     ΔT0 = 25·Qc^(2/3)/z^(5/3)                    [K, Qc kW]
#    Layer descent:     dV/dt = m_p(z_i)/ρ_s − Q_extract  (well-mixed layer)
# ═══════════════════════════════════════════════════════════════════════════
def flame_height_m(Q_kW, D_m=2.0):
    return max(0.235 * Q_kW ** 0.4 - 1.02 * D_m, 0.3)


def plume_mass_flow(Qc_kW, z_m, L_f):
    z = max(z_m, 0.1)
    if z <= L_f:
        return 0.0056 * Qc_kW * z / max(L_f, 0.1)
    return 0.071 * Qc_kW ** (1.0 / 3.0) * z ** (5.0 / 3.0) + 0.0018 * Qc_kW


def plume_centerline_dT(Qc_kW, z_m):
    return min(25.0 * Qc_kW ** (2.0 / 3.0) / max(z_m, 0.3) ** (5.0 / 3.0), 800.0)


def smoke_layer_series(Q_MW, u_fan, A_floor, H, A_fan=3.0,
                       T_amb_C=25.0, t_end=240.0, n=49, conv_frac=0.7):
    """Integrate well-mixed smoke-layer filling vs. mechanical extraction.

    Returns dict(times, z_layer, T_layer_C, m_plume, Q_extract_m3s).
    z_layer = smoke layer interface height above floor [m]."""
    Q_kW = Q_MW * 1000.0
    Qc_kW = conv_frac * Q_kW
    L_f = flame_height_m(Q_kW)
    Q_ext = u_fan * A_fan                          # extraction volumetric flow m³/s
    times = np.linspace(0.0, t_end, int(n))
    z_min = 1.0

    V = 0.0
    z_i = H
    out_z, out_T, out_m = [], [], []
    dt = max(times[1] - times[0], 1e-3) / 8.0
    t_now = 0.0
    for tk in times:
        while t_now < tk - 1e-9:
            m_p = plume_mass_flow(Qc_kW, z_i, L_f)
            T_l = T_amb_C + Qc_kW * 1000.0 / (AIR_CP * max(m_p, 0.2))
            T_l = min(T_l, 450.0)
            rho_s = 353.0 / (T_l + T_K0)
            dV = (m_p / rho_s - Q_ext) * dt
            V = max(V + dV, 0.0)
            z_i = max(H - V / A_floor, z_min)
            t_now += dt
        m_p = plume_mass_flow(Qc_kW, z_i, L_f)
        T_l = min(T_amb_C + Qc_kW * 1000.0 / (AIR_CP * max(m_p, 0.2)), 450.0)
        out_z.append(z_i)
        out_T.append(T_l)
        out_m.append(m_p)
    return {
        "times": times, "z_layer": np.array(out_z),
        "T_layer_C": np.array(out_T), "m_plume": np.array(out_m),
        "Q_extract_m3s": Q_ext, "flame_h": L_f,
    }


def plume_particles(z_layer, T_layer_C, Q_MW, H, dom_x=20.0, dom_y=20.0,
                    fire_x=10.0, fire_y=10.0, u_fan=5.0, frame_seed=0,
                    n_col=200, n_layer_max=550, T_amb_C=25.0, conv_frac=0.7):
    """Monte-Carlo render of (plume column + descending smoke layer) at one
    time step. Positions sampled from the GAUSSIAN plume profile σ(z) ≈ 0.12·z;
    the underlying widths/temps are deterministic physics, the dots are a
    sampling visualization. Returns (x, y, z, temp_C)."""
    rng = np.random.default_rng(1000 + int(frame_seed))
    Qc_kW = conv_frac * Q_MW * 1000.0

    # — rising column: fire → layer interface —
    zc = rng.uniform(0.3, max(z_layer, 0.6), n_col)
    sigma = 0.12 * zc + 0.4
    xc = fire_x + rng.normal(0.0, sigma)
    yc = fire_y + rng.normal(0.0, sigma)
    tc = T_amb_C + np.array([plume_centerline_dT(Qc_kW, z) for z in zc]) \
         * np.exp(-((xc - fire_x) ** 2 + (yc - fire_y) ** 2) / (2.0 * sigma ** 2))

    # — smoke layer: fills z ∈ [z_layer, H], biased toward exhaust wall (x+) —
    thick = max(H - z_layer, 0.0)
    n_lay = int(n_layer_max * min(thick / max(H - 1.0, 1e-6), 1.0))
    if n_lay > 0:
        drift = min(u_fan / 15.0, 1.0) * 0.35     # fan pulls layer toward x = dom_x
        xl = dom_x * np.clip(rng.beta(1.0 + drift * 2.0, 1.0, n_lay), 0.0, 1.0)
        yl = rng.uniform(0.0, dom_y, n_lay)
        zl = rng.uniform(z_layer, H, n_lay)
        tl = np.full(n_lay, T_layer_C) + rng.normal(0.0, 5.0, n_lay)
        x = np.concatenate([xc, xl]); y = np.concatenate([yc, yl])
        z = np.concatenate([zc, zl]); tt = np.concatenate([tc, tl])
    else:
        x, y, z, tt = xc, yc, zc, tc
    return x, y, z, np.clip(tt, T_amb_C, 800.0)


# ═══════════════════════════════════════════════════════════════════════════
# 4. Cell-to-cell thermal-runaway propagation (lumped rack model)
#
#    Incident flux (SFPE point-source): q″ = χr·Q_eff / (4π·d²)
#    Target heating:  m·c·dT/dt = q″·A_exp − h·A·(T − T_amb) − Q_cool,supp
#    Ignition:        T ≥ T_onset (chemistry; UL 9540A test-specific in reality)
#    Burn-down:       E_rem -= Q_eff·dt ; burnout when E_rem ≤ 0
#    Suppression:     flame knockdown Q_eff = (1−η)·Q after response time;
#                     extinguished after ~90/η s exposure (then 15 % smolder)
# ═══════════════════════════════════════════════════════════════════════════
# state codes (match page 10)
S_NORMAL, S_HEATING, S_RUNAWAY, S_FIRE, S_SUPPRESSED = 0, 1, 2, 3, 4

CHI_R   = 0.30        # radiative fraction of HRR (SFPE typical 0.2–0.4)
A_EXP   = 4.0         # exposed face area of target rack [m²]
MC_RACK = 1.2e6       # lumped thermal mass m·c of one rack [J/K]
HA_NAT  = 60.0        # natural-convection loss h·A [W/K]
RACK_W  = 0.6         # rack footprint width [m] (center spacing = gap + width)
T_FLAME = 650.0       # display temperature of a burning rack [°C]
SMOLDER = 0.15        # residual HRR fraction after agent knockdown


def simulate_runaway(rows, cols, origin_rc, hrr_MW, onset_C, energy_MJ,
                     spacing_m, eta_supp, q_cool_W, response_s,
                     t_max_s=2700.0, n_frames=90, T_amb=25.0):
    """Deterministic reaction-front propagation across a rack grid.

    Returns dict(times, T_frames, state_frames, fire_counts, supp_counts)."""
    n_frames = max(int(n_frames), 2)
    frame_dt = t_max_s / (n_frames - 1)
    dt = min(2.0, frame_dt)

    d_orth = spacing_m + RACK_W                   # center-to-center distance
    # flux factor for orthogonal / diagonal neighbours [W per MW of HRR]
    f_orth = CHI_R * 1e6 * A_EXP / (4.0 * np.pi * d_orth ** 2)
    f_diag = f_orth / 2.0                         # d·√2 → ½ flux

    T = np.full((rows, cols), float(T_amb))
    E = np.full((rows, cols), float(energy_MJ))   # MJ remaining
    burning = np.zeros((rows, cols), dtype=bool)
    extinguished = np.zeros((rows, cols), dtype=bool)
    burned_out = np.zeros((rows, cols), dtype=bool)
    exposure = np.zeros((rows, cols))

    r0, c0 = origin_rc
    burning[r0, c0] = True
    T[r0, c0] = T_FLAME

    shifts_o = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    shifts_d = [(-1, -1), (-1, 1), (1, -1), (1, 1)]

    def _shift_sum(src, shifts):
        acc = np.zeros_like(src)
        for dr, dc in shifts:
            s = np.zeros_like(src)
            rs0, rs1 = max(dr, 0), rows + min(dr, 0)
            cs0, cs1 = max(dc, 0), cols + min(dc, 0)
            s[rs0:rs1, cs0:cs1] = src[rs0 - dr:rs1 - dr, cs0 - dc:cs1 - dc]
            acc += s
        return acc

    def _state_grid():
        g = np.full((rows, cols), S_NORMAL, dtype=int)
        g[T >= T_amb + 20.0] = S_HEATING
        g[T >= onset_C - 15.0] = S_RUNAWAY
        g[burning] = S_FIRE
        g[extinguished | burned_out] = S_SUPPRESSED
        return g

    times, T_frames, state_frames, fire_counts, supp_counts = [], [], [], [], []

    def _record(tk):
        times.append(round(tk, 1))
        T_frames.append(T.copy())
        g = _state_grid()
        state_frames.append(g)
        fire_counts.append(int(np.sum(g == S_FIRE)))
        supp_counts.append(int(np.sum(g == S_SUPPRESSED)))

    _record(0.0)
    t = 0.0
    next_frame = frame_dt
    while t < t_max_s - 1e-9:
        t += dt
        supp_active = (eta_supp > 0.0) and (t >= response_s)

        # effective HRR per cell [MW]
        Q_eff = np.zeros((rows, cols))
        knock = (1.0 - eta_supp) if supp_active else 1.0
        Q_eff[burning] = hrr_MW * knock
        Q_eff[extinguished] = hrr_MW * SMOLDER    # vented smolder, residual flux

        # incident power on each cell from burning/smoldering neighbours [W]
        P_in = _shift_sum(Q_eff, shifts_o) * f_orth + _shift_sum(Q_eff, shifts_d) * f_diag

        # heat the non-burning, not-yet-consumed cells
        target = (~burning) & (~burned_out) & (~extinguished)
        cool = HA_NAT * (T - T_amb)
        cool_supp = q_cool_W if supp_active else 0.0
        dT = (P_in - cool - cool_supp) / MC_RACK * dt
        T = np.where(target, np.maximum(T + dT, T_amb), T)

        # ignition
        ignite = target & (T >= onset_C)
        burning[ignite] = True
        T[ignite] = T_FLAME

        # burn-down of energy (MW·s = MJ)
        burn_now = burning | extinguished
        E = np.where(burn_now, E - Q_eff * dt, E)
        new_out = burn_now & (E <= 0.0)
        burned_out |= new_out
        burning[new_out] = False
        extinguished[new_out] = False
        T[new_out] = np.maximum(T[new_out] * 0.0 + T_amb + 80.0, T_amb)

        # agent extinguishment of open flame
        if supp_active and eta_supp > 0:
            exposure[burning] += dt
            newly_ext = burning & (exposure >= 90.0 / max(eta_supp, 0.05))
            extinguished[newly_ext] = True
            burning[newly_ext] = False
            T[newly_ext] = onset_C + 50.0

        # passive cooling of consumed cells
        decay_mask = burned_out & (T > T_amb)
        T[decay_mask] -= (HA_NAT * (T[decay_mask] - T_amb) / MC_RACK) * dt * 4.0

        if t >= next_frame - 1e-9:
            _record(t)
            next_frame += frame_dt

    if times[-1] < t_max_s - 1e-6:
        _record(t_max_s)
    return {
        "times": times, "T_frames": T_frames, "state_frames": state_frames,
        "fire_counts": fire_counts, "supp_counts": supp_counts,
    }


# ═══════════════════════════════════════════════════════════════════════════
# 5. Plotly go.Frames animation helpers (Play / Pause + time slider)
# ═══════════════════════════════════════════════════════════════════════════
def fmt_time(sec):
    """Human time label: 90 → '1m 30s'."""
    sec = float(sec)
    if sec < 60:
        return f"{sec:.0f}s"
    m, s = divmod(int(round(sec)), 60)
    return f"{m}m {s:02d}s" if s else f"{m}m"


def add_play_controls(fig, frame_names, time_labels, duration_ms=250,
                      prefix="t = ", play_label="▶ Play", pause_label="⏸ Pause",
                      font_color="#c9d1d9"):
    """Attach Play/Pause buttons and a time slider driving fig.frames."""
    fig.update_layout(
        updatemenus=[dict(
            type="buttons", direction="left",
            x=0.0, y=1.15, xanchor="left", yanchor="top",
            pad=dict(r=8, t=0),
            bgcolor="rgba(40,44,52,0.8)", bordercolor="#30363d",
            font=dict(color=font_color),
            buttons=[
                dict(label=play_label, method="animate",
                     args=[None, dict(frame=dict(duration=duration_ms, redraw=True),
                                      fromcurrent=True, transition=dict(duration=0),
                                      mode="immediate")]),
                dict(label=pause_label, method="animate",
                     args=[[None], dict(frame=dict(duration=0, redraw=False),
                                        transition=dict(duration=0),
                                        mode="immediate")]),
            ],
        )],
        sliders=[dict(
            active=0, x=0.06, len=0.92, y=-0.02,
            currentvalue=dict(prefix=prefix, font=dict(color=font_color, size=13),
                              visible=True, xanchor="left"),
            font=dict(color=font_color, size=10),
            bgcolor="rgba(255,255,255,0.08)", bordercolor="#30363d",
            tickcolor=font_color,
            steps=[dict(method="animate", label=str(lbl),
                        args=[[str(nm)], dict(mode="immediate",
                                              frame=dict(duration=0, redraw=True),
                                              transition=dict(duration=0))])
                   for nm, lbl in zip(frame_names, time_labels)],
        )],
    )
    return fig


def build_animation(base_traces, frame_traces_list, frame_names, time_labels,
                    animated_trace_idx=None, layout=None, duration_ms=250,
                    prefix="t = "):
    """Assemble a go.Figure with go.Frames.

    base_traces        : full trace list shown initially (frame traces FIRST).
    frame_traces_list  : per-frame list of replacement traces.
    animated_trace_idx : indices in base_traces replaced by each frame
                         (default 0..len(frame_traces)-1).
    """
    if animated_trace_idx is None:
        animated_trace_idx = list(range(len(frame_traces_list[0])))
    frames = [go.Frame(data=trs, traces=animated_trace_idx, name=str(nm))
              for trs, nm in zip(frame_traces_list, frame_names)]
    fig = go.Figure(data=base_traces, frames=frames)
    if layout:
        fig.update_layout(layout)
    add_play_controls(fig, frame_names, time_labels, duration_ms=duration_ms,
                      prefix=prefix)
    return fig
