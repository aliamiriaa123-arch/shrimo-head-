"""
Aeration physics toolkit — first-principles energy/oxygen model for shrimp-pond aerators.

Pure Python (no third-party imports), same convention as spd_design_params.py.

What it answers:
    * How much oxygen does a bubble of diameter d transfer while rising H metres
      (discrete-bubble model, McGinnis & Little 2002, Wuest et al. 1992 correlations)?
    * How much electricity does it cost to push 1 Nm3 of air to a given pressure?
    * What is SAE (kg O2 / kWh, standard conditions) and what does the farmer actually get
      in hot hypersaline water at DO = 4 mg/L (field SAE)?

Conventions:
    SI units unless the name says otherwise.  Standard air = Nm3 at 0 degC, 101.325 kPa.
    "Standard conditions" for SOTE/SOTR/SAE = clean fresh water, 20 degC, 1 atm, DO = 0
    (ASCE 2-06).  All efficiencies are wire-to-air (electrical input -> adiabatic air power).

Accuracy:
    Absolute SOTE predictions of a single-size discrete-bubble model are +/-30 %.
    Relative comparisons (bubble size, depth, plume velocity, pressure loss) are robust.
    Calibrate kl_factor against the first clean-water tank test (see kla_fit.py).
"""

import math

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
P_ATM = 101325.0                 # Pa
R_GAS = 8.314462618              # J/(mol K)
G = 9.81                         # m/s2
T0 = 273.15                      # K
X_O2 = 0.20946                   # dry-air mole fraction
X_N2 = 0.78084 + 0.00934         # N2 + Ar lumped as "N2"
M_O2 = 31.9988e-3                # kg/mol
M_N2 = 28.0134e-3
GAMMA_AIR = 1.4
KG_O2_PER_NM3_AIR = X_O2 * P_ATM * M_O2 / (R_GAS * T0)   # 0.2995 kg O2 per Nm3 of air
THETA = 1.024                    # kLa temperature coefficient (ASCE 2-06)
C_SAT_20_FRESH = 9.09            # mg/L, 20 degC, 0 ppt, 1 atm (ASCE reference)


# ---------------------------------------------------------------------------
# Water and gas properties
# ---------------------------------------------------------------------------
def water_density(t_c, s_ppt=0.0):
    """kg/m3. Thiesen formula for pure water + 0.76 kg/m3 per ppt salinity (+/-0.2 %)."""
    rho0 = 1000.0 * (1.0 - (t_c + 288.9414) / (508929.2 * (t_c + 68.12963)) * (t_c - 3.9863) ** 2)
    return rho0 + 0.76 * s_ppt


def vapor_pressure(t_c, s_ppt=0.0):
    """Pa. Buck (1996) over water, lowered ~0.054 %/ppt for seawater (Raoult)."""
    p = 611.21 * math.exp((18.678 - t_c / 234.5) * (t_c / (257.14 + t_c)))
    return p * (1.0 - 0.000537 * s_ppt)


# Weiss (1970) solubility from moist air at 1 atm total pressure, mL(STP)/L
_WEISS = {
    "O2": (-173.4292, 249.6339, 143.3483, -21.8492, -0.033096, 0.014259, -0.0017000),
    "N2": (-172.4965, 248.4262, 143.0738, -21.7120, -0.049781, 0.025018, -0.0034861),
}
_STP_DENSITY_MG_PER_ML = {"O2": 1.42905, "N2": 1.25046}
_MOLAR_MASS = {"O2": M_O2, "N2": M_N2}
_X_AIR = {"O2": X_O2, "N2": X_N2}


def solubility_mg_l(gas, t_c, s_ppt, p_total_pa=P_ATM):
    """Equilibrium concentration (mg/L) with moist air at total pressure p_total_pa."""
    a1, a2, a3, a4, b1, b2, b3 = _WEISS[gas]
    tk = (t_c + T0) / 100.0
    ln_c = a1 + a2 / tk + a3 * math.log(tk) + a4 * tk + s_ppt * (b1 + b2 * tk + b3 * tk * tk)
    c = math.exp(ln_c) * _STP_DENSITY_MG_PER_ML[gas]
    pwv = vapor_pressure(t_c, s_ppt)
    return c * (p_total_pa - pwv) / (P_ATM - pwv)


def do_saturation_mg_l(t_c, s_ppt, p_total_pa=P_ATM):
    return solubility_mg_l("O2", t_c, s_ppt, p_total_pa)


def henry_mol_m3_pa(gas, t_c, s_ppt):
    """Liquid concentration (mol/m3) in equilibrium with 1 Pa partial pressure of gas."""
    c_mol_m3 = solubility_mg_l(gas, t_c, s_ppt) / 1000.0 / _MOLAR_MASS[gas]
    return c_mol_m3 / (_X_AIR[gas] * (P_ATM - vapor_pressure(t_c, s_ppt)))


# ---------------------------------------------------------------------------
# Bubble correlations (Wuest, Brooks & Imboden 1992; used by McGinnis & Little 2002)
# ---------------------------------------------------------------------------
def bubble_slip_velocity(r_m):
    """Terminal slip velocity (m/s) of a bubble of radius r in natural water."""
    if r_m < 7.0e-4:
        return 4474.0 * r_m ** 1.357
    if r_m < 5.1e-3:
        return 0.23
    return 4.202 * r_m ** 0.547


def bubble_kl(r_m):
    """Liquid-side mass-transfer coefficient (m/s) at 20 degC."""
    return 0.6 * r_m if r_m < 6.67e-4 else 4.0e-4


# ---------------------------------------------------------------------------
# Plume velocity (liquid upflow that the bubbles ride on)
# ---------------------------------------------------------------------------
def line_plume_velocity(q_m2_s, coeff=1.5):
    """Mean upward liquid velocity of a line bubble plume, u = C (g q)^(1/3).
    q = gas volume flux per metre of source length at plume conditions (m2/s).
    C ~ 1.46 for the surface current of a bubble curtain (Bulson 1961); 1.5 used as a
    bubble-weighted mean.  Order-of-magnitude estimate only."""
    return coeff * (G * q_m2_s) ** (1.0 / 3.0)


def actual_gas_flow_m3_s(q_nm3_h, depth_m, t_c, s_ppt=0.0):
    """Nm3/h -> actual m3/s at depth (gas at water temperature)."""
    p = P_ATM + water_density(t_c, s_ppt) * G * depth_m
    return q_nm3_h / 3600.0 * (P_ATM / p) * ((t_c + T0) / T0)


# ---------------------------------------------------------------------------
# Discrete-bubble model
# ---------------------------------------------------------------------------
def discrete_bubble(d0_mm, depth_m, t_c=20.0, s_ppt=0.0, do_mg_l=0.0, u_liquid=0.0,
                    kl_factor=1.0, dz=0.002):
    """Follow one bubble released at depth_m (m below the surface) up to the surface.

    d0_mm      bubble diameter at release (after detachment / near-field coalescence)
    u_liquid   upward liquid velocity the bubble rides on (plume), m/s
    kl_factor  contamination / calibration multiplier on kL (1.0 = Wuest correlation)

    Returns dict: ote (fraction of O2 transferred), d_exit_mm, residence_s.
    Liquid N2 is held at surface saturation (true in an ASCE sulfite test and in ponds).
    """
    tk = t_c + T0
    rho = water_density(t_c, s_ppt)
    pwv = vapor_pressure(t_c, s_ppt)
    kh_o2 = henry_mol_m3_pa("O2", t_c, s_ppt)
    kh_n2 = henry_mol_m3_pa("N2", t_c, s_ppt)
    c_o2 = do_mg_l / 1000.0 / M_O2
    c_n2 = solubility_mg_l("N2", t_c, s_ppt) / 1000.0 / M_N2
    temp_corr = THETA ** (t_c - 20.0)
    kl_ratio_n2 = math.sqrt(1.88 / 2.10)     # D_N2 / D_O2, Higbie scaling

    p_dry = P_ATM + rho * G * depth_m - pwv
    v0 = math.pi / 6.0 * (d0_mm / 1000.0) ** 3
    n = p_dry * v0 / (R_GAS * tk)
    n_o2, n_n2 = n * X_O2, n * X_N2
    n_o2_0 = n_o2
    h, t = depth_m, 0.0
    while h > 0.0:
        step = min(dz, h)
        hm = h - step / 2.0
        p_dry = P_ATM + rho * G * hm - pwv
        n_tot = n_o2 + n_n2
        vol = n_tot * R_GAS * tk / p_dry
        d = (6.0 * vol / math.pi) ** (1.0 / 3.0)
        r = d / 2.0
        vel = bubble_slip_velocity(r) + u_liquid
        dt = step / vel
        area = math.pi * d * d
        kl = kl_factor * bubble_kl(r) * temp_corr
        f_o2 = kl * area * (kh_o2 * (n_o2 / n_tot) * p_dry - c_o2)
        f_n2 = kl * kl_ratio_n2 * area * (kh_n2 * (n_n2 / n_tot) * p_dry - c_n2)
        n_o2 = max(n_o2 - f_o2 * dt, 0.0)
        n_n2 = max(n_n2 - f_n2 * dt, 0.0)
        h -= step
        t += dt
    vol = (n_o2 + n_n2) * R_GAS * tk / (P_ATM - pwv)
    return {
        "ote": 1.0 - n_o2 / n_o2_0,
        "d_exit_mm": (6.0 * vol / math.pi) ** (1.0 / 3.0) * 1000.0,
        "residence_s": t,
    }


def sote_standard(d0_mm, submergence_m, u_liquid=0.0, kl_factor=1.0):
    """Standard oxygen transfer efficiency (clean fresh water, 20 degC, DO = 0)."""
    return discrete_bubble(d0_mm, submergence_m, 20.0, 0.0, 0.0, u_liquid, kl_factor)["ote"]


# ---------------------------------------------------------------------------
# Blower energy
# ---------------------------------------------------------------------------
def blower_kwh_per_nm3(dp_total_kpa, eta_wire_to_air, t_inlet_c=35.0, p_inlet_pa=P_ATM):
    """Electrical energy (kWh) per Nm3 of air delivered at dp_total_kpa above inlet.
    Adiabatic air power / wire-to-air efficiency (the blower-industry definition)."""
    v_actual = (t_inlet_c + T0) / T0 * P_ATM / p_inlet_pa           # m3 per Nm3
    pr = (p_inlet_pa + dp_total_kpa * 1000.0) / p_inlet_pa
    k = GAMMA_AIR
    w = k / (k - 1.0) * p_inlet_pa * v_actual * (pr ** ((k - 1.0) / k) - 1.0)
    return w / eta_wire_to_air / 3.6e6


def sae_standard(sote, dp_total_kpa, eta_wire_to_air, t_inlet_c=35.0):
    """Standard aeration efficiency, kg O2 per kWh (wire)."""
    return sote * KG_O2_PER_NM3_AIR / blower_kwh_per_nm3(dp_total_kpa, eta_wire_to_air, t_inlet_c)


# ---------------------------------------------------------------------------
# Field correction (what the farmer gets)
# ---------------------------------------------------------------------------
def field_factor(t_c, s_ppt, do_mg_l, alpha, submergence_m=0.0, p_total_pa=P_ATM):
    """OTR_field / SOTR  =  alpha * theta^(T-20) * (C*_inf,field - C) / C*_inf,20.

    C*_inf is raised above surface saturation by the effective depth of a diffused-air
    system (~0.4 x submergence, ASCE 2-06 / EPA 1989).  submergence_m = 0 for surface
    aerators.  Salinity is inside C*_field, so no separate beta factor is applied.
    """
    rho = water_density(t_c, s_ppt)
    de = 0.4 * submergence_m
    boost_field = 1.0 + rho * G * de / p_total_pa
    boost_std = 1.0 + water_density(20.0) * G * de / P_ATM
    c_inf_field = do_saturation_mg_l(t_c, s_ppt, p_total_pa) * boost_field
    c_inf_std = C_SAT_20_FRESH * boost_std
    return alpha * THETA ** (t_c - 20.0) * max(c_inf_field - do_mg_l, 0.0) / c_inf_std


# ---------------------------------------------------------------------------
# Pure / enriched oxygen route (field efficiency directly)
# ---------------------------------------------------------------------------
def oxygen_route_field_kg_per_kwh(o2_generation_kwh_per_kg, absorption_eff, dissolution_kwh_per_kg):
    """kg O2 dissolved per kWh for an oxygen generator + contactor.
    o2_generation_kwh_per_kg: VPSA 0.25-0.35, small PSA 0.7-1.0 (kWh per kg O2 produced)
    dissolution_kwh_per_kg:   pumping energy of the contactor per kg O2 dissolved
    Driving force (C* ~ 25-40 mg/L) makes this nearly independent of pond DO at 4-6 mg/L."""
    return 1.0 / (o2_generation_kwh_per_kg / absorption_eff + dissolution_kwh_per_kg)


if __name__ == "__main__":
    print(f"kg O2 per Nm3 air                  {KG_O2_PER_NM3_AIR:.4f}")
    for t, s in ((20, 0), (30, 35), (33, 42), (35, 42)):
        print(f"DO sat {t:>2} degC {s:>2} ppt             {do_saturation_mg_l(t, s):.2f} mg/L")
    for d in (0.5, 1.0, 2.0, 3.0, 5.0):
        print(f"SOTE d={d} mm, 1.35 m, u_l=0      {sote_standard(d, 1.35):.3f}")
