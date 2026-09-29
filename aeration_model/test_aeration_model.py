"""Sanity tests for the aeration model.  Run:  python -m unittest test_aeration_model  (from this folder)."""

import math
import random
import unittest

from aeration_physics import (
    KG_O2_PER_NM3_AIR, blower_kwh_per_nm3, bubble_slip_velocity, do_saturation_mg_l,
    field_factor, sote_standard,
)
from kla_fit import fit_reaeration, standardize


class Properties(unittest.TestCase):
    def test_do_saturation_tables(self):
        # APHA / USGS tables: 20 C fresh 9.09, 30 C fresh 7.56, 25 C 35 ppt ~6.8
        self.assertAlmostEqual(do_saturation_mg_l(20, 0), 9.09, delta=0.05)
        self.assertAlmostEqual(do_saturation_mg_l(30, 0), 7.56, delta=0.06)
        self.assertAlmostEqual(do_saturation_mg_l(25, 35), 6.75, delta=0.1)

    def test_oxygen_per_nm3(self):
        self.assertAlmostEqual(KG_O2_PER_NM3_AIR, 0.299, delta=0.002)

    def test_slip_velocity_continuous(self):
        for r in (7.0e-4, 5.1e-3):
            self.assertAlmostEqual(bubble_slip_velocity(r * 0.999), bubble_slip_velocity(r * 1.001), delta=0.01)


class BubbleModel(unittest.TestCase):
    def test_fine_pore_benchmark_4p5m(self):
        # fine-pore diffusers in clean water at 4.5 m: SOTE ~25-35 %
        self.assertTrue(0.25 <= sote_standard(2.5, 4.5, 0.15) <= 0.35)

    def test_monotonic(self):
        self.assertGreater(sote_standard(1.0, 1.35), sote_standard(2.0, 1.35))
        self.assertGreater(sote_standard(2.0, 1.35, 0.1), sote_standard(2.0, 1.35, 0.5))
        self.assertGreater(sote_standard(2.0, 2.0), sote_standard(2.0, 1.0))


class Energy(unittest.TestCase):
    def test_blower_energy_scales_with_pressure(self):
        e18, e36 = blower_kwh_per_nm3(18, 0.6), blower_kwh_per_nm3(36, 0.6)
        self.assertAlmostEqual(e36 / e18, 1.9, delta=0.1)
        # ideal isothermal floor: p ln(pr) * T/T0
        iso = 101325 * math.log((101325 + 18000) / 101325) * (308.15 / 273.15) / 3.6e6
        self.assertGreater(e18 * 0.6, iso)

    def test_field_factor_reference(self):
        # standard conditions -> factor = alpha
        self.assertAlmostEqual(field_factor(20, 0, 0.0, 1.0), 1.0, delta=0.01)


class KlaFit(unittest.TestCase):
    def test_recovers_synthetic_curve(self):
        rnd = random.Random(1)
        kla, c_inf, c0 = 6.0 / 3600, 9.3, 0.4
        t = [30.0 * i for i in range(60)]
        c = [c_inf - (c_inf - c0) * math.exp(-kla * ti) + rnd.gauss(0, 0.03) for ti in t]
        fit = fit_reaeration(t, c)
        self.assertAlmostEqual(fit["kla"] * 3600, 6.0, delta=0.1)
        self.assertAlmostEqual(fit["c_inf"], 9.3, delta=0.05)
        std = standardize(fit, 10.0, 20.0, airflow_nm3_h=10.0)
        self.assertAlmostEqual(std["sotr_kg_h"], 6.0 * 9.3 * 10 / 1000 * 9.09 / do_saturation_mg_l(20, 0), delta=0.02)


if __name__ == "__main__":
    unittest.main()
