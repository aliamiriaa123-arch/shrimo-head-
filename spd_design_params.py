"""
SPD V3.0 — Single source of design parameters for the Submerged Pulsed Micro-Slit Diffuser.

Pure Python (no third-party imports) so it can be imported both by Blender's Python
(generate_functional_production_cad.py) and by the system Python verifier
(verification/verify_spd_v3.py). Every interface dimension used by more than one part
is defined here exactly once.

Units: millimetres unless stated otherwise. Assembly frame: pond bed Z = 0, module centred
on X = Y = 0, Bank A discharges toward -X, Bank B toward +X.

Design basis: MASTER_SYSTEM_ARCHITECTURE.md v3.0 + TRL4_Verification_Testing_Protocol.md.
Corrections made in V3.0 are documented in CAD_V3_DESIGN_BASIS_AND_VERIFICATION.md.
"""

import math

VERSION = "V3.0"

# ---------------------------------------------------------------------------
# 1. Operating basis (MASTER v3.0 §2, §6)
# ---------------------------------------------------------------------------
Q_NORMAL_M3H = 30.0            # Nm3/h per module (2400 Nm3/h / 80 modules)
RHO_NORMAL = 1.2923            # kg/Nm3 (0 degC, 101.325 kPa)
P_ATM_KPA = 101.325
POND_DEPTH_M = 1.50
RHO_SEAWATER = 1025.0          # kg/m3 (35-42 ppt)
G = 9.81
T_GAS_C = 35.0                 # gas at module after submerged in-situ intercooler (<38 degC)
R_AIR = 287.05                 # J/(kg K)
GAMMA_AIR = 1.4
V_JET_TARGET = (35.0, 40.0)    # m/s, MASTER §2
F_OSC_TARGET_HZ = 65.0         # TRL-4 §2.3 (50-80 Hz band, L = 1.40 m loop)
F_OSC_BAND_HZ = (50.0, 80.0)
BLOWER_P_KPAG = (42.0, 45.0)

# Pressure budget items taken from MASTER §6 (kPa)
DP_HEADER = 3.0
DP_DUCKBILL = 1.5
DP_SLITS_BUDGET = (3.0, 4.0)

# ---------------------------------------------------------------------------
# 2. Slit comb (Parts 06/07) — MASTER §2 slit size, TRL-4 G1 web width
# ---------------------------------------------------------------------------
SLIT_GAP = 1.000               # normal throat
SLIT_LEN = 20.0                # length of one slit (along Y)
SLIT_WEB = 2.5                 # stiffening web between slits (TRL-4 G1)
SLIT_N = 11                    # per bank — derived from local gas density, see derived()
SLIT_ANGLE_DEG = 20.0          # discharge below horizontal, outward (product spec 15-25 deg)
SLIT_LINE = SLIT_N * SLIT_LEN + (SLIT_N - 1) * SLIT_WEB   # 245.0


def slit_y_ranges():
    """(y0, y1) of every slit, centred on Y = 0."""
    y = -SLIT_LINE / 2.0
    out = []
    for _ in range(SLIT_N):
        out.append((y, y + SLIT_LEN))
        y += SLIT_LEN + SLIT_WEB
    return out


# ---------------------------------------------------------------------------
# 3. Vertical levels
# ---------------------------------------------------------------------------
FOOT_Z = (0.0, 40.0)
FRAME_Z = (40.0, 80.0)
Z_FLOOR = 130.0                # plenum floor = cartridge pocket floor = slit rear lower edge
CH_H = 16.0                    # plenum duct / port / pocket height
M2_Z = (Z_FLOOR - 18.0, Z_FLOOR + CH_H + 18.0)   # Part 02: 112 .. 164
P4_Z = (M2_Z[1], M2_Z[1] + 30.0)                  # Part 04: 164 .. 194
CAV_DEPTH = 16.0                                   # oscillator cavity depth (h)
CAV_Z = (P4_Z[1] - CAV_DEPTH, P4_Z[1])            # 178 .. 194
P5_Z = (P4_Z[1], P4_Z[1] + 15.0)                  # Part 05: 194 .. 209
P8_Z0 = P5_Z[1]                                    # Part 08 bottom face: 209
P8_H = 90.0
P8_FLANGE_T = 10.0
P9_Z0 = P8_Z0 + P8_H                               # Part 09 bottom face: 299

# ---------------------------------------------------------------------------
# 4. Part 02 — twin-plenum manifold ("compact inverted air-bell")
# ---------------------------------------------------------------------------
M2_HX = 54.0                   # side (sealing) faces at X = +/-54
M2_HY = 146.0
DUCT_X_IN = 7.0                # integral central divider = 14 mm (replaces V2.2 Part 03)
DUCT_HY = 128.0                # plenum duct / port / pocket half length
DUCT_R = 5.0                   # corner radius of duct/port/pocket profile (YZ)
DUCT_ZC = Z_FLOOR + CH_H / 2.0
DOWNCOMER_XY = (22.0, -92.0)   # (+/-x, y)
DOWNCOMER_R = 8.0              # Ø16
M4_ROW_Z = (Z_FLOOR - 12.0, Z_FLOOR + CH_H + 12.0)            # 118, 158
M4_ROW_Y = (-137.0, -82.2, -27.4, 27.4, 82.2, 137.0)
# 6x M8 base bolts, inserted from below through the hollow pedestal; kept clear of the chassis
# X-bar (|y| <= 20): an M8 SHCS + head needs 28 mm of free height under the pedestal top plate.
M8_BASE_XY = ((-30.0, -100.0), (30.0, -100.0), (-30.0, 100.0), (30.0, 100.0), (0.0, -30.0), (0.0, 30.0))
TAP_PD_Z = DUCT_ZC             # P_DA / P_DB taps through the -Y end wall

# ---------------------------------------------------------------------------
# 5. Parts 06/07 — slit cartridges
# ---------------------------------------------------------------------------
CART_X = (M2_HX, M2_HX + 18.0)                 # rear 54 .. front 72
POCKET_DEPTH = 8.0
CART_FRONT_WALL = CART_X[1] - (CART_X[0] + POCKET_DEPTH)       # 10.0
SLIT_EXIT_Z_LOW = Z_FLOOR - CART_FRONT_WALL * math.tan(math.radians(SLIT_ANGLE_DEG))
SLIT_EXIT_Z_HIGH = SLIT_EXIT_Z_LOW + SLIT_GAP / math.cos(math.radians(SLIT_ANGLE_DEG))
CB_M4 = (4.0, 4.5)             # counterbore radius, depth (ISO 4762 M4)

# ---------------------------------------------------------------------------
# 6. Part 04 — Coanda bistable oscillator (loop / Warren type)
# ---------------------------------------------------------------------------
NOZ_B = 6.0                    # power nozzle width b (>= 6 mm anti-fouling rule)
PLENUM_R = 17.0                # supply plenum under the inlet
Y_CONTRACT0 = -12.0            # contraction starts (circle half-width 12.04)
Y_THROAT0 = -30.0
Y_NOZ_EXIT = -36.0             # throat length = b
CTRL_W = 6.0                   # control port width (= b)
SETBACK = 3.0                  # 0.5 b each side
CTRL_X_END = 35.5              # control channel end (barb hole inside)
WALL_ANGLE_DEG = 12.0          # attachment wall divergence
SPLITTER_DIST = 6.0 * NOZ_B    # 36 mm = 6 b
Y_SPLITTER = Y_NOZ_EXIT - SPLITTER_DIST                                   # -72
X_WALL_AT_SPLITTER = NOZ_B / 2 + SETBACK + (SPLITTER_DIST - CTRL_W) * math.tan(math.radians(WALL_ANGLE_DEG))
DC_POCKET_R = 9.0
BARB_XY = (32.0, Y_NOZ_EXIT - CTRL_W / 2.0)     # (+/-32, -39)
P45_Y = (-125.0, 40.0)         # Y extent of Parts 04/05
P45_HX = 54.0
# Cavity O-ring (2.62 cord) — rounded-rectangle groove in Part 04 top face
CAV_GROOVE_IN = dict(cx=0.0, cy=-42.0, hx=38.0, hy=61.5, r=8.0)
# M5 through-bolts (Part 05 + Part 04 -> heat-set inserts in Part 02)
M5_STACK_XY = ((-48.0, -110.0), (48.0, -110.0), (-48.0, -55.0), (48.0, -55.0), (-48.0, 0.0), (48.0, 0.0),
               (-30.0, -116.5), (30.0, -116.5), (-38.0, 31.5), (38.0, 31.5))
CB_M5 = (5.0, 5.5)

# ---------------------------------------------------------------------------
# 7. Part 05 / Part 08 / Part 09 — vertical supply stack
# ---------------------------------------------------------------------------
INLET_R = 16.0                 # Ø32 supply passage (Part 08 bottom -> Part 05 -> plenum)
P8_BOT_FLANGE_R = 42.0
P8_BODY_R = 29.0
P8_TOP_FLANGE_R = 52.0
DUCKBILL_BORE_R = 23.25        # Ø46.5 valve pocket
DUCKBILL_CB = (28.25, 3.2)     # flange-lip counterbore radius, depth (lip clamped by Part 09)
DUCKBILL_MAX_LEN = 60.0
P8_BOT_BOLT_PCD_R = 36.0       # 4x M5 into inserts in Part 05 (at 45/135/225/315 deg)
P8_TOP_BOLT_PCD_R = 46.0       # 4x M5 from below into inserts in Part 09 (0/90/180/270 deg)

P9_BASE_R = 52.0
P9_OUT_R = 68.0
P9_IN_R = 62.0
P9_WALL = P9_OUT_R - P9_IN_R
P9_FLOOR_SLOPE_DEG = 5.0       # inverted-cone floor, drains outward to the wall
P9_Z_FLOOR_WALL = P9_Z0 + 29.0                 # 328
STANDPIPE_R = (16.0, 20.0)     # bore, outer
STANDPIPE_RISE = 120.0         # above the floor low point (condensate hold-up margin)
HAT_R = 36.0
HAT_GAP = 12.0
HAT_T = 4.0
SOCKET_R = 30.35               # Ø60.7 socket for a 2" Sch40 pipe stub (OD 60.33) + Camlock
SOCKET_DEPTH = 38.0
SOCKET_SHOULDER_R = 26.0
ROOF_H = P9_IN_R - SOCKET_SHOULDER_R           # 45 deg roof
DRAIN_TAP_R = 9.15             # 1/2" NPT tap drill Ø18.3
DRAIN_BOSS_R = 15.0
TARGET_ACC_VOL_L = 4.30        # >= 4.25 L (V2.2 requirement kept)

# ---------------------------------------------------------------------------
# 8. Part 01 chassis / Part 10 ballast cradles
# ---------------------------------------------------------------------------
FRAME_HX, FRAME_HY, BAR = 235.0, 150.0, 40.0
PEDESTAL = dict(hx=M2_HX, hy=125.0, z0=FRAME_Z[1], z1=M2_Z[0], wall=8.0, top=8.0)
FEET_XY = ((-210.0, -118.0), (210.0, -118.0), (-210.0, 118.0), (210.0, 118.0))
FOOT_R = 28.0                  # stays inside Y = +/-150 so the ballast cradles clear the feet
FOOT_MUD_HOLE = (14.0, 4.0)    # offset, radius — mud-suction relief through foot and frame bar
DEFL_X0 = CART_X[1] + 2.0      # 74
DEFL_TOP_Z0 = SLIT_EXIT_Z_LOW - 12.0
DEFL_SLOPE_DEG = 10.0
DEFL_X1 = 205.0
DEFL_LIP_DEG = 20.0            # circulation vector (product spec 15-25 deg)
DEFL_X2 = 230.0
DEFL_T = 6.0
DEFL_HY = 115.0
BED_CLEARANCE_MIN = 75.0       # anti-scour rule (V2.2)
LIFT_HOLES_XY = ((-100.0, -130.0), (100.0, -130.0), (-100.0, 130.0), (100.0, 130.0))
CRADLE_BOLT_X = (-150.0, -50.0, 50.0, 150.0)
CRADLE_BOLT_Z = 60.0
BALLAST_BLOCK = (400.0, 200.0, 100.0)   # solid concrete, per cradle
RHO_CONCRETE = 2300.0

# ---------------------------------------------------------------------------
# 9. Seals & hardware (TRL-4 §0 O-ring standards)
# ---------------------------------------------------------------------------
ORING_262 = dict(cord=2.62, depth=2.00, width=3.60)   # oscillator, cartridges, downcomers
ORING_353 = dict(cord=3.53, depth=2.70, width=4.80)   # stack flanges (Parts 05/08/09)
# Circular face grooves sized so a standard ring sits against the outer wall (internal pressure)
DC_ORING = dict(id=23.47, **ORING_262)       # AS568-119 class, 2 per module
P8_ORING = dict(id=40.87, **ORING_353)       # AS568-223 class
P9_ORING = dict(id=66.27, **ORING_353)       # AS568-231 class
INSERT = {"M4": (2.8, 9.0), "M5": (3.2, 11.0), "M8": (5.0, 14.0)}   # hole radius, depth (brass heat-set)
CLEAR = {"M4": 2.25, "M5": 2.75, "M8": 4.5}                          # ISO 273 medium
TAP_M5_PILOT_R = 1.25
MATERIAL_DENSITY = {"PETG": 1270.0, "PA12": 1010.0}
MIN_LAND = 2.5                 # min sealing land between a groove and any other feature


def groove_radii_for(oring):
    """Circular face groove (inner, outer) radius; outer = ring OD/2 - 0.2 (1% pre-compression)."""
    r_out = (oring["id"] + 2.0 * oring["cord"]) / 2.0 - 0.2
    return r_out - oring["width"], r_out


# ---------------------------------------------------------------------------
# 10. Derived engineering values
# ---------------------------------------------------------------------------
def gas_density(p_kpa_abs, t_c):
    return p_kpa_abs * 1000.0 / (R_AIR * (t_c + 273.15))


def accumulator_levels():
    """Z of roof start, shoulder and socket top that give TARGET_ACC_VOL_L of gas volume."""
    t5 = math.tan(math.radians(P9_FLOOR_SLOPE_DEG))
    r_sp_o = STANDPIPE_R[1]
    z_sp_top = P9_Z_FLOOR_WALL + STANDPIPE_RISE
    # volume displaced by the raised (inverted-cone) floor between r_sp_o and P9_IN_R
    a, b = r_sp_o, P9_IN_R
    v_floor = 2 * math.pi * t5 * ((b * b ** 2 / 2 - b ** 3 / 3) - (b * a ** 2 / 2 - a ** 3 / 3))
    v_sp_wall = math.pi * (STANDPIPE_R[1] ** 2 - STANDPIPE_R[0] ** 2) * (z_sp_top - P9_Z_FLOOR_WALL)
    h = ROOF_H
    v_roof = math.pi * h / 3 * (P9_IN_R ** 2 + P9_IN_R * SOCKET_SHOULDER_R + SOCKET_SHOULDER_R ** 2)
    ri = HAT_R - HAT_T * math.sqrt(2)
    v_hat = math.pi * HAT_R ** 3 / 3 - math.pi * ri ** 3 / 3
    v_ribs = 3 * 4.0 * 150.0
    area = math.pi * P9_IN_R ** 2
    fixed = -v_floor - v_sp_wall + v_roof - v_hat - v_ribs
    h_cyl = (TARGET_ACC_VOL_L * 1e6 - fixed) / area
    z_rs = math.ceil(P9_Z_FLOOR_WALL + h_cyl)
    z_sh = z_rs + ROOF_H
    vol = area * (z_rs - P9_Z_FLOOR_WALL) + fixed
    return dict(z_sp_top=z_sp_top, z_roof_start=z_rs, z_shoulder=z_sh,
                z_socket_top=z_sh + SOCKET_DEPTH, gas_volume_l=vol / 1e6,
                z_floor_centre=P9_Z_FLOOR_WALL + (P9_IN_R - r_sp_o) * t5)


def derived():
    d = {}
    m_dot = Q_NORMAL_M3H * RHO_NORMAL / 3600.0
    d["mass_flow_kg_s"] = m_dot
    slit_depth_m = POND_DEPTH_M - SLIT_EXIT_Z_LOW / 1000.0
    p_slit = P_ATM_KPA + RHO_SEAWATER * G * slit_depth_m / 1000.0
    d["slit_depth_m"] = slit_depth_m
    d["p_slit_exit_kpa_abs"] = p_slit
    rho_slit = gas_density(p_slit, T_GAS_C)
    q_slit = m_dot / rho_slit
    d["q_actual_at_slits_m3h"] = q_slit * 3600
    a_bank = SLIT_N * SLIT_LEN * SLIT_GAP
    d["slit_area_per_bank_mm2"] = a_bank
    d["v_jet_m_s"] = q_slit / (a_bank * 1e-6)
    v_mid = sum(V_JET_TARGET) / 2.0
    d["slits_required_for_target"] = q_slit / (v_mid * SLIT_LEN * SLIT_GAP * 1e-6)
    # MASTER §2 used the blower-outlet density (42 kPa(g), 55 degC):
    rho_master = gas_density(P_ATM_KPA + 42.0, 55.0)
    d["q_master_basis_m3h"] = m_dot / rho_master * 3600
    d["v_jet_if_9_slits_m_s"] = q_slit / (9 * SLIT_LEN * SLIT_GAP * 1e-6)
    # Slit pressure drop estimate: K = 0.5 entry + 1.0 exit + f L/Dh
    dh = 2 * SLIT_GAP * SLIT_LEN / (SLIT_GAP + SLIT_LEN) / 1000.0
    l_ch = CART_FRONT_WALL / math.cos(math.radians(SLIT_ANGLE_DEG)) / 1000.0
    q_dyn = 0.5 * rho_slit * d["v_jet_m_s"] ** 2
    d["dp_slit_kpa"] = (1.5 + 0.035 * l_ch / dh) * q_dyn / 1000.0
    # Oscillator nozzle
    p_noz = p_slit + max(DP_SLITS_BUDGET) + 1.0
    rho_noz = gas_density(p_noz, T_GAS_C)
    a_noz = NOZ_B * CAV_DEPTH
    d["nozzle_area_mm2"] = a_noz
    d["nozzle_aspect"] = CAV_DEPTH / NOZ_B
    d["v_nozzle_m_s"] = m_dot / rho_noz / (a_noz * 1e-6)
    d["q_nozzle_dyn_kpa"] = 0.5 * rho_noz * d["v_nozzle_m_s"] ** 2 / 1000.0
    d["dp_oscillator_est_kpa"] = 0.75 * d["q_nozzle_dyn_kpa"] + 0.3
    d["splitter_dist_over_b"] = SPLITTER_DIST / NOZ_B
    d["output_width_at_splitter_over_b"] = X_WALL_AT_SPLITTER / NOZ_B
    # Plenum capacitance per bank (Part 02 duct+port, cartridge pocket, downcomer, output pocket)
    duct_area = (2 * DUCT_HY) * CH_H - (4 - math.pi) * DUCT_R ** 2
    v_duct = duct_area * (M2_HX - DUCT_X_IN)
    v_pocket = duct_area * POCKET_DEPTH
    v_dc = math.pi * DOWNCOMER_R ** 2 * ((M2_Z[1] - (Z_FLOOR + CH_H)) + (CAV_Z[0] - P4_Z[0]))
    v_out = 900.0 * CAV_DEPTH
    v_bank = v_duct + v_pocket + v_dc + v_out
    d["plenum_volume_per_bank_ml"] = v_bank / 1000.0
    dp_lin = 2.0 * (d["dp_slit_kpa"] + 1.0) * 1000.0 / q_slit          # Pa s / m3
    c_pn = v_bank * 1e-9 / (GAMMA_AIR * p_slit * 1000.0)
    tau = dp_lin * c_pn
    d["plenum_tau_ms"] = tau * 1000.0
    w = 2 * math.pi * F_OSC_TARGET_HZ
    d["pulse_amplitude_ratio_at_target"] = 1.0 / math.sqrt(1.0 + (w * tau) ** 2)
    d["duct_velocity_m_s"] = (q_slit * (DUCT_HY - DOWNCOMER_XY[1]) / (2 * DUCT_HY)) / (
        (M2_HX - DUCT_X_IN) * CH_H * 1e-6)
    # Dry-core check: gas trapped downstream of the duckbill (blower off)
    v_osc_cav = 6500.0 * CAV_DEPTH
    v_loop = math.pi * 4.0 ** 2 * 1400.0
    v_stack_below_valve = math.pi * INLET_R ** 2 * 25.0 + math.pi * DUCKBILL_BORE_R ** 2 * 20.0
    v_trapped = 2 * v_bank + v_osc_cav + v_loop + v_stack_below_valve
    d["trapped_volume_ml"] = v_trapped / 1000.0
    compression = 1.0 - P_ATM_KPA / p_slit                  # first submersion from surface
    cooling = 1.0 - (T_GAS_C + 273.15) / (55.0 + 273.15)    # hot-gas shutdown (worst case)
    floor_area = 2 * (duct_area / CH_H * (M2_HX - DUCT_X_IN) + duct_area / CH_H * POCKET_DEPTH)
    for key, frac in (("first_submersion", compression), ("hot_shutdown", cooling)):
        v_in = v_trapped * frac
        d[f"water_ingress_{key}_ml"] = v_in / 1000.0
        d[f"water_rise_{key}_mm"] = v_in / floor_area
    d["dry_core_margin_mm"] = CH_H
    # Accumulator
    acc = accumulator_levels()
    d.update({f"acc_{k}": v for k, v in acc.items()})
    # Pressure budget
    d["dp_total_kpa"] = (DP_HEADER + DP_DUCKBILL + d["dp_oscillator_est_kpa"] + 0.3
                         + max(DP_SLITS_BUDGET) + RHO_SEAWATER * G * slit_depth_m / 1000.0)
    d["blower_margin_kpa"] = BLOWER_P_KPAG[0] - d["dp_total_kpa"]
    # Deflector
    t10 = math.tan(math.radians(DEFL_SLOPE_DEG))
    d["deflector_lowest_bottom_z"] = DEFL_TOP_Z0 - (DEFL_X1 - DEFL_X0) * t10 - DEFL_T
    return d


def oring_check(o):
    squeeze = (o["cord"] - o["depth"]) / o["cord"]
    fill = (math.pi / 4 * o["cord"] ** 2) / (o["depth"] * o["width"])
    return squeeze, fill


def rule_checks():
    """List of (rule, value, requirement, ok). Generator aborts if any fails."""
    d = derived()
    r = []

    def add(name, val, req, ok):
        r.append((name, val, req, bool(ok)))

    add("Jet velocity at slit-exit conditions [m/s]", round(d["v_jet_m_s"], 1), "35-40 (MASTER §2)",
        V_JET_TARGET[0] <= d["v_jet_m_s"] <= V_JET_TARGET[1])
    add("Slit pressure drop estimate [kPa]", round(d["dp_slit_kpa"], 2), "<= 4.0 (MASTER §6)", d["dp_slit_kpa"] <= 4.0)
    add("Nozzle width b [mm]", NOZ_B, ">= 6 (anti-fouling)", NOZ_B >= 6.0)
    add("Nozzle aspect ratio h/b", round(d["nozzle_aspect"], 2), ">= 2", d["nozzle_aspect"] >= 2.0)
    add("Splitter distance / b", round(d["splitter_dist_over_b"], 2), "4-8", 4.0 <= d["splitter_dist_over_b"] <= 8.0)
    add("Oscillator loss estimate [kPa]", round(d["dp_oscillator_est_kpa"], 2), "<= 8 (MASTER §6)",
        d["dp_oscillator_est_kpa"] <= 8.0)
    add("Pulse amplitude transmitted to slits @65 Hz", round(d["pulse_amplitude_ratio_at_target"], 3), ">= 0.80",
        d["pulse_amplitude_ratio_at_target"] >= 0.80)
    add("Plenum duct velocity [m/s]", round(d["duct_velocity_m_s"], 1), "<= 12 (uniform feed)", d["duct_velocity_m_s"] <= 12)
    add("Water rise, first submersion [mm]", round(d["water_rise_first_submersion_mm"], 1),
        f"< {CH_H} (dry core)", d["water_rise_first_submersion_mm"] < CH_H * 0.6)
    add("Water rise, hot shutdown [mm]", round(d["water_rise_hot_shutdown_mm"], 1),
        f"< {CH_H} (dry core)", d["water_rise_hot_shutdown_mm"] < CH_H * 0.6)
    add("Accumulator gas volume [L]", round(d["acc_gas_volume_l"], 3), ">= 4.25", d["acc_gas_volume_l"] >= 4.25)
    add("Blower pressure margin [kPa]", round(d["blower_margin_kpa"], 1), ">= 5", d["blower_margin_kpa"] >= 5.0)
    add("Deflector bed clearance [mm]", round(d["deflector_lowest_bottom_z"], 1), f">= {BED_CLEARANCE_MIN}",
        d["deflector_lowest_bottom_z"] >= BED_CLEARANCE_MIN)
    add("Slit discharge angle [deg]", SLIT_ANGLE_DEG, "15-25", 15 <= SLIT_ANGLE_DEG <= 25)
    add("Deflector exit lip angle [deg]", DEFL_LIP_DEG, "15-25", 15 <= DEFL_LIP_DEG <= 25)
    for name, o in (("2.62 cord", ORING_262), ("3.53 cord", ORING_353)):
        sq, fill = oring_check(o)
        add(f"O-ring {name} squeeze", round(sq, 3), "0.15-0.30 (static face seal)", 0.15 <= sq <= 0.30)
        add(f"O-ring {name} gland fill", round(fill, 3), "<= 0.85", fill <= 0.85)
    # land checks for the circular stack grooves
    ri, ro = groove_radii_for(P8_ORING)
    add("Part 08 groove land to bore [mm]", round(ri - INLET_R, 2), f">= {MIN_LAND}", ri - INLET_R >= MIN_LAND)
    add("Part 08 groove land to bolt holes [mm]", round(P8_BOT_BOLT_PCD_R - CLEAR["M5"] - ro, 2), f">= {MIN_LAND}",
        P8_BOT_BOLT_PCD_R - CLEAR["M5"] - ro >= MIN_LAND)
    ri, ro = groove_radii_for(P9_ORING)
    add("Part 09 groove land to duckbill lip [mm]", round(ri - DUCKBILL_CB[0], 2), f">= {MIN_LAND}",
        ri - DUCKBILL_CB[0] >= MIN_LAND)
    add("Part 09 groove land to inserts [mm]", round(P8_TOP_BOLT_PCD_R - INSERT['M5'][0] - ro, 2), f">= {MIN_LAND}",
        P8_TOP_BOLT_PCD_R - INSERT["M5"][0] - ro >= MIN_LAND)
    ri, ro = groove_radii_for(DC_ORING)
    add("Downcomer groove land to bore [mm]", round(ri - DOWNCOMER_R, 2), f">= {MIN_LAND}", ri - DOWNCOMER_R >= MIN_LAND)
    add("Duckbill tip clearance [mm]",
        round((P9_Z0 - DUCKBILL_CB[1] - DUCKBILL_MAX_LEN) - (P8_Z0 + P8_FLANGE_T), 1), ">= 10",
        (P9_Z0 - DUCKBILL_CB[1] - DUCKBILL_MAX_LEN) - (P8_Z0 + P8_FLANGE_T) >= 10)
    return r


if __name__ == "__main__":
    for k, v in derived().items():
        print(f"{k:42s} {v:.4f}" if isinstance(v, float) else f"{k:42s} {v}")
    print()
    for name, val, req, ok in rule_checks():
        print(f"[{'PASS' if ok else 'FAIL'}] {name}: {val}  (req {req})")
