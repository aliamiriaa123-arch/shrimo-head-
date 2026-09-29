# TRL-4 Shop and Water-Tank Verification Protocol
## Submerged Pulsed Micro-Slit Aerator Prototype

**Status:** Official Engineering Testing & Commissioning Standard (TRL 4 - Lab Proof of Concept)  
**Date:** September 2026 / شهریور ۱۴۰۵  
**Target Module:** Submerged Pulsed Micro-Slit Diffuser (1.5 m depth, 35–42 ppt hypersaline, 30 Nm³/h per unit)

---

## 0. Test Article Configuration & Instrumentation

Test the complete assembled module built from CAD **V3.0** (`3D_Print_STLs/`, see `CAD_V3_DESIGN_BASIS_AND_VERIFICATION.md`) using production-intent hardware:
- EPDM O-rings: stack flanges Part 08/05 and Part 09/08 — 3.53 mm cord in 2.70 mm deep groove (ID 40.87 mm and 66.27 mm); oscillator cavity (Part 04/05) and both downcomers (Part 02/04) — 2.62 mm cord in 2.00 mm deep groove; cartridges (Parts 06/07 to Part 02) — 2.62 mm cord in 2.00 mm deep groove.
- EPDM duckbill non-return valve in Part 08, **downstream of the accumulator (Part 09)** and directly above the oscillator inlet (keeps the trapped volume at 0.73 L → dry core).
- Calibrated rigid micro-slit cartridges (Parts 06 & 07): **11 slits of 1.0 mm x 20.0 mm per bank** (220 mm² normal area), 2.5 mm webs, 20° downward discharge.
- Grade 316 stainless fasteners (M8 base bolts, M4/M5 with brass heat-set inserts).
- 100% airtight twin-plenum manifold (Part 02) with **integral** A/B divider (replaces the V2.2 air-bell shroud and the separate Part 03 baffle).
- Acoustic feedback loop between the two hose barbs on Part 05 ($L = 1.40\text{ m}$, ID 8.0 mm, OD 10.0 mm polyurethane).
- Ballast: 2 solid concrete blocks 400 × 200 × 100 mm in the Part 10 cradles (the module is buoyant without ballast; net submerged weight with ballast ≈ +17.7 kg PETG / +15.1 kg PA12).

### DAQ & Sensor Setup:
1. **Inlet Pressure ($P_\text{in}$):** M5 tap on the accumulator wall (Part 09, +Y side) — upstream of the duckbill valve (0–100 kPa(g)).
2. **Oscillator Control Ports ($P_\text{CA}, P_\text{CB}$):** Tees in the feedback loop directly at the two barbs on Part 05; fast differential transducers (±10 or ±25 kPa, $\ge 2\text{ kHz}$ sampling rate, 500–800 Hz anti-alias filter).
3. **Plenum Pressures ($P_\text{DA}, P_\text{DB}$):** M5 taps through the −Y end wall of Part 02 into plenum A and plenum B.
4. **Air Mass Flow Meter:** Thermal mass or vortex meter corrected to standard conditions ($2400\text{ Nm}^3/\text{h} / 80 \implies 30\text{ Nm}^3/\text{h}$; ≈ 25.5 m³/h actual at the blower outlet, ≈ 29.8 m³/h actual at slit depth).
5. **DO, Salinity, Temperature Sensors:** Calibrated optical DO probes at bottom, mid-depth, and upper levels.
6. **High-Speed Optical Imaging:** Camera capable of 500–1000 fps with backlight / shadowgraphy illumination.

---

## 1. Pneumatic Leak & Pressure-Decay Test (Dry Shop Test)

### 1.1 Pressures:
- **Functional Pressure:** $45\text{ kPa(g)}$ (nominal maximum blower condition).
- **Proof / Leak Test Pressure:** $55\text{ kPa(g)}$ (10 kPa safety margin; do not exceed without proof-testing polymer).

### 1.2 Procedure:
1. Cap both 11-slit cartridge faces using low-volume clamped test gaskets; plug the 1/2" NPT drain and the three M5 taps.
2. Slowly pressurize with clean dry nitrogen/air to $20\text{ kPa(g)}$; check gross leaks.
3. Hold at $45\text{ kPa(g)}$ for 5 minutes.
4. Raise to $55\text{ kPa(g)}$ over 60 seconds; isolate air supply.
5. Allow **10-minute thermal stabilization** (do not measure decay during this time).
6. Record temperature-corrected pressure decay over **30 minutes**.
7. Apply leak detection fluid (soapy water) to all joints, O-rings, and cable/port glands.

### 1.3 Acceptance Criteria:
- **PASS:** Temperature-corrected pressure drop $\le \mathbf{1.0\text{ kPa}}$ over 30 minutes ($\le 0.033\text{ kPa/min}$).
- **REJECT:** $> 1.0\text{ kPa}$ drop or continuous bubble stream.
- Zero O-ring extrusion, cracking, or insert pull-out.

---

## 2. Benchtop Oscillator Frequency & Switching Test

### 2.1 Test Matrix:
- Inlet Pressure: $35\text{ kPa(g)}$, $40\text{ kPa(g)}$, $45\text{ kPa(g)}$.
- Feedback Tube Trimming: $L = 1.10\text{ m}$, $1.40\text{ m}$, $1.90\text{ m}$.

### 2.2 Measurements (at $\ge 2\text{ kHz}$):
- Differential pressure: $P_\Delta = P_\text{A} - P_\text{B}$.
- Dominant frequency via FFT and zero-crossing.
- Duty cycle and Bank A/B flow ratio.

### 2.3 Acceptance Criteria:
- **Frequency:** Stable in range **50 to 80 Hz** (target ~65 Hz with $L = 1.40\text{ m}$).
- **Coefficient of Variation:** $\le 5\%$ over 60 seconds.
- **Duty Cycle:** 45% to 55% per bank (symmetrical alternation).
- **Flow Ratio (Bank A / Bank B):** $0.90\text{ to }1.10$.
- **Latching:** Zero sustained latching ($> 100\text{ ms}$). Automatic restart after 100 ms interruption.

---

## 3. Water-Tank Bubble Size & SOTE Verification (1.5 m Submerged Column)

### 3.1 Tank Setup:
- Clear vertical column, depth $\ge 1.50\text{ m}$ above diffuser.
- Water matrices:
  - **Test A:** Clean freshwater at $20 \pm 1^\circ\text{C}$ (for ASCE 2-06 benchmark).
  - **Test B:** Hypersaline process water ($35\text{--}42\text{ ppt}$, $30\text{--}35^\circ\text{C}$, biofloc/organic suspension).

### 3.2 High-Speed Shadowgraphy ($d_{32}$ Determination):
- Sampling windows: $50\text{ mm}$, $300\text{ mm}$, $750\text{ mm}$, and $1200\text{ mm}$ above slits.
- Segment $\ge 10,000$ individual bubbles per test condition.
- Calculate Sauter mean diameter:
  $$d_{32} = \frac{\sum d_i^3}{\sum d_i^2}$$
- **Acceptance Criterion:** $d_{32} = \mathbf{1.0\text{ to }1.5\text{ mm}}$ under nominal flow (30 Nm³/h ≈ 29.8 m³/h actual at slit depth, $v \approx 37.6\text{ m/s}$ per active bank through 220 mm²).
- Less than $10\%$ coalescence between adjacent vertical planes.

### 3.3 ASCE 2-06 Clean Water SOTE Test:
- Deoxygenate with sodium sulfite + cobalt catalyst (or pure $N_2$ bubbling).
- Record DO rise curves at 3 depths until $90\%$ saturation.
- Determine $K_La$, SOTR, and verify SOTE in clean water $\ge 10\text{--}12\%$.

---

## 4. Wave Imbalance & Anti-Latching Test

### 4.1 Principle:
Simulate uneven external pond wave surge ($\pm 5\text{ kPa}$ differential head $\approx 0.5\text{ m}$ water level wave) across Bank A and Bank B.

### 4.2 Fixture & Procedure:
- Enclose Bank A and Bank B discharge slits in separate transparent test chambers.
- Impose differential water backpressure $\Delta P_\text{water} = P_\text{Bank A} - P_\text{Bank B}$ from $-5\text{ kPa}$ to $+5\text{ kPa}$ in steps of $1\text{ kPa}$ and $2.5\text{ kPa}$.
- Apply sinusoidal wave cycling at $0.05\text{ Hz}$, $0.1\text{ Hz}$, and $0.2\text{ Hz}$.

### 4.3 Acceptance Criteria:
- Oscillator frequency stays within **50–80 Hz** (frequency drift $\le 10\%$).
- No latching or stall lasting $> 100\text{ ms}$.
- Recovery time after sharp wave reversal $\le 250\text{ ms}$.
- Total air flow reduction $\le 15\%$.
- **Dry-Core Protection:** Zero water ingress into the upper oscillator chamber or duckbill valve.

---

## 5. Shop Maintenance & CIP Flushing Standard

### 5.1 Routine Freshwater Flush (After every run):
1. Flush low-pressure freshwater ($\le 10\text{--}15\text{ kPa}$) through the air intake.
2. Run oscillator for 2–5 minutes to purge saline aerosols.
3. Rinse slit cartridges from plenum outward. Never use wire or metal picks in 1.0 mm slits.

### 5.2 Citric Acid Mineral Scale CIP:
- **Concentration:** $2\text{--}5\text{ wt\%}$ citric acid solution (ambient to $35^\circ\text{C}$).
- **Contact Time:** $20\text{--}30\text{ minutes}$.
- **Rule:** Never use Hydrochloric Acid (HCl), as it attacks stainless steel and causes pitting corrosion.
- Thoroughly rinse with clean freshwater until neutral pH.

### 5.3 Hypochlorite Biofilm Cleaning (Separated Step):
- **Concentration:** $100\text{--}200\text{ mg/L}$ free available chlorine at pH 7–8.
- **Contact Time:** $10\text{--}20\text{ minutes}$.
- **CRITICAL SAFETY RULE:** **NEVER MIX ACID AND BLEACH.** Acid generates lethal chlorine gas ($Cl_2$). Always execute:  
  $$\text{Acid Clean} \implies \text{Freshwater Rinse} \implies \text{Hypochlorite Clean} \implies \text{Freshwater Rinse}$$

### 5.4 Cartridge Replacement Trigger:
- Any slit narrowed by $> 10\%$ or blocked.
- Pressure drop increased by $> 15\%$ after cleaning.
- Measured bubble $d_{32}$ increased by $> 20\%$.

---

## 6. Official TRL-4 Release Checklist

| Step | Test Description | Acceptance Gate | Status |
|:---:|---|---|:---:|
| **G0** | Digital CAD verification (`verification/verify_spd_v3.py`) | Mesh integrity, zero interference, sealed continuous air path, A/B isolation, slit geometry, volumes, buoyancy | **Done — 82/82 PASS (2026-09-28)** |
| **G1** | Dimensional & CMM Inspection | 1.0 mm slits open (11 per bank), webs 2.5 mm, O-ring groove depth 2.70 mm / 2.00 mm, nozzle b = 6.00 ± 0.05 mm | Ready |
| **G2** | Pneumatic Leak Decay (55 kPa) | $\Delta P \le 1.0\text{ kPa}$ over 30 min | Pending |
| **G3** | Benchtop Frequency Sweep | Alternating frequency 50–80 Hz ($L = 1.40\text{ m}$) | Pending |
| **G4** | 10x Submerged Startup/Shutdown | Zero water in oscillator cavity or duckbill valve | Pending |
| **G5** | $\pm 5\text{ kPa}$ Wave Imbalance Test | No latching, recovery $\le 250\text{ ms}$ | Pending |
| **G6** | High-Speed Bubble Sizing | $d_{32} = 1.0\text{--}1.5\text{ mm}$ in hypersaline water | Pending |
| **G7** | Standard SOTE Measurement | ASCE 2-06 clean water re-aeration verified | Pending |
