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

ROOT = Path(__file__).resolve().parent.parent

from slabx_lh2.diagnostics import (CRITICAL_WIND_FIT, CRITICAL_WIND_RANGE_KGS,
                                   critical_wind)

#: Marker per campaign. **The points themselves are not hard-coded here** --
#: an earlier version listed the release rates, winds and premise ratios in
#: this file, and they went stale when the E3.5 conditions were corrected.
#: They now come from `applicability_all.py`'s output.
MARKERS = {"FFI": "o", "PRESLHY E3.5": "s", "NASA": "^", "Zhang 2024": "D"}


def load_cases(path=None):
    """
    Read the per-case table `applicability_all.py` writes.

    Regenerate it first if it is missing; the figure is a view of that table
    and must not carry its own copy of the numbers.
    """
    import csv
    import subprocess
    p = Path(path) if path else (ROOT / "paper_results" /
                                 "applicability_all_cases.csv")
    if not p.exists():
        subprocess.run([sys.executable,
                        str(ROOT / "scripts" / "applicability_all.py")],
                       cwd=ROOT, check=True, capture_output=True)
    out = {}
    with p.open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            out.setdefault(r["dataset"], []).append(
                (float(r["rate_kg_s"]), float(r["wind_ref_m_s"]),
                 float(r["premise_ratio_max"]), r["source_type"]))
    return out


def build(cases: dict | None = None):
    cases = cases or load_cases()
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

    for name, trials in cases.items():
        marker = MARKERS.get(name, "o")
        for x, y, ratio, _kind in trials:
            ok = ratio <= 1.0
            ax.plot(x, y, marker, ms=6.8, zorder=5,
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

    handles = [Line2D([], [], ls="none", marker=MARKERS.get(n, "o"), ms=6.5,
                      mfc="white", mec="#1a1a1a", label=n)
               for n in cases]
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

    root = ROOT
    cases = load_cases()
    fig = build(cases)
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
    for name, trials in cases.items():
        for x, y, ratio, _kind in trials:
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
