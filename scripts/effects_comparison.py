"""EFFECTS' own NASA conditions: is their validation set inside the premise?

Mack & Boot (JLP 2023) validate their buoyant-plume extension on five NASA
trials. Their entrainment closure cites Ermak's SLAB manual and reproduces its
EQ 35a form, so if the premise diagnosis of this work is structural rather
than implementation-specific, their validation points should sit outside it
too -- and their reported vertical under-prediction should follow.
"""
import warnings; warnings.simplefilter("ignore")
import math
import numpy as np
from slabx.core.plume import run_dispersion
from slabx.core.source import EvaporatingPool
from slabx.submodels.atmosphere import Atmosphere
from slabx.thermo.base import Substance
from slabx.thermo.coolprop import CoolPropThermo, coolprop_water
from slabx_lh2.diagnostics import premise_summary, rise_scaling, critical_wind
from slabx_lh2.plume_width import plume_width_coupling
from slabx_lh2.water_ice import with_sublimation

H2 = Substance(name="H2", mw=0.002016, cp_vapour=14300., cp_liquid=9800.,
               dh_vap=445000., T_boil=20.3, rho_liquid=70.8)
#  test: rate kg/s, duration s, T K, RH %, u m/s   (EFFECTS Table 2)
EFFECTS = {2: (9.23, 39, 24., 49., 1.55), 3: (4.23, 85, 26., 27., 4.5),
           4: (10.29, 35, 15., 43., 3.35), 5: (9.95, 17, 12., 43., 6.3),
           6: (9.48, 38, 15., 29., 2.2), 7: (1.66, 120, 17., 29., 3.1)}
#  EFFECTS Table 3: horizontal LFL, their sim, vertical LFL, their sim
REPORTED = {4: (212, 169, 53, 38), 5: (None, None, 27, 23),
            6: (160, 139, 65, 48), 3: (120, 121, None, None),
            7: (61, 81, 9, 9)}
POOL_R = 3.0                      # EFFECTS report a 3 m radius for test 6

print("EFFECTS' own conditions, roughness 0.03 m as they state")
print(f"{'test':>5}{'q':>7}{'u':>6}{'u_crit':>8}{'max w_c/u':>11}{'angle':>7}"
      f"{'premise':>10}   EFFECTS vertical LFL")
rows = {}
for t, (q, ts, T, rh, u) in sorted(EFFECTS.items(), key=lambda kv: kv[1][4]):
    atm = Atmosphere(u_ref=u, z_ref=10., T=T+273.15, rh=rh, z0=0.03,
                     stability="D")
    src = EvaporatingPool(substance=H2, rate=q, area=math.pi*POOL_R**2,
                          duration=float(ts))
    with plume_width_coupling():
        tr, _ = run_dispersion(src, atm, CoolPropThermo(H2, fluid="Hydrogen"),
                               with_sublimation(coolprop_water()),
                               x_max=400., n_puff_steps=40)
    s = premise_summary(tr)
    rows[t] = (s, tr, atm)
    exp, sim = REPORTED.get(t, (None, None, None, None))[2:4]
    note = (f"{exp} m obs, {sim} sim ({sim/exp-1:+.0%})"
            if exp else "not reported")
    print(f"{t:>5}{q:>7.2f}{u:>6.2f}{critical_wind(q,'D'):>8.2f}"
          f"{s['max']:>11.2f}{s['angle_deg']:>7.1f}"
          f"{('OUTSIDE' if s['violated'] else 'inside'):>10}   {note}")

n_out = sum(1 for s, _, _ in rows.values() if s["violated"])
print(f"\n  {n_out} of {len(rows)} of EFFECTS' validation trials are outside"
      f" the bent-over premise")

print("\nAnd the scaling that says why the rise is hard to close")
print(f"{'test':>5}{'dlnB/dlnz':>11}{'dlnh/dlnz':>11}{'s':>7}"
      f"{'2/(s+1)':>9}{'fitted n':>10}{'Briggs needs':>14}")
for t in sorted(rows, key=lambda k: EFFECTS[k][4]):
    try:
        r = rise_scaling(rows[t][1])
    except ValueError:
        print(f"{t:>5}   never lofts in the fitting window")
        continue
    print(f"{t:>5}{r['dlnB_dlnz']:>11.3f}{r['dlnh_dlnz']:>11.3f}{r['s']:>7.3f}"
          f"{r['exponent_predicted']:>9.3f}{r['exponent']:>10.3f}"
          f"{'s = 2':>14}")
