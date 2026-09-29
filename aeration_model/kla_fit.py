"""
ASCE 2-06 style clean-water reaeration analysis for the tank tests.

Input CSV: two columns  time_s,do_mg_l  (header line optional), one file per DO probe.
Fits  C(t) = Cinf - (Cinf - C0) * exp(-kLa * t)  by nonlinear least squares
(for a fixed kLa the model is linear in Cinf and C0, so kLa is found by a 1-D search).

Run:
    python kla_fit.py probe1.csv --volume 12.5 --temp 24.1 --airflow 18.0 --power 0.21
        volume   m3 of water in the tank
        temp     water temperature, degC
        airflow  Nm3/h supplied to the diffuser under test
        power    kW electrical (wire) of the blower at that operating point
Outputs kLa20, Cinf20, SOTR, SOTE and SAE (standard conditions).
"""

import argparse
import csv
import math

from aeration_physics import C_SAT_20_FRESH, KG_O2_PER_NM3_AIR, THETA, do_saturation_mg_l


def _linear_fit(t, c, kla):
    """For fixed kLa: C = a + b*x with x = exp(-kLa t); returns a (=Cinf), a+b (=C0), SSE."""
    x = [math.exp(-kla * ti) for ti in t]
    n = len(t)
    sx, sy = sum(x), sum(c)
    sxx = sum(xi * xi for xi in x)
    sxy = sum(xi * yi for xi, yi in zip(x, c))
    den = n * sxx - sx * sx
    b = (n * sxy - sx * sy) / den
    a = (sy - b * sx) / n
    sse = sum((a + b * xi - yi) ** 2 for xi, yi in zip(x, c))
    return a, a + b, sse


def fit_reaeration(t, c, kla_bounds=(1e-5, 1.0)):
    """Return dict(kla [1/s], c_inf, c0, rmse). Golden-section search on log(kLa)."""
    lo, hi = math.log(kla_bounds[0]), math.log(kla_bounds[1])
    # coarse scan first to bracket the global minimum
    grid = [lo + (hi - lo) * i / 200 for i in range(201)]
    sse = [_linear_fit(t, c, math.exp(g))[2] for g in grid]
    i = min(range(len(grid)), key=sse.__getitem__)
    lo, hi = grid[max(i - 1, 0)], grid[min(i + 1, len(grid) - 1)]
    gr = (math.sqrt(5) - 1) / 2
    x1, x2 = hi - gr * (hi - lo), lo + gr * (hi - lo)
    f1, f2 = _linear_fit(t, c, math.exp(x1))[2], _linear_fit(t, c, math.exp(x2))[2]
    for _ in range(100):
        if f1 < f2:
            hi, x2, f2 = x2, x1, f1
            x1 = hi - gr * (hi - lo)
            f1 = _linear_fit(t, c, math.exp(x1))[2]
        else:
            lo, x1, f1 = x1, x2, f2
            x2 = lo + gr * (hi - lo)
            f2 = _linear_fit(t, c, math.exp(x2))[2]
    kla = math.exp((lo + hi) / 2)
    c_inf, c0, s = _linear_fit(t, c, kla)
    return {"kla": kla, "c_inf": c_inf, "c0": c0, "rmse": math.sqrt(s / len(t))}


def truncate_asce(t, c, c_inf_guess, low=0.20, high=0.98):
    """ASCE 2-06: use data from <=20 % to >=80 % of saturation, drop points above 98 %."""
    keep = [(ti, ci) for ti, ci in zip(t, c) if ci <= high * c_inf_guess]
    start = next((k for k, (_, ci) in enumerate(keep) if ci >= 0.0), 0)
    first_low = next((k for k, (_, ci) in enumerate(keep) if ci <= low * c_inf_guess), start)
    keep = keep[first_low:]
    return [k[0] - keep[0][0] for k in keep], [k[1] for k in keep]


def standardize(fit, volume_m3, temp_c, airflow_nm3_h=None, power_kw=None):
    """kLa20, Cinf20 and standard SOTR (kg/h); SOTE and SAE if airflow / power given.
    Cinf20 is scaled by the ratio of surface saturation values (tau), barometric Omega = 1."""
    kla20 = fit["kla"] * THETA ** (20.0 - temp_c)
    tau = do_saturation_mg_l(temp_c, 0.0) / C_SAT_20_FRESH
    c_inf20 = fit["c_inf"] / tau
    sotr = kla20 * 3600.0 * c_inf20 * volume_m3 / 1000.0          # kg O2/h
    out = {"kla20_per_h": kla20 * 3600.0, "c_inf20": c_inf20, "sotr_kg_h": sotr}
    if airflow_nm3_h:
        out["sote"] = sotr / (airflow_nm3_h * KG_O2_PER_NM3_AIR)
    if power_kw:
        out["sae_kg_kwh"] = sotr / power_kw
    return out


def read_csv(path):
    t, c = [], []
    with open(path, newline="") as f:
        for row in csv.reader(f):
            try:
                t.append(float(row[0]))
                c.append(float(row[1]))
            except (ValueError, IndexError):
                continue                                          # header / blank lines
    return t, c


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv", nargs="+")
    ap.add_argument("--volume", type=float, required=True)
    ap.add_argument("--temp", type=float, required=True)
    ap.add_argument("--airflow", type=float)
    ap.add_argument("--power", type=float)
    a = ap.parse_args()
    for path in a.csv:
        t, c = read_csv(path)
        first = fit_reaeration(t, c)
        t, c = truncate_asce(t, c, first["c_inf"])
        fit = fit_reaeration(t, c)
        std = standardize(fit, a.volume, a.temp, a.airflow, a.power)
        print(f"{path}: kLa_T = {fit['kla'] * 3600:.2f} 1/h, Cinf = {fit['c_inf']:.2f} mg/L, "
              f"RMSE = {fit['rmse']:.3f} mg/L, n = {len(t)}")
        print("   " + ", ".join(f"{k} = {v:.3f}" for k, v in std.items()))


if __name__ == "__main__":
    main()
