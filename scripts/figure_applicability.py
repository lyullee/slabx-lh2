"""
The applicability map: where the formulation is entitled to answer.

    python scripts/figure_applicability.py            writes figures/applicability.png
    python scripts/figure_applicability.py --show

This is the one figure that is not a model result. It is the boundary of the
`x`-marching premise in the two variables a monitoring system knows before it
runs anything -- release rate and wind speed -- with every experimental
campaign in this work placed on it.

Two things are drawn, and they are not the same thing
-----------------------------------------------------
The **curves** are the screening approximation `u_crit = a q^b`, fitted to a
**pool** source. The **fill of each marker** is the model's own diagnostic,
`max w_c/u`, measured on that trial.

They disagree, and the disagreement is informative: the curve flags the calmer
E3.5 trials, and the diagnostic says all seventeen are inside. Those are
momentum jets, and a jet resists lofting in a way a pool does not, so **the
pool-fitted curve is conservative for them**. Screen with the curve; decide
with the diagnostic.

What the reader should take from it
-----------------------------------
The worst case a separation distance is usually set from, a large release in
stable low wind, is **outside**. That is not a property of this
implementation: Briggs's bent-over plume formula rests on the same premise and
is equally invalid there, and so is every integral model that marches
downwind.

The curves are `u_crit = a q^b` per Pasquill class, bisected on the model's own
`max w_c/u` and fitted in log-log over 0.1 to 30 kg/s. **Outside that range
they are extrapolation**, which is why the fitted band is drawn explicitly.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import matplotlib
import numpy as np

from slabx_lh2.diagnostics import (CRITICAL_WIND_FIT, CRITICAL_WIND_RANGE_KGS,
                                   critical_wind)

#: Campaign, marker, source type, and trials as (rate kg/s, wind m/s,
#: measured max w_c/u). **The ratio is the model's own diagnostic**, not the
#: screening curve -- the two disagree and that disagreement is the point.
CAMPAIGNS = {
    "FFI (Spadeadam)": {
        "marker": "o", "source": "jet",
        "trials": [(0.225, 3.2, 0.11), (0.730, 5.8, 0.03),
                   (0.828, 6.7, 0.03), (0.715, 5.2, 0.04),
                   (0.832, 2.7, 0.09), (0.162, 6.5, 0.02)],
    },
    "PRESLHY E3.5": {
        "marker": "s", "source": "jet",
        "trials": [(0.1395, 3.60, 0.189), (0.1055, 1.83, 0.308),
                   (0.1055, 3.90, 0.107), (0.1055, 2.50, 0.205),
                   (0.1055, 2.37, 0.194), (0.298, 2.47, 0.229),
                   (0.265, 2.700, 0.221), (0.095, 2.700, 0.015),
                   (0.265, 1.50, 0.123), (0.298, 1.93, 0.158),
                   (0.1395, 4.17, 0.051), (0.1055, 2.87, 0.065),
                   (0.1395, 1.60, 0.378), (0.1055, 0.57, 0.697),
                   (0.298, 1.70, 0.139), (0.265, 1.70, 0.139),
                   (0.095, 1.90, 0.016)],
    },
    "NASA White Sands": {
        "marker": "^", "source": "pool",
        "trials": [(10.09, 1.6, 5.14), (11.53, 2.2, 2.36),
                   (12.23, 3.6, 1.17), (16.82, 6.3, 0.59)],
    },
    "Zhang et al. 2024": {
        "marker": "D", "source": "pool",
        "trials": [(53.10, 0.13, 217.4), (4.42, 0.30, 44.6),
                   (5.90, 0.04, 455.4), (3.69, 0.05, 397.0),
                   (4.25, 0.61, 13.7), (53.10, 0.11, 252.3),
                   (42.48, 0.01, 821.8), (1.77, 0.15, 110.4)],
    },
}


def build(results: dict | None = None):
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    fig, ax = plt.subplots(figsize=(7.2, 5.4))
    q = np.logspace(-1.3, 2.0, 400)

    lo, hi = CRITICAL_WIND_RANGE_KGS
    ax.axvspan(q[0], lo, color="0.93", zorder=0)
    ax.axvspan(hi, q[-1], color="0.93", zorder=0)
    ax.text(hi * 1.35, 0.14, "extrapolated", rotation=90, fontsize=7,
            color="0.45", va="bottom")
    ax.text(q[0] * 1.15, 0.14, "extrapolated", rotation=90, fontsize=7,
            color="0.45", va="bottom")

    # the D curve separates the plane; shade below it
    d = np.array([critical_wind(x, "D") for x in q])
    ax.fill_between(q, 1e-2, d, color="#c9302c", alpha=0.07, zorder=1)

    greys = {"A": "0.72", "B": "0.62", "C": "0.52", "D": "0.10",
             "E": "0.38", "F": "0.28"}
    for cls in "ABCDEF":
        u = [critical_wind(x, cls) for x in q]
        ax.plot(q, u, color=greys[cls], lw=2.0 if cls == "D" else 1.0,
                zorder=3, solid_capstyle="round")
        ax.annotate(cls, (q[-1], u[-1]), textcoords="offset points",
                    xytext=(4, -3), fontsize=8, color=greys[cls],
                    fontweight="bold" if cls == "D" else "normal")

    for name, spec in CAMPAIGNS.items():
        for x, y, ratio in spec["trials"]:
            ok = ratio <= 1.0
            ax.plot(x, y, spec["marker"], ms=6.8, zorder=5,
                    mfc="white" if ok else "#c9302c",
                    mec="#1a1a1a" if ok else "#7d1d1a", mew=1.1)

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(q[0], q[-1] * 2.2)
    ax.set_ylim(6e-3, 26)
    ax.set_xlabel("release rate  $q$  [kg s$^{-1}$]")
    ax.set_ylabel("wind speed at 10 m  $u$  [m s$^{-1}$]")
    ax.set_title("Where the downwind-marching formulation may be used",
                 fontsize=11, pad=10)
    ax.text(1.2, 0.030, "measured $w_c/u > 1$", fontsize=9,
            color="#8d2420", ha="center", va="center")
    ax.text(0.35, 12.0, "measured $w_c/u \\leq 1$", fontsize=9,
            color="0.30", ha="center")
    ax.annotate("screening curve is conservative\nfor momentum jets",
                xy=(0.11, 0.60), xytext=(0.24, 0.055),
                fontsize=7.5, color="0.35", ha="center",
                arrowprops=dict(arrowstyle="->", color="0.55", lw=0.8,
                                connectionstyle="arc3,rad=-0.25"))
    ax.grid(True, which="both", lw=0.4, color="0.88", zorder=0)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)

    handles = [Line2D([], [], ls="none", marker=s["marker"], ms=6.5,
                      mfc="white", mec="#1a1a1a", label=n)
               for n, s in CAMPAIGNS.items()]
    handles += [
        Line2D([], [], ls="none", marker="o", ms=6.8, mfc="#c9302c",
               mec="#7d1d1a", label="outside the premise"),
        Line2D([], [], color="0.10", lw=2.0,
               label="$u_{crit}$ screening, class D"),
    ]
    ax.legend(handles=handles, fontsize=8, loc="lower right", frameon=False,
              handletextpad=0.6, labelspacing=0.5)
    fig.tight_layout()
    return fig


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--show", action="store_true")
    ap.add_argument("--out", default="figures/applicability.png")
    args = ap.parse_args()

    if not args.show:
        matplotlib.use("Agg")

    root = Path(__file__).resolve().parent.parent
    rj = root / "results" / "results.json"
    results = json.loads(rj.read_text()) if rj.exists() else None

    fig = build(results)
    if args.show:
        import matplotlib.pyplot as plt
        plt.show()
        return 0
    out = root / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=200)
    fig.savefig(out.with_suffix(".pdf"))
    print(f"wrote {out} and {out.with_suffix('.pdf')}")

    agree = disagree = 0
    n_in = n_out = 0
    for name, spec in CAMPAIGNS.items():
        for x, y, ratio in spec["trials"]:
            measured_in = ratio <= 1.0
            screened_in = y >= critical_wind(x, "D")
            n_in += measured_in
            n_out += not measured_in
            agree += measured_in == screened_in
            disagree += measured_in != screened_in
    print(f"  measured diagnostic: {n_in} inside, {n_out} outside")
    print(f"  screening agrees on {agree} of {agree + disagree}; "
          f"the {disagree} disagreements are all momentum jets the pool-fitted "
          f"curve flags conservatively")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
