# aeration_model — first-principles aerator energy model

Pure Python 3 (no packages). Backs the numbers in `../NextGen_Aerator_Expert_Assessment.md`.

| File | Purpose |
|---|---|
| `aeration_physics.py` | O2/N2 solubility (Weiss 1970), discrete-bubble model (McGinnis & Little 2002, Wüest 1992), plume velocity, blower energy, field correction |
| `compare_architectures.py` | Paddlewheel vs aerotube vs SPD V3 vs proposed LLFB vs oxygen routes; all assumptions at the top |
| `kla_fit.py` | ASCE 2-06 reaeration fit for tank tests → kLa20, SOTR, SOTE, SAE |
| `test_aeration_model.py` | Sanity tests |

```bash
cd aeration_model
python compare_architectures.py
python -m unittest test_aeration_model
python kla_fit.py probe1.csv --volume 12.5 --temp 24.1 --airflow 18 --power 0.21
```

Absolute SOTE from a single-size bubble model is ±30 %; coarse bubbles are under-predicted (up to 2×).
Calibrate `kl_factor` with the first clean-water tank test before using the numbers for sizing.
