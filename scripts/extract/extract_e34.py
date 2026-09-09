"""
Extract the PRESLHY E3.4 unignited pool experiments into small CSVs.

Ten 16-90 MB spreadsheets, of which the useful part is a few hundred
kilobytes: the LH2 mass on the scale, the temperatures inside the substrate,
and the temperatures in and above the pool.

    pip install openpyxl
    python extract_e34.py "/path/to/10.35097-1319"

Two outputs per experiment, plus one summary:

    lh2_e34_traces.csv       downsampled time series, one row per sample
    lh2_e34_periods.csv      the vaporisation periods, one row per period
    lh2_e34_summary.csv      one row per experiment

Column names come from PRESLHY D3.5 section 4.1 and Figure 4. The naming is
positional and readable straight off:

    TA<height>-<offset>   above the substrate surface, cm
    TG<depth>-<offset>    inside the substrate; TG02 is 2 mm below the top of
                          the 100 mm bed, so the distance from the surface is
                          100 minus the number

so TG02-00 sits 98 mm below the surface and TG96-00 sits 4 mm below it. Those
are the 4, 9, 14, 54 and 98 mm depths the report plots.

What is measured, and why not "periods"
--------------------------------------
The box is filled three or four times; after each fill the supply stops and
the pool boils off. The report reads one average rate per fill (its Table 3)
over a window it chose by eye.

**The mass loss is not linear over a fill.** Conduction into the ground goes
as ``t^-1/2``, so the rate is steep just after the fill and shallow later, and
the average depends entirely on how long a window is taken. Fitting a straight
line over a whole 278 s fill gives 5.5 g/s where the report's 115 s window
gives 9.6 -- neither is wrong, they are answers to different questions.

So this script does not reproduce Table 3. It emits the **local rate against
time since the fill**, on a short sliding window, which is what the
semi-infinite solution predicts and what a model comparison actually needs.
Table 3's four numbers are recoverable from it by averaging over the report's
windows; the converse is not true.

Time base: the report's Table 3 is on **`Orig.Time`**, the scale's own clock,
which runs 7.67 s behind the synchronised `Sync. Time` in Concrete02. Its
`m0` values land on `Orig.Time` exactly and on `Sync. Time` not at all. The
fills are only 30 s long, so reading the wrong clock moves the fitted rates by
tens of per cent.

`t_orig_s` is that clock. `t_ground_s` is measured from the moment the surface
thermocouple `TA000-00` first reaches liquid-hydrogen temperature, which is
when the ground starts being cooled and is what the semi-infinite solution's
`t` means. **That is a measurement, not a choice**; the report instead
subtracts a round 500 s, which for Concrete02 is 220 s later than the
thermocouple says.

The distinction matters because the box is filled three or four times and the
ground keeps cooling throughout. Timing each fill from its own peak -- the
obvious thing -- gives a conduction comparison out by a factor of five on the
later fills, because by then the ground has been cold for several minutes.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

#: Substrate thermocouples: column name -> depth below the surface [mm].
#: The bed is 100 mm deep and the labels count from the bottom.
SUBSTRATE_DEPTH_MM = {
    "TG02-00": 98.0, "TG46-00": 54.0, "TG86-00": 14.0,
    "TG91-00": 9.0, "TG96-00": 4.0,
    "TG86-05": 14.0, "TG86-15": 14.0, "TG86-23": 14.0,
}
#: Pool and above-pool thermocouples: name -> height above the surface [cm].
POOL_HEIGHT_CM = {
    "TA000-00": 0.0, "TA000-01": 1.0, "TA000-02": 2.0, "TA000-03": 3.0,
    "TA000-05": 5.0, "TA000-07": 7.0, "TA000-10": 10.0, "TA000-15": 15.0,
    "TA000-25": 25.0,
}
HEADER_ROW = 7
POOL_AREA_M2 = 0.25          # 0.5 x 0.5 m box
NAME_RE = re.compile(r"(\d{8})[-_]?([A-Za-z]+\d+)(Wind)?", re.I)


def parse_name(stem: str) -> dict:
    m = NAME_RE.search(stem)
    if not m:
        return {"date": "", "run": stem, "substrate": "", "wind": False}
    date, run, wind = m.group(1), m.group(2), bool(m.group(3))
    sub = re.sub(r"\d+$", "", run).lower()
    return {"date": date, "run": run, "substrate": sub, "wind": wind}


def num(v):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    try:
        return float(str(v).strip().replace(",", "."))
    except ValueError:
        return None


def read_sheet(path: Path):
    """(headers, rows) of the first sheet, from the row that names columns."""
    from openpyxl import load_workbook
    wb = load_workbook(path, read_only=True, data_only=True)
    try:
        ws = wb[wb.sheetnames[0]]
        it = ws.iter_rows(values_only=True)
        for _ in range(HEADER_ROW - 1):
            next(it)
        headers = [("" if c is None else str(c).strip()) for c in next(it)]
        rows = [r for r in it]
    finally:
        wb.close()
    return headers, rows


def _fit(t, m, i0, i1):
    """Least-squares slope [g/s, positive for loss] and its RMS residual."""
    n = i1 - i0 + 1
    tm = sum(t[i0:i1 + 1]) / n
    mm = sum(m[i0:i1 + 1]) / n
    sxy = sum((t[k] - tm) * (m[k] - mm) for k in range(i0, i1 + 1))
    sxx = sum((t[k] - tm) ** 2 for k in range(i0, i1 + 1))
    if sxx <= 0.0:
        return 0.0, float("inf")
    slope = sxy / sxx
    res = [m[k] - (mm + slope * (t[k] - tm)) for k in range(i0, i1 + 1)]
    rms = (sum(r * r for r in res) / n) ** 0.5
    return -slope, rms


def ground_cold_from(t, T_surface, *, threshold_K=25.0):
    """
    Time at which the substrate surface first reaches liquid temperature.

    Returns ``None`` where it never does, which is itself a result: in
    Water01 the surface thermocouple never goes below 25 K and the peak
    inventory is a quarter of the other tests, matching the report's note that
    ditching blew substrate out of the box before a pool could establish.
    """
    for i, x in enumerate(T_surface):
        if x is not None and x <= threshold_K:
            return t[i], i
    return None, None


def find_fills(t, m, *, rise_g=250.0, rise_s=30.0, min_peak_g=400.0):
    """
    Boil-off phases, as ``[(i_peak, i_end)]``.

    A fill is a sharp rise; the phase that matters starts at the peak and runs
    until the mass stops falling. Phases peaking below `min_peak_g` are
    dropped -- those are the cool-down flows before a pool has formed.
    """
    n = len(t)
    win = max(1, int(round(rise_s / max(t[1] - t[0], 1e-6))))
    peaks, i = [], win
    while i < n - win:
        if m[i] - m[i - win] >= rise_g:              # rising fast
            j = i
            while j < n - 1 and max(m[j + 1:j + 1 + win] or [m[j]]) > m[j]:
                j += 1
            if m[j] >= min_peak_g:
                peaks.append(j)
            i = j + win
        else:
            i += 1
    out = []
    for k, p in enumerate(peaks):
        limit = peaks[k + 1] if k + 1 < len(peaks) else n - 1
        j = p
        low = m[p]
        while j < limit:
            if m[j] < low:
                low = m[j]
            if m[j] > low + rise_g:                  # next fill starting
                break
            j += 1
        if t[j] - t[p] >= 20.0:
            out.append((p, j))
    return out


def local_rates(t, m, i0, i1, *, window_s=20.0, every_s=10.0):
    """
    ``[(t_since_peak, rate_g_s, rms)]`` from a sliding least-squares window.

    Twenty seconds is long enough to beat the scale's noise and short enough
    that ``t^-1/2`` is locally straight across it.
    """
    dt = max(t[1] - t[0], 1e-6)
    half = max(2, int(round(0.5 * window_s / dt)))
    step = max(1, int(round(every_s / dt)))
    out = []
    for c in range(i0 + half, i1 - half, step):
        rate, rms = _fit(t, m, c - half, c + half)
        if rate > 0.0:
            out.append((t[c] - t[i0], rate, rms))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("root", help="folder holding the E3.4 spreadsheets")
    ap.add_argument("--every", type=int, default=10,
                    help="keep one sample in N for the traces (default 10)")
    args = ap.parse_args()

    try:
        import openpyxl  # noqa: F401
    except ImportError:
        print("pip install openpyxl")
        return 2

    root = Path(args.root).expanduser().resolve()
    files = sorted(p for p in root.rglob("*.xlsx")
                   if "cH2" not in p.name and p.name[0] != "~")
    if not files:
        print(f"no .xlsx under {root}")
        return 2

    here = Path(__file__).resolve().parent
    traces, periods, summary = [], [], []

    for path in files:
        meta = parse_name(path.stem)
        print(f"  {meta['run']:<14} {path.name}")
        headers, rows = read_sheet(path)
        idx = {h: i for i, h in enumerate(headers) if h}
        # PRESLHY D3.5 Table 3 is on the scale's own clock, not the
        # synchronised one: its m0 values land exactly on `Orig.Time`, which
        # runs 7.67 s behind `Sync. Time` in Concrete02. Using the wrong one
        # shifts every period by that much and changes the fitted rates by
        # tens of per cent, because the fills are only 30 s long.
        t_col = idx.get("Orig.Time [s]",
                        idx.get("Sync. Time [s]", idx.get("X_Value")))
        m_col = idx.get("m(LH2) [g]")
        if t_col is None or m_col is None:
            print(f"    !! no time or mass column; skipped")
            continue

        t = [num(r[t_col]) if t_col < len(r) else None for r in rows]
        m = [num(r[m_col]) if m_col < len(r) else None for r in rows]
        keep = [k for k in range(len(rows))
                if t[k] is not None and m[k] is not None]
        if len(keep) < 100:
            print(f"    !! only {len(keep)} usable samples; skipped")
            continue
        t = [t[k] for k in keep]
        m = [m[k] for k in keep]
        rows = [rows[k] for k in keep]

        s_col = idx.get("TA000-00")
        T_surf = [num(r[s_col]) if s_col is not None and s_col < len(r)
                  else None for r in rows]
        t_cold, _ = ground_cold_from(t, T_surf)
        if t_cold is None:
            print(f"    !! surface never reached liquid temperature; "
                  f"no pool established")

        found = find_fills(t, m)
        for n, (i0, i1) in enumerate(found, 1):
            for t_pool, rate, rms in local_rates(t, m, i0, i1):
                flux = rate * 1e-3 / POOL_AREA_M2
                periods.append({
                    "run": meta["run"], "substrate": meta["substrate"],
                    "wind": int(meta["wind"]), "fill": n,
                    "t_orig_s": t[i0] + t_pool, "t_fill_s": t_pool,
                    "t_ground_s": ("" if t_cold is None
                                   else t[i0] + t_pool - t_cold),
                    "m_lh2_g": m[i0] - rate * t_pool,
                    "rate_g_s": rate, "rms_g": rms,
                    "flux_kg_m2_s": flux,
                    "regression_mm_s": flux / 70.8 * 1e3,
                })

        starts = [t[i0] for i0, _ in found]
        for k in range(0, len(rows), max(args.every, 1)):
            r, row = rows[k], {"run": meta["run"],
                               "substrate": meta["substrate"],
                               "wind": int(meta["wind"]),
                               "t_orig_s": t[k], "m_lh2_g": m[k]}
            prior = [s for s in starts if s <= t[k]]
            row["t_fill_s"] = (t[k] - prior[-1]) if prior else ""
            row["t_ground_s"] = "" if t_cold is None else t[k] - t_cold
            for name, depth in SUBSTRATE_DEPTH_MM.items():
                if name in idx and idx[name] < len(r):
                    row[f"{name}_K"] = num(r[idx[name]])
            for name in POOL_HEIGHT_CM:
                if name in idx and idx[name] < len(r):
                    row[f"{name}_K"] = num(r[idx[name]])
            traces.append(row)

        mine = [p for p in periods if p["run"] == meta["run"]]
        rates = [p["rate_g_s"] for p in mine]
        summary.append({
            "run": meta["run"], "date": meta["date"],
            "substrate": meta["substrate"], "wind": int(meta["wind"]),
            "n_samples": len(rows), "n_fills": len(found),
            "n_rate_points": len(rates),
            "duration_s": t[-1] - t[0],
            "t_ground_cold_s": "" if t_cold is None else t_cold,
            "pool_established": int(t_cold is not None),
            "T_surface_min_K": min((x for x in T_surf if x is not None),
                                   default=""),
            "m_lh2_max_g": max(m),
            "rate_first_g_s": rates[0] if rates else "",
            "rate_last_g_s": rates[-1] if rates else "",
            "file": path.name,
        })

    def dump(name, data):
        if not data:
            return
        keys, seen = [], set()
        for d in data:
            for k in d:
                if k not in seen:
                    seen.add(k)
                    keys.append(k)
        p = here / name
        with p.open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=keys)
            w.writeheader()
            w.writerows(data)
        print(f"wrote {p}  ({len(data)} rows)")

    dump("lh2_e34_summary.csv", summary)
    dump("lh2_e34_rates.csv", periods)
    dump("lh2_e34_traces.csv", traces)
    print("\nSubstrate thermocouple depths below the surface [mm]:")
    for k, v in sorted(SUBSTRATE_DEPTH_MM.items(), key=lambda kv: kv[1]):
        print(f"  {k:<10} {v:>5.0f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
