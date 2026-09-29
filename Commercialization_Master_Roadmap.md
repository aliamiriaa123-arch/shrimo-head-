# Master Engineering & Commercialization Roadmap
## Submerged Pulsed‑Air Microbubble Diffuser Retrofit — Concept → Certified Mass Production → Commercial Deployment

---

## Phase 0 — Architecture Corrections Before Any CFD Money Is Spent

Three items in the current schematic conflict with the physics established in the previous review. Resolving them now changes the CFD scope, the BOM, and the claims — so they come first.

| Schematic element | Problem | Correction |
|---|---|---|
| **Eductor + "shear zone" producing 50–300 µm** | A 15 m³/h air jet at ~100–130 m/s carries ≈0.7 N momentum flux. Induced water velocity in a submerged mixing throat is 1–3 m/s, ε ≈ 10¹–10² W/kg → Hinze limit ≈ 1–2 mm. Air‑motive cross‑flow does not make sub‑300 µm bubbles. | Keep the eductor **only** as a plume‑momentum/circulation feature (or delete it — it costs 5–8 kPa you do not have). Add an explicit **bubble‑forming element** (rigid micro‑slit/micro‑orifice plate 150–300 µm, or 40–60 µm sintered HDPE tubes) downstream of the oscillator. The oscillator's job is pulsed detachment at that element. |
| **Bubble size claim** | 50–300 µm is not reachable at $45/unit and 15 m³/h/unit without a liquid pump. | Design target: **Sauter mean 0.5–1.0 mm in 40 ppt seawater, clean; ≤1.3 mm fouled.** Note that this target is *already sufficient* for your stated SOTE of 7.5–8.5% at 1.2–1.5 m — the SOTE target is realistic, the µm claim is not. |
| **Air flux per module** | 15 m³/h through a compact molded module implies element flux ≫10 m³/h·m², which produces coalesced 2–3 mm bubbles regardless of upstream cleverness. | Either (a) 0.4–0.6 m² of element area per module (4 × 300 mm sintered HDPE tubes or a 0.5 m² molded micro‑slit plate), or (b) 160 modules at 7.5 m³/h. Decide in Phase 1 on cost; (a) is preferred for manifold cost. |

**Pressure budget (must close on paper before CFD):**

| Item | kPa |
|---|---|
| Blower discharge (design, not nameplate max) | 42 |
| Main ring + laterals (Phase 4 sizing) | −3 |
| Choke orifice | −4 |
| Duckbill (open, at design flow) | −1 |
| Oscillator (nozzle + feedback) | −6 to −9 |
| Bubble‑forming element, clean | −8 to −12 |
| Hydrostatic at element, 1.5 m pond, element 0.3 m above bottom | −12 |
| **Residual for fouling / depth variation** | **+1 to +8** |

The residual is thin. Fouling allowance must be created by *fixing the blower operating point at 45 kPa* and by choosing the element at the low‑ΔP end (≥40 µm sintered or ≥200 µm slits). This is the single most important number in the project: **if the element + oscillator exceed ~18 kPa clean, the design cannot survive mid‑season fouling on a 45 kPa blower.**

Corrected performance baseline (1,200 m³/h × 0.30 kg O₂/m³ = 360 kg O₂/h in air):

| | Aerotube baseline | Target |
|---|---|---|
| SOTE at 1.35 m mean depth | 3 % | 7.5–8.5 % |
| SOTR | 10.8 kg/h | 27–31 kg/h |
| SAE (22 kW at shaft+motor) | 0.49 kg/kWh | 1.2–1.4 kg/kWh |
| Field OTR at DO 4.0, C* 5.5 mg/L, 34 °C, α 0.85 | ~2.2 kg/h | ~5.5–6.5 kg/h |

Biomass "unlock" from 10–12 to 24–30 t/ha is proportionally consistent with a 2.5× OTR gain only if oxygen is the sole limiting factor; in practice water‑exchange, TAN/NO₂ and sludge management co‑limit. State 18–24 t/ha until Phase 4 proves otherwise.

---

## Phase 1 — CFD & Numerical Optimization (Months 1–4)

### 1.1 Decompose the problem; do not run one giant multiphase model

| Sub‑problem | Physics | Solver / model | Mesh & time step |
|---|---|---|---|
| **A. Oscillator core** (single‑phase compressible air) | Coandă attachment, feedback‑loop switching, 50–200 Hz | OpenFOAM `rhoPimpleFoam` or Fluent pressure‑based coupled, **transient**, k‑ω SST (URANS) for screening → LES (WALE) on final 3 candidates. Ideal gas, isothermal walls. | 2D‑extruded quasi‑3D (5–10 cells in depth) for screening; full 3D for finals. y⁺ < 1 on Coandă walls, ≥15 cells across nozzle throat. Δt ≤ 1/(200 f) → **5–10 µs**; CFL < 1. Run ≥50 cycles, discard first 20. |
| **B. Element + detachment** (pulsed air through a slit/pore in seawater) | Bubble formation under oscillating supply pressure | Fluent VOF with CSF surface tension, or OpenFOAM `interFoam`/`compressibleInterFoam`; single slit/pore periodic cell; inlet = pressure signal exported from A. σ = 0.0735 N/m, ρ_w = 1,027, μ_w = 0.78 mPa·s (34 °C, 40 ppt), θ from measured wetted element. | Cell size ≤ d_slit/20; adaptive refinement at interface. 2D‑axisymmetric for pores, 3D for slits. |
| **C. Near‑field plume & entrainment** (0.5 m around module) | Bubbly plume, entrainment, bottom shear | Eulerian‑Eulerian (Fluent Multi‑Fluid VOF or OpenFOAM `multiphaseEulerFoam`) with **PBM**: Luo–Svendsen breakup, Prince–Blanch coalescence **with coalescence efficiency reduced by a seawater factor** (calibrate against Phase 2 data — default freshwater kernels over‑predict coalescence by 2–3× at 0.6 M). Drag: Tomiyama (contaminated); lift: Tomiyama with sign change at Eö ≈ 4; turbulent dispersion: Burns. Inlet BSD from B. | 5–8 M cells, quadrature/CQMOM with 6–8 nodes or discrete method 12 bins. |
| **D. Pond‑scale hydraulics** (1 ha, 80 sources) | Circulation, DO field, sludge transport | Drift‑flux / mixture model or simplified Eulerian with fixed BSD from C; couple to a DO source term using K_La per unit from Phase 2; k‑ε; bed shear output. | 2–4 M cells, steady‑periodic. Used only for layout in Phase 4. |

Do **not** attempt to resolve nanometre or micron bubbles; the model must be told the truth that the element makes 0.5–1 mm.

### 1.2 Oscillator parametric study

Frequency of a feedback‑type oscillator is set by loop transit time plus switching time:

f ≈ 1 / [2 (τ_fb + τ_sw)], τ_fb ≈ L_fb / c_eff, τ_sw ≈ (3–5) w_n / U_j

At 8 kPa across the nozzle, U_j ≈ 100–110 m/s. For 100 Hz, the total half‑period is 5 ms; with τ_sw ≈ 0.2–0.4 ms, the loop must supply ~4.6 ms. If pressure‑wave dominated (c ≈ 340 m/s), that is a **1.5 m** loop — not moldable in a $45 module. If designed convectively dominated (loop cross‑section comparable to nozzle, so the loop carries a real flow at ~50–100 m/s), 0.25–0.45 m serpentine loops give 50–150 Hz. **Design decision embedded in the study: convective‑dominated compact loops, or a jet‑interaction (feedback‑free) oscillator (Tesař type), which is intrinsically compact but less frequency‑stable.**

Design‑of‑experiments variables (Latin hypercube, 40–60 runs URANS):

| Variable | Range | Note |
|---|---|---|
| Nozzle width w_n | 2–5 mm | Sets U_j for the pressure budget |
| Nozzle aspect ratio (depth/width) | 3–6 | ≥3 to keep 2D behavior |
| Coandă wall radius R/w_n | 6–15 | Controls attachment robustness vs. back‑pressure |
| Wall setback / offset s/w_n | 0.5–1.5 | Bistability margin |
| Splitter distance x_s/w_n | 6–12 | |
| Feedback loop length L_fb | 150–500 mm | Frequency |
| Feedback loop area A_fb/A_n | 0.3–1.0 | Convective vs acoustic regime |
| Outlet back‑pressure asymmetry | 0–4 kPa | **Critical**: element fouling on one bank must not lock the jet to one side |

Responses: frequency, duty‑cycle symmetry (target 50 ± 5%), pressure recovery (ΔP total ≤ 9 kPa at 15 m³/h), pulse amplitude at each outlet (target ≥60% modulation depth at the element face), Strouhal number St = f·w_n/U_j (expect 0.005–0.03 for feedback types; use it for scaling between prototypes, not as a target).

Also simulate with **inlet temperature 60 °C and 40 °C** (blower air after a 100 m buried line) and with **10% humidity condensation film** on Coandă walls — Coandă attachment is sensitive to wall wetting.

### 1.3 Entrainment vs. benthic pressure

If the eductor is retained, sweep hydrostatic back‑pressure 10–18 kPa (1.0–1.8 m pond) and report water entrainment ratio (m_w/m_a) and exit plume velocity. Expect entrainment ratio 5–20 by mass, exit velocity 1–3 m/s, decaying below 0.3 m/s within ~0.5 m. This sub‑study also gives the **bed shear stress map** required in Phase 4: target τ_bed < 0.1 Pa beyond 0.5 m from the module (critical shear for unconsolidated organic sludge ≈ 0.05–0.15 Pa).

### 1.4 Deliverables & gate

- Three frozen oscillator geometries (differing in frequency 60/100/160 Hz) with predicted ΔP, frequency, symmetry, and robustness to ±3 kPa outlet asymmetry.
- Predicted element‑face pulse waveform → input to Phase 2.
- Verification: mesh‑independence (3 levels, GCI < 5% on frequency), time‑step independence, comparison against a published Sheffield/Tesař oscillator case for solver credibility.
- **Gate 1:** ΔP_oscillator ≤ 9 kPa at 15 m³/h AND symmetric bistable operation with 3 kPa outlet asymmetry. Fail → change to jet‑interaction oscillator or reduce per‑module flow.

Budget: 1 CFD engineer 4 months, 64‑core workstation or cloud (~$6–10k compute), Fluent licence or OpenFOAM: **$35–55k.**

---

## Phase 2 — Bench Prototyping & Optical Validation (Months 2–7)

### 2.1 Prototyping methods

| Method | Use | Caveats |
|---|---|---|
| **CNC‑machined cast PMMA (acrylic), 2‑plate sandwich** | Oscillator core for optical & pressure diagnostics | Preferred. Ra < 1.6 µm on Coandă walls; O‑ring or solvent‑bonded; tolerance ±0.05 mm on nozzle. Max air temp 60 °C. |
| **SLA, clear resin (Formlabs Clear/Rigid 4000, DSM WaterShed XC)** | Rapid geometry iterations | Post‑cure fully (uncured resin leaches, affects surface tension), coat channels with thin epoxy to seal micro‑porosity; surface roughness Ra 3–8 µm alters attachment — validate one SLA vs one CNC part before trusting SLA for frequency. |
| **SLS PA12** | Housings, brackets only | Absorbs 1–3% water, porous — never for pneumatic channels or pressure references. |
| **MJF PA12 / PP** | Near‑production check of snap‑fits | OK for form/fit, not for flow. |
| **Element** | Buy: sintered HDPE tubes 40/60/100 µm (Porex/GenPore or Chinese equivalents), molded EPDM slit membranes, and laser‑drilled PP plates 150/250/350 µm | Measure bubble point and wet ΔP of each before use. |

### 2.2 Flume & instrumentation

- **Column/flume:** 1.8 m deep × 0.8 × 0.8 m clear‑walled tank (optical windows on two adjacent faces), filled with artificial seawater (Instant Ocean or NaCl/MgSO₄/CaCl₂ recipe to 40 ppt), heated to 34 ± 0.5 °C. Second identical run in tap water at 20 °C for standard reporting.
- **Air supply:** small Roots blower or regulated compressed air with 0–60 kPa precision regulator, thermal mass flow meter (±1%), inlet temperature control (40/60 °C).
- **Pressure:** piezoresistive transducers (0–100 kPa, ≥5 kHz bandwidth) at module inlet, both outlets, and element face; FFT for frequency and modulation depth.
- **Hydrophone** in the tank for oscillation frequency confirmation without intrusion.
- **Bubble size distribution — shadowgraphy:** high‑speed camera (≥5,000 fps at 1 MP; e.g., Phantom VEO/Photron Mini or Chronos 2.1 on a budget), telecentric lens (0.5×–1×, field 10–20 mm, DOF 1–2 mm), pulsed LED backlight (≤10 µs). Measurement planes at 0.1, 0.5, 1.0 m above element and 0–0.3 m radial. ≥2,000 bubbles per condition; automated detection (Hough/watershed in ImageJ or Python‑OpenCV), report d₁₀, d₃₂ (Sauter), d₉₀, and void fraction. Calibrate with a reticle.
- **PDPA/PDA:** only meaningful for near‑spherical bubbles <1 mm at void fraction <2%; use in the far‑field (1 m up) as a cross‑check, not as the primary method. Laser diffraction (Malvern) is not suitable at these sizes/void fractions.
- **Element‑face imaging:** macro lens on the slit/pore to confirm pulsed detachment (bubble departs at supply‑pressure minimum, not at buoyancy size).

Test matrix: 3 oscillator geometries × 4 elements × 3 flows (10/15/20 m³/h) × 2 waters × 2 back‑pressures. ~150 conditions; 6–8 weeks.

### 2.3 SOTR / SOTE protocol (ASCE 2‑06 with saline adaptation)

Standard: ASCE/EWRI 2‑06 clean‑water test, non‑steady‑state re‑aeration.

- **Tank:** ≥3 m³ and ≥1.5 m depth (use a 2 × 2 × 1.8 m tank; report submergence). Modules at production spacing where possible.
- **Deoxygenation:** sodium sulfite, 7.88 mg/L per mg/L DO ×1.2–1.5 excess; cobalt chloride 0.1–0.5 mg/L Co²⁺. In seawater at 34 °C, cobalt can precipitate as hydroxide/carbonate at pH > 8.2 — pre‑acidify to pH 7.8–8.0 or use higher Co dose and verify no residual sulfite (test strips) before data acceptance. Alternative for saline series: **nitrogen stripping** to <0.5 mg/L, no chemicals, no cumulative sulfate/TDS drift.
- **Probes:** ≥4 optical DO probes at 3 depths and 2 radii, 1 Hz logging.
- **Fit:** non‑linear least squares of C(t) = C*∞ − (C*∞ − C₀)·exp(−K_La·t) with C*∞ as a **fitted** parameter; truncate data below 20% and above 98% of C*∞. Do not use tabulated C* for seawater — measure.
- **Corrections:** K_La₂₀ = K_La_T · 1.024^(20−T); barometric correction of C*∞. Report SOTR₂₀, SOTE, SAE (blower power from wire‑to‑air measurement or from manufacturer curve at the measured discharge pressure).
- **Report both:** (i) 20 °C tap water (comparable with any datasheet), (ii) 34 °C / 40 ppt (what the farmer gets), plus the ratio. Expect the saline SOTE to be 20–40% higher due to smaller bubbles.
- **Off‑gas method (ASCE 18‑18)** in parallel: capture rising gas under a hood, measure O₂ mole fraction (paramagnetic or zirconia analyzer); this gives SOTE directly in a single run and is what you will use in the pond later.
- Acceptance repeatability: 3 runs per condition, CV < 5%.

**Gate 2:** d₃₂ ≤ 1.0 mm (clean, 40 ppt), SOTE at 1.5 m ≥ 9% (clean, saline), module ΔP ≤ 20 kPa total. Fail → revise element (smaller flux per module) before proceeding.

Budget: prototypes $15k, camera rental/purchase $15–40k, tank/instrumentation $25k, labor: **$80–110k.**

---

## Phase 3 — Durability, Fouling & Materials (Months 4–10, overlaps Phase 2)

### 3.1 Material selection

| Component | Selected | Rejected & why |
|---|---|---|
| Housing, manifold fittings | **PP block copolymer, black, ≥2% carbon black, food‑contact grade** (or HDPE PE100 for extruded parts) | PA6/PA66: 2–3% water uptake, modulus loss; POM: hydrolysis in warm water, sensitive to chlorine used in pond disinfection; ABS: UV, ESC in sunscreen/diesel contaminants |
| Oscillator core (dimensional precision, hotter air) | **PP‑GF20 (glass‑filled) for stiffness**, or **PVDF** if inlet air >70 °C is unavoidable | PVC‑C acceptable for machined pilot; unsuitable for molding cost; PC: ESC in seawater + hydrolysis at >60 °C |
| Bubble‑forming element | Sintered HDPE (UHMW blend) 40–60 µm, or molded PP micro‑slit plate | Sintered 316L: galvanic, cost; ceramic alumina: fine technically, brittle in farm handling, 3× cost |
| Duckbill check valve | **EPDM 50–60 Shore A, peroxide‑cured** (H₂S, ozone, seawater, 100 °C resistant); silicone as alternative if inlet air exceeds 90 °C | NBR: poor H₂S/ozone/UV; natural rubber: no |
| Choke orifice | Molded PP insert, or laser‑cut PP/PVDF disc; **not** metal | Brass/stainless in H₂S sludge zone |
| Ballast | Concrete encapsulated in PP shell, or HDPE‑jacketed steel | Bare concrete raises local pH; bare steel is an anode for everything |
| Fasteners/clamps | None if possible (snap‑fit + weld); otherwise A4‑80 or PP | |

Verify PP grade for **environmental stress cracking** in the presence of feed oils, formalin, and the farm's disinfectants (BCDMH, chlorine): ASTM D1693 Bell test at 50 °C, 1,000 h, in pond‑water + 200 mg/L active chlorine.

Air temperature: Roots discharge at 45 °C ambient and 45 kPa is 95–115 °C. Specify **minimum 30 m of buried HDPE main before the first PP module, or an air cooler**; measure the inlet temperature at the furthest and nearest module in Phase 4. PP creep at 70 °C under 45 kPa is acceptable; at 100 °C it is not.

### 3.2 Antifouling strategy

Constraints: shrimp are copper‑sensitive (Cu²⁺ LC₅₀ for *L. vannamei* juveniles is low tens of µg/L); any biocidal release is prohibited on food‑safety and toxicity grounds. Therefore:

1. **Hydraulics first:** pulsed flow at the element face (the oscillator itself), exit velocity ≥1 m/s at slits, no horizontal upward‑facing stagnant surfaces, self‑draining geometry, gas‑side positive pressure at all times when running.
2. **Fouling‑release, not biocidal:** PDMS‑based fouling‑release coating on external housing (used on aquaculture nets); apply to the element only if it does not alter contact angle/bubble point — likely it does, so keep the element uncoated and rely on 1 and 3.
3. **Anti‑wetting on shutdown:** duckbill + an **inverted air‑bell** in the housing so the element stays gas‑side dry for ≥24 h without blower pressure (trap volume ≥ element pore volume × 20). This is a patent‑worthy feature and the primary defense against internal biofouling.
4. **Operational:** daily 60 s "bump" at max blower speed (Phase 6), 5% formic or 3% HCl dip between crops (element only, 30 min), lift‑out handle for a diver‑free inspection from the dike with a pole.

### 3.3 Accelerated testing

| Test | Protocol | Acceptance |
|---|---|---|
| Duckbill fatigue | Hydraulic rig: 0 → 20 kPa forward → 0 → 15 kPa reverse (water), 1 cycle/min, **10,000 cycles** (not 1,000: 3 seasons × ~10 stops/day incl. power cuts), at 40 °C in 40 ppt water with 5 mg/L sulfide | Reverse leak < 1 mL/min at 15 kPa; cracking pressure 1–3 kPa unchanged ±30% |
| Duckbill chemical aging | 1,000 h at 70 °C in seawater + 10 mg/L H₂S; 500 h UV (ISO 4892‑2) | Hardness change < ±8 Shore A, tensile retention > 70% |
| Element fouling (lab) | Live pond water recirculated at 34 °C with 1 g/L feed added daily; static vs pulsed; 8 weeks | Wet ΔP rise ≤ +30%, d₃₂ ≤ 1.3 mm at week 8 |
| Element scaling | Synthetic seawater at Ω_arag = 4 (mimics CO₂‑stripped microlayer), 4 weeks | ΔP rise ≤ +20%; acid dip restores ≥95% |
| Housing/element thermal creep | 45 kPa internal at 80 °C air, 500 h | Nozzle dimensional change < 0.05 mm |
| Field coupon rack | 6 racks with all materials in a live pond from Month 5 | Visual/mass fouling scoring, coating adhesion |

**Gate 3:** all acceptance criteria met; material set frozen for tooling.

Budget: rigs $20k, lab time and coupons $20k, external labs (aging, ESC) $15k: **$50–60k.**

---

## Phase 4 — Full‑Scale 1 ha Commercial Pond Pilot (Months 7–15, one full crop cycle plus preparation)

### 4.1 Layout & manifold sizing

Air state at 45 kPa gauge, 60 °C after cooling: ρ ≈ 1.45 kg/m³; actual volumetric flow ≈ 1,200 × (101/146) × (333/293) ≈ 940 m³/h ≈ 0.26 m³/s.

Design rule: main ring ≤ 12 m/s, laterals ≤ 10 m/s, total distribution loss ≤ 3 kPa.

| Segment | Flow | Pipe | Velocity | Length | ΔP (Darcy, ε = 0.01 mm HDPE) |
|---|---|---|---|---|---|
| Blower to ring feed | 0.26 m³/s | DN200 PE100 SDR17 (ID 176 mm) | 10.7 m/s | 30 m | 0.6 kPa |
| Main ring (two‑way split, worst half) | 0.13 m³/s | DN160 SDR17 (ID 141 mm) | 8.3 m/s | 200 m (perimeter 400 m) | 1.1 kPa |
| Laterals (5 modules each, 16 laterals) | 75 m³/h actual ≈ 0.016 m³/s | DN63 SDR11 (ID 51 mm) | 8.0 m/s | ≤50 m | 0.8–1.2 kPa |
| Module drop | 15 m³/h | DN32 | 6 m/s | 2 m | 0.1 kPa |

Total ≈ 2.5–3.0 kPa. Choke orifice at 4 kPa yields a flow imbalance of ±(ΔP_var/2·ΔP_choke) ≈ ±(1.5/8) ≈ **±19% worst case** across the grid from manifold loss alone, plus ±1 kPa from ±10 cm depth variation. If the pond bottom is not level within ±10 cm, raise the choke to 5–6 kPa or accept it — but the pressure budget punishes you. Better: **two‑tier choking** — 2 kPa at each lateral takeoff (16 orifices) plus 3 kPa at each module. Include an air‑release/purge valve at the far end of each lateral and a condensate drain at the ring low point.

Placement (1 ha square, 100 × 100 m, typical circular flow driven by 4–8 paddlewheels retained for circulation):

- Modules on a ring pattern at 8–12 m and 25–30 m from the dike toe (two concentric loops), spacing ~10 m, none inside a 20 m radius of the central drain (sludge accumulation zone).
- Element 0.30–0.35 m above liner, plume exit horizontal to +30° upward, oriented with the circulation direction to add momentum, never downward.
- Keep 4 paddlewheels (or 2 + airlift circulators) for horizontal flow and sludge conveyance; the diffusers do not do this job.

### 4.2 Benthic verification

- Pre‑pilot: install one module in a lined test pond over a 5 cm laid bed of pond sludge; ADV (acoustic Doppler velocimeter) traverses at 5 cm above bed, 0.25–2 m radial; turbidity sensors; accept if near‑bed velocity < 0.15 m/s beyond 0.5 m and no visible plume of resuspended solids on video after 24 h.
- During the crop: monthly sludge‑depth mapping (graduated pole grid, 10 m spacing), H₂S in porewater at 5 stations, redox at 1 cm depth, TSS at 30 cm above bottom versus control.

### 4.3 Biological trial design

One treatment pond vs one control pond is pseudoreplication and will not convince a bank or a distributor. Minimum: **2 treatment + 2 control** (1 ha each, or 4 × 0.5 ha), same hatchery PL batch, same stocking density (target 200 PL/m²), same feed and protocol, same blower size per pond, same paddlewheel complement. Ideally 3 + 3.

| Metric | Method | Frequency |
|---|---|---|
| DO profile | 2 wiped optical probes per pond at 30 cm above bottom + weekly manual transect of 12 points at 3 depths at 05:00 | Continuous / weekly |
| DO deficit statistics | Hours per night below 4.0 and 3.0 mg/L | Continuous |
| Blower discharge pressure & kWh | Transducer, energy meter | Continuous |
| Field OTR | Off‑gas hood over 3 modules (ASCE 18‑18) | Weeks 2, 6, 10, 14 |
| Element fouling | Pull 3 sacrificial modules at weeks 4/8/12; bench ΔP and d₃₂ | |
| pH, alkalinity, CO₂ | 06:00 & 15:00 | Daily |
| TAN, NO₂‑N, NO₃‑N, TSS, chl‑a | Lab | 2×/week |
| TGP | Saturometer | Weekly (guard against >110%) |
| Growth | Cast‑net sampling 100 shrimp | Weekly |
| Survival, FCR, yield, size CV, kWh/kg | Harvest | End |
| Economics | $/kg operating, capex/kg | End |

Success criteria for **Gate 4** (per‑pond means, treatment vs control): night‑time hours below 4.0 mg/L reduced ≥50%; yield ≥ +40% at equal or better FCR and survival ≥ control − 3 points; element ΔP rise ≤ 40% at week 12; no sludge resuspension events; kWh/kg ≤ 60% of control.

Budget: 80 + spares modules (pilot builds, ~$150 each machined/printed), manifold $12k, instrumentation $25k, pond costs and compensation to host farm $40k, labor: **$120–150k.**

---

## Phase 5 — Industrial Tooling, DFM & Mass Production (Months 9–17)

### 5.1 DFM of the oscillator core

- Geometry is 2D‑extruded → split into **two half‑shells along the mid‑plane of the depth direction**, so all channels are open‑faced and molded in a single pull; **draft (0.5–1°) applies only in the depth direction**, which does not perturb Coandă wall profile. Nozzle width tolerance ±0.03 mm: specify hardened H13 inserts for the nozzle/Coandă region, polished SPI‑A2 in the channel, textured elsewhere.
- Joining: **ultrasonic welding with energy directors** (PP welds well; provides hermetic, tool‑free 8–12 s cycle) — *not* solvent welding (PP is solvent‑inert) and *not* adhesives. Alternative for service access: snap‑fit + EPDM face gasket, at the cost of a leak path. Recommend welded core in a snap‑fit housing so the core is a sealed, non‑serviceable cartridge and the element is field‑replaceable.
- Feedback loops molded as serpentines in the same half‑shells; avoid cores/slides.
- Element interface: bayonet or 4‑lug quarter‑turn with O‑ring; tool‑free.
- Duckbill: purchased molded EPDM part (commodity, $0.8–1.5) retained by a snap collar.
- Choke: molded orifice insert in three sizes (colour‑coded) to allow depth compensation.
- Wall thickness 2.5–3.0 mm uniform; ribs ≤60% wall; gate at thick section; simulate with Moldflow for warp (glass‑filled PP warps — validate flatness of the mating face < 0.1 mm).

### 5.2 Tooling capex & BOM (1,000 units/batch, China or Turkey tool shop)

| Tool | Cavities | Steel | Cost |
|---|---|---|---|
| Oscillator half‑shells (family tool, L+R) | 2+2 | H13 inserts, P20 base | $38–55k |
| Housing / air‑bell | 2 | P20 | $30–45k |
| Element carrier/manifold plate | 2 | P20 | $18–25k |
| Choke inserts (3 sizes) | 8 | P20 | $8–12k |
| Ballast shell | 1 | Al/P20 | $12–18k |
| Micro‑slit plate (if molded rather than sintered) | 1 | H13, EDM slits | $25–40k |
| Fixtures, welding horns | | | $10–15k |
| **Total** | | | **$140–210k** |

Unit BOM at 1,000 units:

| Item | $ |
|---|---|
| Oscillator core (PP‑GF20, 180 g, welded) | 3.2 |
| Housing + air‑bell (PP, 600 g) | 2.8 |
| Element: 4 × sintered HDPE tubes 300 mm 50 µm, or molded slit plate 0.45 m² | 14–18 |
| Duckbill EPDM | 1.2 |
| Choke insert, O‑rings | 0.9 |
| Element carrier plate | 1.6 |
| Ballast (12 kg encapsulated) | 4.5 |
| Hose barb, clamp, 2 m DN32 drop | 3.0 |
| Assembly & welding (6 min) | 2.5 |
| EOL test (1 min) | 0.6 |
| Packaging, fasteners, labels | 1.5 |
| Scrap/yield 3% | 1.1 |
| **Total** | **37–42** |

At 100‑unit pilot batches with soft tooling, expect $90–140. Manifold and blower controls are quoted separately per pond.

### 5.3 QC & end‑of‑line

- Incoming: element bubble‑point (ASTM F316) and wet ΔP on 5% sample; duckbill cracking pressure 100%.
- Molding SPC: nozzle width by optical comparator every 50 shots; CMM on first‑off per shift.
- **EOL pneumatic fixture:** clamp module, apply 45 kPa at 15 m³/h (mass flow controlled), record ΔP (accept 14–20 kPa), oscillation frequency via microphone FFT (accept design f ± 15%), outlet symmetry via two fast pressure sensors (duty 50 ± 8%), reverse leak at 15 kPa water (<1 mL/min). 60 s cycle; barcode + data record per serial.
- Sample audit: 1 per 200 to the water column for d₃₂.

**Gate 5:** first 200 production modules pass EOL with ≥97% yield and match pilot SOTE within 5%.

---

## Phase 6 — Embedded Systems, Automation & Telemetry (Months 5–16)

### 6.1 Sensor suite (per 1 ha pond)

| Sensor | Spec | Qty | Notes |
|---|---|---|---|
| Optical DO + temperature | Luminescent, **with mechanical wiper**, RS‑485 Modbus RTU, 0–20 mg/L, ±0.1, titanium/PVC body | 2 | Mount 30 cm above bottom at the downwind sludge margin and mid‑pond; not in a plume |
| ORP | Pt/Ag‑AgCl, gel reference | 1 (optional) | Low control value in 40 ppt (reference drift, biofilm); use only as trend/alarm for sulfide zone, never in the loop |
| pH | Optional | 1 | Useful for CO₂ management; drifts |
| Blower discharge pressure | 0–100 kPa gauge, ceramic diaphragm, 4–20 mA, 0.5% | 1 | Primary fouling & line‑break indicator |
| Far‑end ring pressure | Same | 1 | Distribution loss health |
| Differential across a reference choke | 0–10 kPa DP, 4–20 mA | 1 | Derives real air flow |
| Blower inlet/outlet temperature | PT100 | 2 | Over‑temperature, VSD derating |
| Motor current/power | From VFD Modbus | — | |
| Water level | Pressure or ultrasonic | 1 | Depth compensation of hydrostatic term |

### 6.2 Control architecture

Two‑layer, safety‑first:

- **Layer 1 (hard‑wired safety, no firmware dependency):** blower overpressure switch (55 kPa) → VFD external fault; VFD fault relay → alarm + automatic bypass contactor to DOL after 30 s if VFD unrecoverable (Roots at DOL is safe); hardware watchdog on the controller; loss‑of‑comms to VFD → VFD preset frequency 50 Hz (100%).
- **Layer 2 (controller):** industrial‑grade board around **STM32H7 or a DIN‑rail PLC (e.g., Siemens S7‑1200, Unitronics, or an industrial ESP32‑S3 module for telemetry only)**. Requirements: 2× isolated RS‑485 (sensors, VFD), 6× 4–20 mA in, 4× relay, RTC, SD logging, −20…+70 °C rating, conformal coating, IP66 enclosure with vent, 24 VDC with 4 h UPS. Isolate the telemetry radio (4G LTE Cat‑1 with fallback to GSM/SMS; NB‑IoT coverage is unreliable on most coasts) on a separate MCU so a modem hang cannot stall the control loop.

Control law (Roots blower is positive‑displacement: pressure is set by the system, flow ∝ speed, power ≈ ∝ flow):

1. Feed‑forward diurnal schedule (learned per pond over 7 days): night 22:00–07:00 = 100%; day ramps.
2. PI trim on the **minimum of the two DO probes** with setpoint 4.5 mg/L (day) / 4.0 (night, with 100% floor), anti‑windup, rate limit ±5%/min, output clamp **40–100% speed** (Roots minimum speed for lubrication/cooling and to maintain >25 kPa so duckbills and elements stay dry).
3. Do not chase daytime supersaturation: if DO > 8 mg/L hold at 40%, not 0% — the grid must remain pressurized.
4. Probe plausibility: |DO₁ − DO₂| > 1.5 mg/L for >15 min, or flat‑line, or wiper fault → **fail‑safe 100% + alarm**.
5. Purge/bump: 60 s at 100% every 24 h at 14:00 (low DO demand); after any stop >5 min, restart at 100% for 120 s.
6. Fouling index: discharge pressure at 100% speed vs commissioning baseline; +8 kPa → maintenance alarm; +12 kPa → mandatory acid‑dip work order.
7. Line break: far‑end pressure < 0.7 × expected → alarm; identify lateral by sequential valve test if motorized valves are fitted (optional tier).

Realistic energy saving: the night floor is 100%, day trims to 40–70% → **20–30% seasonal kWh reduction**, not 30–40%; state accordingly. On generator‑fed farms this is the dominant ROI item.

### 6.3 Telemetry & software

MQTT over TLS to a broker; 1 min telemetry, 1 s local buffer; dashboard with DO, pressure, speed, fouling index, alarms via SMS/WhatsApp; OTA firmware with A/B partitions and rollback; local HMI (7" panel) for offline operation. Data model: pond → devices → time series; export CSV for FCR analytics. Keep the cloud optional — the pond must run for weeks with no connectivity.

Budget: hardware development $40k, firmware $50k, cloud/dashboard $30k, EMC pre‑compliance $10k: **$120–140k.**

---

## Phase 7 — IP, Certification, Risk Register, Milestones

### 7.1 Patent strategy

Prior art is dense: Zimmerman/Tesař (University of Sheffield, Perlemax) hold or held families on fluidic‑oscillator‑driven microbubble generation (earliest priority ~2007–2009; check expiry and territorial coverage — several core claims are near or past 20 years, others live); Warren/Bowles/Stouffer on fluidic oscillator geometry; numerous duckbill and coarse‑bubble diffuser patents. Claims must be narrow, structural, and combinational:

1. **Integrated module claim:** a submerged aeration module comprising, in series within a single molded body, a calibrated choke, an elastomeric check valve, a bistable fluidic oscillator with two outlets each feeding a separate porous/slit element bank, and an inverted gas‑retaining bell enclosing the element gas side — characterized by [specific volume ratio of bell to element pore volume ≥ X] to prevent wet‑out on depressurization.
2. **Compact convective feedback loop:** serpentine feedback channels co‑molded in half‑shells with area ratio A_fb/A_n in [range] yielding f in [range] at ΔP ≤ 10 kPa (claim the ratio/regime, supported by Phase 1–2 data).
3. **Asymmetry‑tolerant oscillator:** Coandă wall/setback geometry maintaining bistability under ≥3 kPa outlet asymmetry (fouling tolerance), with the numerical range.
4. **Two‑tier passive balancing method** for submerged grids (lateral choke + module choke with stated ratio).
5. **Control method claim** (weaker, but useful): fouling index from pressure‑vs‑speed baseline triggering purge, combined with probe‑plausibility fail‑safe.

Route: national priority filing → PCT within 12 months → national phases in CN, IN, VN, TH, ID, EC, MX, US, EP (aquaculture markets). Design registration for the module. Keep oscillator tuning tables and mold surface specifications as trade secrets. Run a professional FTO search on Sheffield/Perlemax families before Phase 5 tooling.

### 7.2 Certification

| Item | Applicability |
|---|---|
| Diffuser module | No electrical parts → CE marking under LVD/EMC **not applicable**; Pressure Equipment Directive not applicable (<0.5 bar); Machinery Directive not applicable (no drive). **IP68 is meaningless for a non‑electrical submerged plastic part** — do not claim it; claim material and pressure test standards instead (ISO 1167 pipe pressure test methodology, ASTM D1693 ESC, EN ISO 4892‑2 UV). Food‑contact grade PP per EU 10/2011 / FDA 21 CFR 177.1520 as a marketing and safety assurance. |
| Controller & sensors | CE: EMC 2014/30/EU (EN 61326‑1), LVD 2014/35/EU (EN 61010‑1), RoHS 2011/65/EU, RED 2014/53/EU for the radio (or use a pre‑certified modem module); enclosure IP66 per EN 60529; UKCA if selling UK. |
| VFD retrofit | Use CE‑marked drive; installation per IEC 60364; line reactor and output filter. |
| Quality system | ISO 9001 at contract manufacturer; ISO 14001 optional. |
| Market‑specific | Some importers (EC, IN) request aquaculture‑input registration; ASC/BAP farm certifications value energy‑per‑kg data — publish it. |

### 7.3 Risk register

| # | Risk | Type | Sev (1–5) | Lik (1–5) | Mitigation |
|---|---|---|---|---|---|
| 1 | Pressure budget does not close on fouled elements → grid starves at mid‑season | Tech | 5 | 4 | Element ≥40 µm/≥200 µm slits; blower set to 45 kPa; fouling index & bump; Gate 2 hard limit ΔP ≤ 20 kPa |
| 2 | Oscillator locks to one side under fouled‑bank asymmetry | Tech | 4 | 3 | Phase 1 asymmetry design variable; EOL symmetry test |
| 3 | Bubble size in field > 1.3 mm → SOTE gain < 1.5× → ROI fails | Tech/Comm | 5 | 3 | Gate 2 & 4 criteria; fallback product = pulsed EPDM discs |
| 4 | Sludge resuspension / anoxic release near modules | Bio | 5 | 2 | Height 0.3 m, exit ≥ horizontal, central exclusion zone, ADV verification |
| 5 | CO₂ accumulation / pH drop from reduced stripping | Bio | 3 | 3 | Retain paddlewheels; pH/alkalinity monitoring; liming protocol |
| 6 | TGP > 110% in 1.0–1.2 m ponds | Bio | 3 | 2 | Saturometer in pilot; daytime speed floor logic |
| 7 | Hot blower air deforms PP near blower | Tech | 4 | 3 | 30 m buried run or after‑cooler; PVDF core option |
| 8 | Wet‑out during long power cuts → internal biofouling | Ops | 4 | 4 | Duckbill + air bell; restart purge |
| 9 | Farmers skip acid dip / cleaning | Ops | 4 | 4 | Fouling index alarms; service contract; lift‑out design |
| 10 | Roots blower VSD at low speed overheats/loses lubrication | Tech | 3 | 3 | 40% floor; temperature monitoring; blower OEM sign‑off |
| 11 | DO probe drift → wrong control | Ops | 4 | 3 | Wipers, dual probes, plausibility → 100% |
| 12 | Tooling before design freeze → $150k rework | Comm | 5 | 3 | Gates 2–4 mandatory before Phase 5 PO |
| 13 | IP blocked by Sheffield/Perlemax live claims | Comm | 4 | 2 | FTO before Phase 5; design‑around (jet‑interaction oscillator) |
| 14 | Pseudoreplicated pilot unconvincing | Comm | 3 | 4 | ≥2+2 ponds; third‑party (university) data collection |
| 15 | Price resistance vs $0.5–1.5/m³h aerotubes | Comm | 4 | 4 | Sell per‑pond package with blower VSD; lead with t/ha per kW and kWh/kg; leasing/pay‑per‑crop |
| 16 | Element supply single‑sourced | Ops | 3 | 3 | Qualify 2 sintered‑HDPE vendors + molded slit plate |

### 7.4 18‑Month Milestones & Budget Gates

| Month | Milestone | Cumulative spend | Gate |
|---|---|---|---|
| 0–1 | Phase 0 design correction; pressure budget signed; FTO preliminary | $25k | G0: budget closes on paper |
| 1–4 | Phase 1 CFD; 3 frozen oscillator geometries | $80k | **G1**: ΔP ≤ 9 kPa, symmetric under 3 kPa asymmetry |
| 2–7 | Phase 2 prototypes, shadowgraphy, ASCE SOTR (fresh + saline) | $190k | **G2**: d₃₂ ≤ 1.0 mm, SOTE ≥ 9%, module ΔP ≤ 20 kPa |
| 4–10 | Phase 3 materials, duckbill 10k cycles, fouling/scaling rigs, coupons | $250k | **G3**: material set frozen |
| 5–9 | Phase 6a controller & VSD retrofit prototype; firmware v0.x | $300k | Bench HIL passes |
| 7–9 | Pilot module build (100 units soft‑tooled/machined), manifold install, ADV benthic test | $360k | Benthic acceptance |
| 9–13 | Phase 4 crop cycle (stock M9, harvest M12–13), 2+2 ponds; Phase 6b field firmware | $470k | **G4**: yield ≥ +40%, ΔP rise ≤ 40%, kWh/kg ≤ 60% |
| 10–12 | Priority patent filing; FTO final; DFM freeze; tool RFQs | $500k | Board approval for tooling |
| 12–16 | Phase 5 tooling ($140–210k), T1–T3 samples, EOL fixture, EMC/CE on controller | $720k | **G5**: 200 units ≥97% yield, SOTE within 5% of pilot |
| 15–17 | First commercial batch 1,000 modules (12 pond packages), 2nd‑season pilots at 3 customer farms, service protocol & training | $800k (incl. inventory, part‑recoverable) | First revenue |
| 17–18 | PCT filing; V2 backlog (motorized lateral valves, integrated pond controller); second‑crop data | | Commercial gate: 3 paying farms renewing |

Total cash need to first revenue: **~$750–850k**, of which ~$180k is tooling and ~$80k is recoverable inventory. Headcount: CFD/fluids engineer, mechanical/DFM engineer, embedded engineer, aquaculture biologist (pilot), technician; plus a contracted molding partner and a university lab for third‑party SOTE and pilot data.

### 7.5 Commercial framing to preserve

Sell **pond packages** (80 modules + two‑tier manifold + VSD retrofit + controller + 2 wiped probes: ~$9–12k installed per ha) against the farmer's binding constraint — **installed blower kW and t/ha**, plus kWh/kg on generator farms — never against aerotube capex per module. Contract the acid‑dip and probe‑cap service annually; it protects performance and creates recurring revenue. Publish SOTE in both 20 °C freshwater and 34 °C/40 ppt seawater, the field OTR curve, and never the word "nano."
