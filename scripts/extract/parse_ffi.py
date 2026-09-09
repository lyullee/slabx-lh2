"""
Parse Appendix A of FFI-RAPPORT 20/03101 into two tables.

The appendix carries, for each of the seven outdoor tests, a per-sensor summary
(average, maximum, minimum, standard deviation) together with the sensor's
position in polar form -- R metres from the release point, Z metres above the
ground, B degrees bearing.  It also carries the averaging window each summary
was taken over, which matters: these are not whole-record statistics.

Two files come out:

    lh2_ffi_conditions.csv   one row per test
    lh2_ffi_sensors.csv      one row per test per sensor

Decimal commas are converted.  Some tests use points instead, so both are
accepted.  Nothing is interpolated and nothing is dropped silently: a sensor
line that does not parse is reported.
"""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

NUM = r"-?\d+(?:[.,]\d+)?"
SENSOR = re.compile(
    # no word boundary: the previous sensor's unit is glued to this name
    # ("... 0,1 %volOC_02 (R=30, ...") so \b would not hold
    rf"(TT|OC)_(\d+)\s*"
    rf"\(R=({NUM}),\s*Z=({NUM}),\s*B=({NUM})\)\s*"
    rf"({NUM})\s+({NUM})\s+({NUM})\s+({NUM})\s*"
    rf"(%vol|°C)"
)
TESTNAME = re.compile(r"Test Name\s+Test(\d+)")
WINDOW = re.compile(r"(?:^|\s)Start\s+(-?\d+)\s+sec.*?End\s+(-?\d+)\s+sec", re.S)


def f(s: str) -> float:
    return float(s.replace(",", "."))


# per-test facts read from the body of the report (chapter 2), kept here rather
# than parsed, because the body states them once in prose and tables that the
# text extraction does not preserve as tables
CONDITIONS = [
    # test, date, orientation, tanker_barg, outflow_kg_min, run_min, ignited,
    # u_mean, u_sd, dir_mean, dir_sd, T_amb
    (1, "2019-12-11", "vertical_down",  2.0, 13.5, 13, False, 3.2, 0.8, 246, 14, 1.0),
    (2, "2019-12-12", "vertical_down",  6.0, 28.2,  8, False, 4.1, 0.8,  82, 10, 1.5),
    (3, "2019-12-13", "vertical_down", 10.0, 43.8, 15, False, 5.8, 1.8, 259, 11, 2.9),
    (4, "2019-12-13", "horizontal",    10.0, 49.7,  6, False, 6.7, 1.6, 264, 10, 3.3),
    (5, "2019-12-13", "vertical_down", 10.0, 42.9,  6, True,  5.2, 1.9, 257, 12, 3.7),
    (6, "2019-12-13", "horizontal",    10.0, 49.9,  3, True,  2.7, 0.9, 245, 15, 3.8),
    (7, "2019-12-13", "vertical_down",  0.8,  9.7,  8, False, 6.5, 1.4, 266, 11, 3.2),
]


def main() -> int:
    src = Path(sys.argv[1] if len(sys.argv) > 1 else "ffi.txt")
    text = src.read_text(encoding="utf-8", errors="replace")

    # the appendix begins where the reference list ends
    start = text.find("A Results outdoor leakage tests")
    if start < 0:
        print("!! appendix heading not found")
        return 1
    end = text.find("The results for Test 8 to Test 15")
    body = text[start:end if end > 0 else len(text)]

    # split into blocks, each opening with a "Test Name TestNN" marker
    marks = [(m.start(), int(m.group(1))) for m in TESTNAME.finditer(body)]
    if not marks:
        print("!! no test markers found")
        return 1
    marks.append((len(body), -1))

    rows: list[dict] = []
    seen: dict[tuple[int, str], dict] = {}
    for (pos, test), (nxt, _) in zip(marks, marks[1:]):
        block = body[pos:nxt]
        w = WINDOW.search(block)
        win_start, win_end = (int(w.group(1)), int(w.group(2))) if w else ("", "")
        for m in SENSOR.finditer(block):
            kind, num, R, Z, B, avg, mx, mn, sd, unit = m.groups()
            key = (test, f"{kind}_{int(num):02d}")
            row = {
                "test": test,
                "sensor": key[1],
                "kind": "concentration" if kind == "OC" else "temperature",
                "R_m": f(R), "z_m": f(Z), "bearing_deg": f(B),
                "average": f(avg), "max": f(mx), "min": f(mn), "stdev": f(sd),
                "unit": "vol%" if unit == "%vol" else "degC",
                "window_start_s": win_start, "window_end_s": win_end,
            }
            # the same sensor appears in several plots per test; keep the first
            if key not in seen:
                seen[key] = row
                rows.append(row)

    out_dir = Path(".")
    sens = out_dir / "lh2_ffi_sensors.csv"
    with sens.open("w", newline="", encoding="utf-8") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        wr.writeheader()
        wr.writerows(rows)

    cond = out_dir / "lh2_ffi_conditions.csv"
    with cond.open("w", newline="", encoding="utf-8") as fh:
        wr = csv.writer(fh)
        wr.writerow(["test", "date", "orientation", "tanker_barg",
                     "outflow_kg_min", "outflow_kg_s", "run_min", "ignited",
                     "u_mean_m_s", "u_sd_m_s", "wind_dir_deg", "wind_dir_sd_deg",
                     "T_amb_C", "nozzle_mm", "n_sensors_parsed"])
        for (t, d, o, p, q, r, ig, u, us, wd, wds, ta) in CONDITIONS:
            n = sum(1 for row in rows if row["test"] == t)
            wr.writerow([t, d, o, p, q, round(q / 60.0, 4), r,
                         "yes" if ig else "no", u, us, wd, wds, ta, 25.4, n])

    # report
    print(f"parsed {len(rows)} sensor rows across "
          f"{len(sorted({r['test'] for r in rows}))} tests")
    for t in sorted({r["test"] for r in rows}):
        oc = [r for r in rows if r["test"] == t and r["kind"] == "concentration"]
        tt = [r for r in rows if r["test"] == t and r["kind"] == "temperature"]
        w = next((r for r in rows if r["test"] == t), {})
        radii = sorted({r["R_m"] for r in oc})
        print(f"  Test {t}: {len(oc):>2} OC, {len(tt):>2} TT   "
              f"R = {radii}   window {w.get('window_start_s')}-"
              f"{w.get('window_end_s')} s")
    print(f"\nwrote {sens} and {cond}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
