# 40. 공개 배포 — 무엇을 올리고 무엇을 안 올리나

> **문제는 CSV가 아닙니다.** 관측값이 **코드에 하드코딩**돼 있어서
> `data/` 를 빼도 공개됩니다.
>
> `slabx_lh2/lfl.py` docstring, `scripts/reproduce.py`,
> `tests/test_integration.py` 에 FFI 아크 최대값과 시험 조건이 그대로
> 들어 있습니다.
>
> **분리는 파일 단위가 아니라 값 단위여야 합니다.**

---

## 40.1 무엇이 어디에 있나

`grep "17.20\|21.00\|0.828"` 으로 찾은 것:

| 파일 | 무엇 |
|---|---|
| `slabx_lh2/lfl.py` | docstring의 FFI 6시험 표 (유출률·풍속·구간·모델값) |
| `scripts/reproduce.py` | `FFI` 딕셔너리 — 조건 + **아크 최대값 3개씩** |
| `scripts/ablation_2x2.py` | 동 |
| `scripts/applicability_all.py` | 조건만 |
| `scripts/benchmark_runtime.py` | 조건만 |
| `scripts/figure_applicability.py` | 조건 + 전제비 |
| `tests/test_integration.py` | 조건 + **아크 최대값** |

**아크 최대값이 실제 관측치**입니다. 조건(유출률·풍속·온도)은 보고서 표에
있는 실험 설정이고 성격이 다릅니다.

---

## 40.2 분리 기준

| 구분 | 무엇 | 공개 |
|---|---|---|
| **A. 모델 코드** | `slabx_lh2/*.py` 의 물리 | **✅** |
| **B. 실험 조건** | 유출률·풍속·온도·노즐·지속시간 | **✅** — 재현에 필요하고, 원 보고서 표에 있는 설정값 |
| **C. 관측 결과** | 아크 농도, 웅덩이 반경, 온도 궤적 | **❌** — 원 보고서의 결과물 |
| **D. 모델 출력** | LFL 거리, `w_c/u`, `L_p`, 지수 | **✅** — 이 작업이 계산한 것 |
| **E. 판정** | 구간 안/밖, 통과 수 | **✅** — 다만 C 없이는 재현 불가 |

> **B와 C의 구별이 핵심입니다.** 조건을 공개하면 **누구나 모델을 돌려
> D를 재현**할 수 있고, C가 필요한 것은 **E를 재현할 때뿐**입니다.
>
> 그리고 C는 **원 보고서에서 각자 얻을 수 있습니다** — FFI-RAPPORT
> 20/03101은 공개, PRESLHY는 CC BY-SA 4.0 DOI, RR986은 HSE 공개입니다.

---

## 40.3 공개본 구조

```
slabx-lh2/                       ← GitHub · PyPI · Zenodo
  slabx_lh2/                     모델 코드 (A)
    water_ice.py   plume_width.py   pool.py
    diagnostics.py lfl.py           vertical_drag.py
    air_condensation.py
    trials/                        ← 신규
      __init__.py                  조건 로더 (B)
      ffi.py         E3.5·NASA·Zhang·FFI 조건만
      observations.py              스텁 + 취득 안내 (C 자리)
  tests/
    test_water_ice.py              전부 통과 (관측 불요)
    test_modules.py                전부 통과
    test_integration.py            **관측 필요분은 skip**
  scripts/
    reproduce.py                   D는 재현, E는 관측 있을 때만
    benchmark_runtime.py           전부 재현
    figure_applicability.py        전부 재현
    applicability_all.py           전부 재현
    ablation_2x2.py                D는 재현
    extract/                       원 보고서 → CSV 생성기 (전부 공개)
  docs/
    README.md  23  22  26  34      결함·전제·등급·자료 계보
    PATCH_upstream_slabx.md
    prereg/                        사전등록 10건
  data/
    SOURCES.md                     ← 신규. 출처·취득법만
    catalogue.csv                  ← 관측 파생값 제외판
  README.md  LICENSE  pyproject.toml
```

**비공개본에만:**

```
  data/lh2_*.csv                   전사본 (C)
  slabx_lh2/trials/observations.py 실제 값이 들어간 판
  docs/18 24 25 27~33 35~39        작업 이력·정정·비교
  paper_results/                   투고 산출물
```

---

## 40.4 `data/SOURCES.md` 가 대신합니다

관측값 대신 **어디서 어떻게 얻는지**를 적습니다.

| 자료 | 출처 | 접근 | 무엇을 뽑나 |
|---|---|---|---|
| FFI 야외 6시험 | FFI-RAPPORT 20/03101 부록 A | 공개 PDF | 아크 30·50·100 m 최대 농도 |
| PRESLHY E3.5 | DOI 10.35097/1481 | CC BY-SA 4.0 | 원거리 스탠드 농도 |
| PRESLHY E3.4 | DOI 10.35097/1319 | 등록 후 다운로드 | 질량·기재온도 |
| HSE RR986 | HSE 공개 | 공개 PDF | Figure 15 온도, 웅덩이 치수 |
| NASA | Witcofski & Chirivella 1984 | *Int. J. Hydrogen Energy* 9, 425 | Table 1·3·4 |
| Zhang 2024 | DOI 10.3390/app14093645 | 오픈액세스 | Table 1 조건 |

**그리고 `scripts/extract/` 를 함께 공개합니다** — 받은 원본에서 CSV를
만드는 코드입니다. 값은 안 주고 **만드는 법을 줍니다.**

---

## 40.5 관측이 없으면 무엇이 안 되나

| | 관측 없이 | 관측 있으면 |
|---|---|---|
| 물 결함 크기 (3,900배) | **✅** | ✅ |
| 밀도가스 음성대조 | **✅** | ✅ |
| `w_c/u`, `u_crit`, 혼동행렬 | **✅** | ✅ |
| 지연시간 벤치마크 | **✅** | ✅ |
| 2×2 절제 (LFL 값) | **✅** | ✅ |
| 적용범위 지도 | **✅** | ✅ |
| **LFL 구간 판정 (5/6)** | **❌** | ✅ |
| **웅덩이 반경 대조** | **❌** | ✅ |
| **RR986 온도 대조** | **❌** | ✅ |

> **논문의 두 기둥은 관측 없이 재현됩니다.** 물 결함과 적용범위 진단자
> 둘 다 모델 내부 비교 또는 기준 상관식 대조입니다 (등급 A).
>
> **관측이 필요한 것은 등급 B~C 뿐**이고, 그건 원 보고서를 받으면
> 됩니다.

---

## 40.6 테스트 처리

관측이 필요한 테스트는 **삭제하지 않고 skip** 합니다:

```python
observations = pytest.importorskip(
    "slabx_lh2.trials.observations",
    reason="measured arc concentrations are not distributed; see "
           "data/SOURCES.md for how to obtain them")
```

**공개본에서 몇 건이 skip 되는지가 보입니다.** 지웠으면 안 보입니다.

---

## 40.7 절차

1. `slabx_lh2/trials/` 를 만들어 **조건(B)과 관측(C)을 분리**
2. `lfl.py` docstring 표에서 **관측 열을 빼고** `SOURCES.md` 로 넘김
3. 스크립트·테스트가 `trials` 를 임포트하게 고침
4. `data/SOURCES.md` 작성
5. `catalogue.csv` 에서 `kind == "measurement"` 중 **관측 파생분 제외**
6. 공개본 트리 생성 → GitHub → PyPI → Zenodo
7. **비공개본은 별도 저장소**(private) 또는 로컬 보관

**5번이 까다롭습니다** — 목록에서 관측 파생이 어느 것인지 이미
`kind` 와 `grade` 로 구분돼 있으니 필터가 됩니다.

---

## 40.8 라이선스·귀속

| | |
|---|---|
| 코드 | **MIT** — `slabx` 와 동일 |
| 저작권 | **확인 필요.** 국가 R&D 산출물이라 협약서 규정이 있을 수 있음 |
| `slabx` 의존 | `slabx>=1.0.4`, MIT |
| 인용 | `CITATION.cff` 에 Zenodo DOI |

**`slabx` 본체 물 수정을 먼저 릴리스하는 것을 권합니다.** 논문이 결함을
지적하는데 그 코드가 안 고쳐져 있으면 심사자가 묻습니다.
