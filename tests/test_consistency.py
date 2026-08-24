"""
Consistency between the documents, the code, and the generated numbers.

Why this exists
---------------
Thirteen numbers in this project have been corrected after first being
written down, and three of those corrections were caught only because someone
went looking. A retracted figure that survives in one live document is worse
than no document: it will be quoted.

These tests are cheap and they run on every commit. They check two things:

**Retracted values do not appear as claims.** `docs/retired/` and
`docs/prereg/` are exempt: the first is the archive and the second is a record
of what was believed at registration time, which must not be edited to agree
with a later correction. A retracted number may appear in
a sentence that retracts it -- that is the record and it must stay -- but not
in a table, a summary line, or a docstring where a reader would take it as
current. The tests look for the value in a live context and allow it in a
retracting one.

**The code agrees with `results.json`.** Docstrings quote numbers, and a
docstring is where a stale figure hides longest, because nothing recomputes it.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
#: Documents that are current. `retired/` is the record and is exempt.
#: `prereg/` above the RESULTS line is immutable by construction -- a
#: registration records what was believed when it was written, and editing it
#: to match a later correction would destroy the only thing it is for. Its
#: ADDENDUM sections carry the corrections instead.
LIVE_DOCS = sorted(
    [p for p in (ROOT / "docs").glob("*.md")]
    + [p for p in (ROOT / "README.md",) if p.exists()]
)
CODE = sorted((ROOT / "slabx_lh2").glob("*.py")) + \
    sorted((ROOT / "scripts").glob("*.py"))

#: Words that mark a sentence as retracting rather than asserting.
RETRACTION_MARKERS = (
    "철회", "정정", "대체", "오류", "superseded", "withdraw", "retract",
    "corrected", "no longer", "earlier", "was ", "adopted 아님",
    "not adopted", "not an adopted", "이었습니다", "적었습니다", "적고 있",
    "라 적", "고 판단", "금지", "주장 불가", "must not", "do not quote",
    "ADDENDUM", "추록", "경고", "caveat", "withdrawn", "결과가 나빠",
    "우연", "산물", "자기 오류", "교훈", "이력", "유리한 지점",
)

#: value pattern -> what replaced it, for the failure message
RETRACTED = {
    r"97\s?%": "no single ratio; see docs/28 and docs/29",
    r"0\.37\s?%": "0.25 % (results.json, negative_control_lng_pool)",
    r"2\.5\s?q\^0\.15": "CRITICAL_WIND_FIT; class D is 2.674 q^0.135",
    r"인수\s+1\.23\b": "1.114 (results.json, safety_factor_required)",
    r"free parameters?:?\s*zero": "E is a choice; see docs/28 section 28.4",
    r"자유 파라미터가 진짜 0": "E is a choice; see docs/28 section 28.4",
    r"\b45\.75\b": "43.56 m (results.json, ffi.5.lfl_model_m); the FFI Test 5 "
                   "unignited release is 240 s, not 120",
    r"4 *% 이내|to within 4 %": "6 % (3.0, 3.1, 5.7 and 5.9)",
}


#: A retracted value is quoted, not asserted, when it sits inside quotation
#: marks, backticks or a blockquote -- that is how the record of a correction
#: reads, and how a test pattern is named in prose.
_QUOTED = re.compile(r'[*`"\u201c\u201d]')


def _lines_with(path: Path, pattern: str):
    """
    Lines that **assert** `pattern`, dropping those that retract or quote it.

    A correction is written across a few lines -- the value on one, the word
    "withdrawn" on the next -- so the surrounding two lines count as context.
    """
    lines = path.read_text(encoding="utf-8").splitlines()
    out = []
    for n, line in enumerate(lines, 1):
        if not re.search(pattern, line, re.I):
            continue
        context = " ".join(lines[max(0, n - 3):n + 2])
        if any(m in context for m in RETRACTION_MARKERS):
            continue
        if line.lstrip().startswith(">") or _QUOTED.search(line):
            continue
        out.append((n, line.strip()))
    return out


@pytest.mark.parametrize("pattern,replacement", list(RETRACTED.items()))
def test_retracted_values_are_not_asserted_in_the_code(pattern, replacement):
    """
    A stale number in a docstring is the worst case: nothing recomputes it and
    it reads as authoritative.
    """
    bad = [(p, n, t) for p in CODE for n, t in _lines_with(p, pattern)]
    assert not bad, "\n".join(
        [f"retracted value matching {pattern!r}; use {replacement}"]
        + [f"  {p.relative_to(ROOT)}:{n}: {t}" for p, n, t in bad])


@pytest.mark.parametrize("pattern,replacement", list(RETRACTED.items()))
def test_retracted_values_are_not_asserted_in_live_documents(pattern,
                                                             replacement):
    bad = [(p, n, t) for p in LIVE_DOCS for n, t in _lines_with(p, pattern)]
    assert not bad, "\n".join(
        [f"retracted value matching {pattern!r}; use {replacement}",
         "(a line that retracts the value is allowed; one that asserts it "
         "is not)"]
        + [f"  {p.relative_to(ROOT)}:{n}: {t}" for p, n, t in bad])


#: The public release carries a subset of the documents and no index of them,
#: so these two checks belong to the working tree.
_INDEX = ROOT / "docs" / "README.md"
has_index = pytest.mark.skipif(
    not _INDEX.exists(),
    reason="no docs/README.md; this is the public subset, which ships a "
           "chosen set of documents rather than the full history")


@has_index
def test_every_live_document_is_indexed():
    """A document nobody links to is a document nobody corrects."""
    index = _INDEX.read_text(encoding="utf-8")
    missing = [p.name for p in (ROOT / "docs").glob("*.md")
               if p.name != "README.md" and p.name not in index]
    assert not missing, f"not in docs/README.md: {missing}"


@has_index
def test_retired_documents_are_not_linked_as_current():
    """`retired/` may be referenced, but not from the live reading order."""
    index = _INDEX.read_text(encoding="utf-8")
    head = index.split("## 은퇴한 문서")[0]
    stale = [p.name for p in (ROOT / "docs" / "retired").glob("*.md")
             if p.name in head]
    assert not stale, f"retired document in the live section: {stale}"


@pytest.mark.slow
@pytest.mark.skipif(
    not (ROOT / "data" / "lh2_ffi_sensors.csv").exists(),
    reason="reproduce.py compares against measurements that are not "
           "distributed; see data/SOURCES.md")
def test_the_generated_numbers_still_match_the_headline_claims():
    """
    Regenerate `results.json` and check the figures the documents lean on.

    Loose tolerances on purpose: this catches a value that has moved, not one
    that has drifted in the last digit.
    """
    out = ROOT / "results" / "results.json"
    subprocess.run([sys.executable, str(ROOT / "scripts" / "reproduce.py"),
                    "water", "--json"], cwd=ROOT, check=True,
                   capture_output=True)
    d = json.loads(out.read_text())

    assert d["negative_control_lng_pool"]["max_change_pct"] < 0.5
    assert d["lfl_in_bracket"] == 5
    assert 1.05 < d["safety_factor_required"] < 1.20
    assert d["safety_factor"] == 1.25
    assert 0.9 < d["pool_radius"]["median_ratio"] < 1.2
    # the defect's size, or 1 where slabx has fixed it upstream (1.0.6+)
    from slabx.thermo.coolprop import coolprop_water
    from slabx_lh2.water_ice import already_corrected
    ratio = d["water_saturation_error"]["200.00"]["ratio"]
    if already_corrected(coolprop_water()):
        assert ratio == pytest.approx(1.0, abs=0.05)
    else:
        assert ratio > 1000
    pw = d["prereg_plume_width"]
    assert pw["P_W1_pass_width_only"] == 0
    assert pw["P_W1_pass_with_drag"] == 1
    assert max(pw["residual_errors_pct"]) < 6.0
    assert d["briggs_e35"]["rank_corr_Lp_wind"] < -0.7
    assert not d["air_condensation"]["N2"]["inside_flammable_range"]
    a, b = (d["critical_wind"]["coefficients"]["D"][k] for k in ("a", "b"))
    assert 2.6 < a < 2.8 and 0.12 < b < 0.15


#: Every script a reader might run, with the arguments that make them cheap.
#: `benchmark_runtime` and `ablation_2x2` are slow, so they get the smallest
#: settings that still exercise the code path.
PUBLIC_SCRIPTS = [
    ("reproduce.py", ["--json"]),
    ("applicability_all.py", []),
    ("figure_applicability.py", []),
    ("rr986_ground.py", []),
    ("effects_comparison.py", []),
    ("ablation_2x2.py", []),
    ("benchmark_runtime.py", ["--repeats", "2", "--batch-repeats", "1",
                              "--skip-cold"]),
]


@pytest.mark.slow
@pytest.mark.parametrize("script,args", PUBLIC_SCRIPTS,
                         ids=[s for s, _ in PUBLIC_SCRIPTS])
def test_every_script_runs_without_the_measurements(script, args):
    """
    A public install has the conditions and not the measurements, and the
    documentation says every model output still reproduces.

    **Two scripts did not, and both failed the same way** -- the code that
    assembled the results handled a missing bracket and the code that printed
    it did not. `reproduce.py` was caught in review; `ablation_2x2.py` only
    when this test was widened from one script to all of them.
    """
    import os
    env = dict(os.environ, SLABX_LH2_DATA="/nonexistent-on-purpose",
               MPLBACKEND="Agg")
    p = subprocess.run([sys.executable, str(ROOT / "scripts" / script),
                        *args], cwd=ROOT, env=env, capture_output=True,
                       text=True, timeout=1800)
    assert p.returncode == 0, (
        f"scripts/{script} failed without the measurements:\n"
        f"{p.stderr[-1500:]}")


def _catalogue_is_filtered() -> bool:
    import json as _j
    p = ROOT / "data" / "catalogue.json"
    return p.exists() and bool(_j.loads(p.read_text(encoding="utf-8"))
                               .get("note"))


@pytest.mark.slow
def test_build_dataset_refuses_to_regenerate_a_filtered_catalogue():
    """
    In the public release `data/catalogue.json` is the filtered copy, with
    the measured records removed. Regenerating it there would silently put
    them back, so `build_dataset.py` refuses and says why.

    **This is the one script that should fail in the public tree**, which is
    why it is not in `PUBLIC_SCRIPTS`: a script that exits non-zero on
    purpose and one that crashes look the same to a loop over return codes.
    """
    import os
    env = dict(os.environ, SLABX_LH2_DATA="/nonexistent-on-purpose")
    p = subprocess.run([sys.executable,
                        str(ROOT / "scripts" / "build_dataset.py")],
                       cwd=ROOT, env=env, capture_output=True, text=True,
                       timeout=600)
    if _catalogue_is_filtered():
        assert p.returncode != 0
        assert "filtered copy" in (p.stdout + p.stderr), (
            "it refused, but without saying why")
    else:
        assert p.returncode == 0, p.stderr[-800:]


@pytest.mark.slow
def test_reproduce_completes_without_the_measurements():
    """
    The public claim is that a fresh install reproduces every model output
    and skips only the comparisons against measurement.

    **That was false until this test existed.** `collect()` handled the
    missing brackets and the printed sections did not, so
    `reproduce.py --json` died with a TypeError on a public install while
    the documentation said it would not.
    """
    import os
    env = dict(os.environ, SLABX_LH2_DATA="/nonexistent-on-purpose")
    p = subprocess.run([sys.executable, str(ROOT / "scripts" /
                                            "reproduce.py"), "--json"],
                       cwd=ROOT, env=env, capture_output=True, text=True)
    assert p.returncode == 0, (
        f"reproduce.py failed without the measurements:\n"
        f"{p.stderr[-1500:]}")
    out = p.stdout
    assert "not installed" in out, (
        "the LFL section should say the brackets are missing, not omit them")
    assert "3900" in out or "3.900" in out or "1.0" in out, \
        "the water section should still print"
    d = json.loads((ROOT / "results" / "results.json").read_text())
    assert d["measurements_installed"] is False
    assert d["safety_factor_required"] is None
    # the model outputs are all still there
    assert d["ffi"]["4"]["lfl_model_m"] > 0
    assert "critical_wind" in d and "nasa" in d


class TestCountsAreNotHardCoded:
    """
    Counts that change whenever anything is added must not be written into
    prose.

    Test totals, catalogue sizes and file counts were written into six
    documents and went stale in six different places. **A number nobody
    recomputes is a number that will be wrong**, and unlike a physical
    result there is nothing to check it against.
    """

    #: (pattern, what to do instead)
    VOLATILE = {
        r"목록 \d{2,3}건": "let build_dataset.py print it",
        r"catalogue\.csv +\d{2,3}건": "let build_dataset.py print it",
        r"\*\*\d{3} 통과(, \d+ skip)?\*\*": "say 'all pass' and let pytest count",
        r"\*\*\d{2,3}개\*\* *\|": "let make_public.py print it",
    }

    @pytest.mark.parametrize("pattern,advice", list(VOLATILE.items()))
    def test_volatile_counts_are_absent(self, pattern, advice):
        bad = []
        for p in LIVE_DOCS:
            for n, line in enumerate(p.read_text(encoding="utf-8")
                                     .splitlines(), 1):
                if re.search(pattern, line):
                    if any(m in line for m in RETRACTION_MARKERS):
                        continue
                    bad.append(f"  {p.relative_to(ROOT)}:{n}: {line.strip()}")
        assert not bad, "\n".join(
            [f"hard-coded count matching {pattern!r}; {advice}"] + bad)


class TestExternalDocumentReferences:
    """
    Documents 01 to 17 belong to the upstream dense-gas validation and are
    not in this repository. A reader who follows a reference and finds
    nothing has been misled, so the three documents that cite them carry a
    note saying where they live.
    """

    CITING = ["18_LH2_APPLICABILITY.md", "22_BENTOVER_PREMISE.md",
              "24_LH2_SUMMARY.md"]

    @pytest.mark.parametrize("name", CITING)
    def test_they_say_the_referenced_documents_are_elsewhere(self, name):
        p = ROOT / "docs" / name
        if not p.exists():
            pytest.skip(f"{name} is not in this subset")
        assert "문서 01~17" in p.read_text(encoding="utf-8"), (
            f"{name} cites documents 01-17 without saying they are in the "
            f"slabx repository, not this one")

    def test_no_other_document_cites_them_silently(self):
        pattern = re.compile(r"문서 (0[1-9]|1[0-7])\b")
        bad = []
        for p in LIVE_DOCS:
            if p.name in self.CITING:
                continue
            text = p.read_text(encoding="utf-8")
            if pattern.search(text) and "문서 01~17" not in text:
                bad.append(p.name)
        assert not bad, f"cite documents 01-17 without the note: {bad}"
