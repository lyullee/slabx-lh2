# 41. 배포 절차 — GitHub · PyPI · Zenodo

> **공개본은 `scripts/make_public.py` 가 만듭니다.** 손으로 파일을 고르지
> 마십시오 — 관측값이 코드에 하드코딩돼 있었고, 그 검사가 스크립트 안에
> 있습니다.

---

## 41.1 확인된 것

| | |
|---|---|
| 공개본 파일 | `make_public.py` 가 출력합니다 |
| 공개본 테스트 (관측 없음) | **전부 통과, 관측 비교만 skip** — 수는 slabx 버전에 따라 다릅니다 |
| 비공개본 테스트 | 전부 통과 |
| wheel 빌드 | 0.1.3 후보 공개 트리에서 새로 생성·검사 |
| 관측값 잔류 검사 | ✅ 0건 |
| 목록 필터 | `make_public.py` 가 제외 건수를 출력합니다 |

---

## 41.2 순서

### ① 먼저 — 상류 `slabx` 상태 확인

상류 `slabx`는 v1.0.5에서 승화압을, v1.0.6에서 융해열을 반영했습니다.
`slabx-lh2`는 압력곡선과 융해열을 각각 거동 검사하므로 1.0.4·1.0.5를
보완하고 1.0.6에는 중복 적용하지 않습니다. 릴리스 검증 환경은
`slabx 1.0.6`으로 고정하고 실제 설치 버전을 로그에 남깁니다.

### ② 공개본 생성

```bash
cd slabx-lh2
python scripts/make_public.py --out ../slabx-lh2-public-0.1.3-candidate
```

**관측값이 남아 있으면 쓰기를 거부합니다.** `--force` 는 쓰지 마십시오 —
거부되면 그 값을 `trials/observations.py` 로 옮기라는 뜻입니다.

### ③ 검증

```bash
cd ../slabx-lh2-public-0.1.3-candidate
python -m venv .venv && .venv/bin/pip install -e ".[test,figures]"
SLABX_LH2_DATA=/nonexistent .venv/bin/pytest -q
```

**skip 이 여러 건 나와야 합니다.** 0건이면 관측이 새어 들어간 것이고,
실패가 있으면 skip 표시가 빠진 것입니다. **정확한 수는 설치된 `slabx`
버전에 따라 다릅니다** — 1.0.6 에서는 결함을 못박는 테스트가 추가로
skip 됩니다.

### ④ ZIP과 wheel 생성·내부 검사

검증 과정은 `results/`, `paper_results/`, 캐시를 다시 만들 수 있습니다.
`package_release.py`는 공개 ZIP에서 이를 다시 제외하지만, 생성 후 ZIP 내부
목록도 확인합니다.

```bash
# 비공개 정본 디렉터리에서 실행
python scripts/package_release.py --version 0.1.3 \
  --public-tree ../slabx-lh2-public-0.1.3-candidate \
  --out ../release/0.1.3-candidate

# 공개 트리에서 wheel과 sdist 생성
cd ../slabx-lh2-public-0.1.3-candidate
python -m build
python -m twine check dist/*
```

공개 ZIP에는 `data/lh2_*.csv`, `paper_results/`, `results/`, `figures/`,
`same_test_flacs.py`, 캐시와 빌드 디렉터리가 없어야 합니다. 새 해시를 만든
뒤 이전 후보와 섞지 않습니다.

### ⑤ GitHub

```bash
git init && git add -A
git commit -m "slabx-lh2 0.1.3"
git remote add origin https://github.com/lyullee/slabx-lh2.git
git push -u origin main
```

`.github/workflows/tests.yml` 이 Python 3.10·3.12 에서 자동으로 돕니다.

### ⑥ Zenodo

**GitHub 릴리스 전에 Zenodo 연동을 켜십시오.** 순서가 반대면 그 릴리스는
DOI를 못 받습니다.

1. Zenodo → GitHub → `lyullee/slabx-lh2` 토글 ON
2. GitHub 에서 태그 `v0.1.3` 릴리스
3. Zenodo 가 concept DOI 와 version DOI 를 발급

> **`slabx` 에서 겪은 문제를 반복하지 마십시오.** version DOI 를 추적
> 파일에 적으면 항상 **직전 릴리스**를 가리킵니다. `CITATION.cff`에는
> **concept DOI**를 유지하고, 논문의 Methods/Data availability에는 실제
> 계산에 사용한 **0.1.3 version DOI**를 릴리스 후 넣습니다.

### ⑦ PyPI

```bash
python -m build
python -m twine upload --repository testpypi dist/*
pip install --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple slabx-lh2
python -c "import slabx_lh2; print(slabx_lh2.__version__)"
python -m twine upload dist/*
```

**TestPyPI 를 건너뛰지 마십시오** — `slabx>=1.0.4` 의존이 실제로 풀리는지
확인해야 합니다.

---

## 41.3 공개본에 들어간 것

```
slabx_lh2/          모델 코드 + trials (조건 35건)
tests/              회귀검사. 관측 필요분은 skip
scripts/            9개 + extract/ 4개
docs/               22 23 26 40 41 54 + PATCH + prereg
data/               SOURCES.md + catalogue (103건)
README.md  LICENSE  CITATION.cff  pyproject.toml
```

**사전등록 원문과 추록이 갑니다.** 방법론이고, 왜 여러 모듈이 기각됐는지를
설명하며, 폭 결합이 왜 기본 꺼짐인지 알고 싶은 사람이 찾을 수 있어야
합니다.

**추출 스크립트가 갑니다.** 값 대신 **만드는 법**을 주는 것이 이 방식의
전부입니다.

## 41.4 비공개본에만 남는 것

| | 왜 |
|---|---|
| `data/lh2_*.csv` | 타 기관 결과물의 전사본 |
| `data/lh2_*.csv`를 읽어 제공되는 실제 관측 배열 | 동 |
| `docs/34_DATA_HANDOFF.md` | 관측 수치를 포함한 내부 자료 인계 |
| 문서 18·24·25·27~33·35~39 | 작업 이력. 정정 13건과 기각 사유 |
| `paper_results/` | 투고 산출물 |

**비공개본을 private 저장소로 따로 두십시오.** 로컬에만 두면 이력이
사라집니다.

---

## 41.5 배포 전 확인 넷

**① 저작권자.** `LICENSE` 와 `pyproject.toml` 에 KGS 를 넣었는데,
**국가 R&D 산출물이라 협약서 규정이 있을 수 있습니다.** RS-2025-02311196
협약서를 확인하십시오.

**② FFI 전사본.** 공개본에서 뺐으므로 문제없습니다. 다만 **논문 부록에
넣을 계획이면 FFI 에 확인**이 필요합니다.

**③ `slabx` 버전 고정.** 논문 결과를 만든 버전을 `run_manifest.txt`에
적었습니다. 배포 후 의존성을 바꾸지 마십시오.

**④ 지연시간 원자료.** 2026-08-29에 동일 i9-12900K에서 0.1.3을 다시 실행해
380행 raw CSV, summary, environment, validation, SHA-256 manifest를
`paper_results/runtime_i9_0.1.3/`에 보존했습니다. 내부 manifest와 raw 재집계는
모두 일치했고 실패는 0건입니다. 이 디렉터리를 포함한 새 후보의 해시를 만든
뒤에만 0.1.3 version DOI를 발급하십시오. 기존 `paper_results/runtime_raw.csv`는
Linux VM smoke run이므로 계속 i9 근거로 사용하지 않습니다.

---

## 41.6 이후

**GitHub/Zenodo 릴리스 후 발급된 0.1.3 version DOI를 논문에 넣습니다.**
그 시점에 배포 태그에서 `results.json`을 다시 생성해 `paper_results/`를
갱신하고, 결과·ZIP·wheel의 SHA-256으로 배포본과 논문 수치를 묶으십시오.
