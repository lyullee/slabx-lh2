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
    assert d["prereg_plume_width"]["P_W1_pass"] == 0
    assert d["briggs_e35"]["rank_corr_Lp_wind"] < -0.7
    assert not d["air_condensation"]["N2"]["inside_flammable_range"]
    a, b = (d["critical_wind"]["coefficients"]["D"][k] for k in ("a", "b"))
    assert 2.6 < a < 2.8 and 0.12 < b < 0.15
