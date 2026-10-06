# PSEP seven-test research reproducibility record

Status: research capsule frozen on 2026-10-06; no production qualification.

The 210-record paper calculation used a selected v1162 route for Tests 1, 2,
3, 5 and 7 and a selected v1165 route for Tests 4 and 6. Its executable
environment used `slabx` 1.0.6, an editable `slabx-lh2` 0.1.4 source tree and
`lh2poolx` 0.1.2. The public `slabx-lh2` 0.2.0 and `slabx` 1.0.8 releases
document later software lineage; installing them does not recreate this
research field.

The corresponding author retains a private ZIP capsule identified by SHA-256
`baf1d0daa882124232e70ab01e9f328396082780e3f9a676a30991293c9daa59`
(52,601,464 bytes). It contains 1,867 individually hashed files, including
the exact research scripts, declared input ledger, selected model fields,
sensor comparison, 36-case reproducibility chain and all 182 declared audit
outputs. After the settled source-clock state, 35 deterministic cases and 175
declared files were byte-stable. Seven files constitute a complete
point-in-time workspace inventory. The ZIP and each included file passed
hash verification on 2026-10-06.

The capsule contains the FFI report and measurement-derived tables, so the ZIP
is not posted here. The original report can be obtained from [FFI's publisher
page](https://www.ffi.no/en/publications-archive/large-scale-leakage-of-liquid-hydrogen-lh2-tests-related-to-bunkering-and-maritime-use-of-liquid-hydrogen).
The exact report copy used in the audit had SHA-256
`d500b61da23a44043648d71e06ee7d061e7b46671af5ecc8fc370cf9c9a23a4a`.
The report permits citation with attribution; that statement is not treated
here as permission to redistribute the PDF or its transcribed measurement
tables. Requests for research code or derived records should be addressed to
the corresponding author and assessed under the originating organisation's
terms.

The paper's Supplementary Data S1--S3 are held with the private capsule while
their redistribution rights are reviewed. Public software provenance and
the scoped seven-test results are described in
[`61_FFI_7_TEST_RESEARCH_MODEL.md`](61_FFI_7_TEST_RESEARCH_MODEL.md).
