"""
Side-by-side energy/oxygen comparison of aerator architectures for a 1 ha, 1.5 m deep
shrimp pond in Persian-Gulf summer conditions.

Run:  python compare_architectures.py            (prints markdown tables)

Every number that is an assumption rather than physics is in SCENARIOS below with a note.
Change it there, not in the physics module.
"""

from aeration_physics import (
    KG_O2_PER_NM3_AIR, actual_gas_flow_m3_s, blower_kwh_per_nm3, field_factor,
    line_plume_velocity, oxygen_route_field_kg_per_kwh, sae_standard, sote_standard,
    water_density, G,
)

# ---------------------------------------------------------------------------
# Site basis
# ---------------------------------------------------------------------------
POND_DEPTH = 1.50
FIELD_T, FIELD_S, FIELD_DO = 33.0, 42.0, 4.0     # night-time design point (Bushehr/Hormozgan summer)
NIGHT_DEMAND_KG_H = 24.0                          # kg O2/h per ha at ~30 t biomass (MASTER §5)
BLOWER_INLET_T = 35.0


def hydro_kpa(submergence_m):
    return water_density(FIELD_T, FIELD_S) * G * submergence_m / 1000.0


def line_u(q_nm3_h_per_m, submergence_m, reduction=1.0):
    q = actual_gas_flow_m3_s(q_nm3_h_per_m, submergence_m / 2.0, FIELD_T, FIELD_S)
    return line_plume_velocity(q) * reduction


# ---------------------------------------------------------------------------
# Diffused-air scenarios
#   d_mm      effective (volume-weighted) bubble diameter after near-field coalescence
#   u_l       liquid upflow the bubbles ride on (m/s)
#   dp_dev    device pressure loss (kPa) = diffuser/oscillator/valves/orifices
#   dp_pipe   header + laterals (kPa)
#   eta       blower wire-to-air efficiency
#   alpha     field alpha factor (pond water / clean water)
#   extra_kw  other power per ha (circulation mixers)
# ---------------------------------------------------------------------------
SUB_TUBE = POND_DEPTH - 0.15          # diffuser lines on sleds 15 cm above the bottom
SUB_SPD = 1.3736                      # spd_design_params.derived()["slit_depth_m"]

SCENARIOS = [
    dict(key="aerotube", name="Aerotube grid, as typically run (Roots)",
         d_mm=3.5, u_l=0.30, sub=SUB_TUBE, dp_dev=8.0, dp_pipe=8.0, eta=0.55, alpha=0.85, extra_kw=0.0,
         note="d, u_l and operating pressure are ASSUMPTIONS: measure blower discharge pressure on farms"),
    dict(key="spd_claim", name="SPD V3 (current project), claimed d32 = 1.25 mm",
         d_mm=1.25, u_l=0.82, sub=SUB_SPD, dp_dev=None, dp_pipe=None, eta=0.55, alpha=0.80, extra_kw=0.0,
         note="dp from spd_design_params (26.4 kPa total); u_l = compact 30 Nm3/h source"),
    dict(key="spd_likely", name="SPD V3, likely d32 = 4 mm (dense plume)",
         d_mm=4.0, u_l=0.82, sub=SUB_SPD, dp_dev=None, dp_pipe=None, eta=0.55, alpha=0.85, extra_kw=0.0,
         note="Hinze limit in a 0.1 W/kg plume ~6 mm; 5.8 mL of gas per slit per pulse"),
    dict(key="llfb_roots", name="PROPOSED LLFB on existing Roots + VFD",
         d_mm=2.0, u_l=line_u(2.0, SUB_TUBE), sub=SUB_TUBE, dp_dev=3.0, dp_pipe=2.0, eta=0.55, alpha=0.85,
         extra_kw=1.0, note="EPDM slit-membrane tubes, 2 Nm3/h per metre, low-velocity headers"),
    dict(key="llfb_flow", name="PROPOSED LLFB + horizontal flow (0.15-0.3 m/s)",
         d_mm=1.8, u_l=line_u(2.0, SUB_TUBE, 0.5), sub=SUB_TUBE, dp_dev=3.0, dp_pipe=2.0, eta=0.55,
         alpha=0.85, extra_kw=1.5, note="cross-flow bends/spreads the plume and shears bubbles off"),
    dict(key="llfb_best", name="PROPOSED LLFB + flow + high-eff. blower",
         d_mm=1.8, u_l=line_u(2.0, SUB_TUBE, 0.5), sub=SUB_TUBE, dp_dev=3.0, dp_pipe=2.0, eta=0.72,
         alpha=0.85, extra_kw=1.5, note="turbo / screw / multistage centrifugal at ~19 kPa"),
]

PADDLEWHEEL = dict(name="Paddlewheel, good commercial (Boyd 1998 tests)", sae_std=2.0, alpha=0.95,
                   note="Boyd 1998: 1.1-3.0, mean 2.13 kg/kWh; typical Asian units 1.2-1.8")

OXYGEN = [
    dict(name="Oxygen: VPSA + low-head contactor", gen=0.30, absorb=0.90, dissolve=0.35,
         note="farm-scale VPSA (>=10 t O2/d class); C* ~25 mg/L so DO 4 barely matters"),
    dict(name="Oxygen: small PSA + cone", gen=0.85, absorb=0.85, dissolve=0.45,
         note="skid PSA with compressor, per-pond scale"),
]


def evaluate(s):
    if s["dp_dev"] is None:
        from_spd = 26.3868                     # spd_design_params.derived()["dp_total_kpa"]
        dp_total = from_spd
    else:
        dp_total = hydro_kpa(s["sub"]) + s["dp_dev"] + s["dp_pipe"]
    sote = sote_standard(s["d_mm"], s["sub"], s["u_l"])
    e = blower_kwh_per_nm3(dp_total, s["eta"], BLOWER_INLET_T)
    sae = sote * KG_O2_PER_NM3_AIR / e
    ff = field_factor(FIELD_T, FIELD_S, FIELD_DO, s["alpha"], s["sub"])
    air = NIGHT_DEMAND_KG_H / ff / sote / KG_O2_PER_NM3_AIR       # Nm3/h
    kw_blower = air * e
    kw = kw_blower + s["extra_kw"]
    sae_std_sys = NIGHT_DEMAND_KG_H / ff / kw
    return dict(dp_total=dp_total, sote=sote, e=e, sae=sae, sae_sys=sae_std_sys,
                field=NIGHT_DEMAND_KG_H / kw, air=air, kw=kw, hydro_share=hydro_kpa(s["sub"]) / dp_total)


def main():
    rows = []
    pw_ff = field_factor(FIELD_T, FIELD_S, FIELD_DO, PADDLEWHEEL["alpha"], 0.0)
    pw_field = PADDLEWHEEL["sae_std"] * pw_ff
    rows.append((PADDLEWHEEL["name"], "-", "-", "-", "-", PADDLEWHEEL["sae_std"], pw_field,
                 NIGHT_DEMAND_KG_H / pw_field))
    for s in SCENARIOS:
        r = evaluate(s)
        rows.append((s["name"], f"{r['dp_total']:.1f}", f"{100 * r['hydro_share']:.0f}%",
                     f"{100 * r['sote']:.1f}%", f"{s['u_l']:.2f}", r["sae_sys"], r["field"], r["kw"]))
    for o in OXYGEN:
        f = oxygen_route_field_kg_per_kwh(o["gen"], o["absorb"], o["dissolve"])
        rows.append((o["name"], "-", "-", "-", "-", float("nan"), f, NIGHT_DEMAND_KG_H / f))

    print(f"Site: pond {POND_DEPTH} m, field point {FIELD_T:.0f} degC / {FIELD_S:.0f} ppt / DO {FIELD_DO} mg/L, "
          f"night demand {NIGHT_DEMAND_KG_H} kg O2/h per ha\n")
    print("| Architecture | dp total kPa | useful (hydrostatic) share | SOTE std | plume u m/s "
          "| SAE std kg/kWh | field kg/kWh | kW per ha at night peak |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|")
    for name, dp, share, sote, u, sae, fld, kw in rows:
        sae_s = "-" if sae != sae else f"{sae:.2f}"
        print(f"| {name} | {dp} | {share} | {sote} | {u} | {sae_s} | {fld:.2f} | {kw:.0f} |")

    print("\nNotes:")
    print(f"- {PADDLEWHEEL['note']}")
    for s in SCENARIOS:
        print(f"- {s['name']}: {s['note']}")
    for o in OXYGEN:
        print(f"- {o['name']}: {o['note']}")
    print("- SAE std for diffused air includes circulation-mixer power (extra_kw) where listed.")
    print("- Coarse-bubble rows (aerotube, SPD likely) may be pessimistic by up to 2x: the single-size")
    print("  discrete-bubble model omits formation-zone transfer and wobbling of large bubbles.")

    print("\nSensitivity — SOTE std (%) at 1.35 m vs bubble diameter and plume upflow:")
    us = (0.0, 0.1, 0.2, 0.3, 0.5, 0.8)
    print("| d mm | " + " | ".join(f"u={u}" for u in us) + " |")
    print("|---|" + "---:|" * len(us))
    for d in (0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0):
        print(f"| {d} | " + " | ".join(f"{100 * sote_standard(d, 1.35, u):.1f}" for u in us) + " |")

    print("\nSensitivity — blower kWh per 1000 Nm3 vs total pressure and wire-to-air efficiency:")
    etas = (0.45, 0.55, 0.65, 0.75)
    print("| dp kPa | " + " | ".join(f"eta={e}" for e in etas) + " |")
    print("|---|" + "---:|" * len(etas))
    for dp in (16, 18, 20, 25, 30, 35, 42):
        print(f"| {dp} | " + " | ".join(f"{1000 * blower_kwh_per_nm3(dp, e):.1f}" for e in etas) + " |")

    print("\nField factor (OTR_field / SOTR) vs night DO, 33 degC / 42 ppt:")
    print("| DO mg/L | surface aerator (alpha .95) | diffuser 1.35 m (alpha .85) |")
    print("|---:|---:|---:|")
    for do in (2.0, 3.0, 3.5, 4.0, 4.5, 5.0):
        print(f"| {do} | {field_factor(FIELD_T, FIELD_S, do, 0.95):.3f} | "
              f"{field_factor(FIELD_T, FIELD_S, do, 0.85, SUB_TUBE):.3f} |")


if __name__ == "__main__":
    main()
