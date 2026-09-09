# 54. 배포 직전 재감사 정정본

> 작성일: 2026-08-28  
> 대상: `slabx-lh2` 0.1.3 후보본  
> **논문·README·DOI 배포자료에는 이 문서를 53보다 우선 적용합니다.**

이번 감사에서는 계산식을 새로 맞추지 않았습니다. 비교군의 정의, 관측자료와
모델 단면의 대응, 습도 결론의 강도, 상류 버전 호환성을 다시 확인했습니다.
그 결과 논문에 직접 영향을 주는 해석 네 건과 실제 호환성 버그 한 건을
수정했습니다.

## 54.1 확정된 변경

### 물 보정은 압력과 융해열을 따로 판정

`slabx`의 상류 반영은 두 단계였습니다.

| 버전 | 삼중점 이하 포화압 | 융해열 333.4 kJ/kg |
|---|---|---|
| 1.0.4 | 없음 | 없음 |
| 1.0.5 | 있음 | 없음 |
| 1.0.6 | 있음 | 있음 |

기존 `already_corrected()`는 압력만 보고 1.0.5를 완전 보정으로 오인할 수
있었습니다. 이제 `correction_state()`가 두 거동을 독립적으로 검사하고,
`with_sublimation()`은 빠진 부분만 적용합니다. 1.0.6에서는 원본 객체를
그대로 반환하므로 융해열 이중 가산도 일어나지 않습니다.

### 음성대조와 교차유체 효과를 분리

기존 결과는 LNG에서 물 처리와 수소 전용 폭 보정을 함께 바꿔 놓고 이를
음성대조라고 불렀습니다. 이제 질문을 둘로 분리했습니다.

| 질문 | 비교 | 결과 | 해석 |
|---|---|---|---|
| 수소 전용 폭 보정이 LNG에 새는가 | 같은 물 처리, 폭 보정만 off/on | 10/10 bit-identical, 최대 0.0 % | 음성대조 통과 |
| 삼중점 이하 물 처리가 LNG에도 중요한가 | 의도적으로 복원한 clamp 대 corrected | 최대 13.417 %, Burro 8 13.54 % | 교차유체 절제시험; pass/fail 아님 |

두 번째 비교의 clamp는 과거 거동을 재구성한 시험용 arm입니다. 따라서
“현재 slabx 1.0.6에 13% 결함이 있다” 또는 “음성대조가 13% 실패했다”고
쓰면 안 됩니다. 허용되는 결론은 **삼중점 이하 물 처리의 영향이 LH2에만
국한되지 않는다는 계산상 증거**입니다.

### 습도 결론은 두 문장으로 분리

`paper_results/humidity_sensitivity.json`의 확정 플래그는 다음과 같습니다.

- `horizontal_underprediction_at_every_rh = true`
- `orientation_separated_at_every_rh = false`

즉, 수평 두 시험의 과소예측은 RH 0--100 % 전 범위에서 유지되지만,
RH 100 %에서는 하향 시험 하나도 과소예측이어서 “방향이 모든 습도에서
깔끔하게 분리된다”는 강한 주장은 성립하지 않습니다. 또한 Tests 1과 6의
LFL 거리는 전 범위에서 각각 약 54%, 57% 움직이며, 구간 내 판정은
RH <= 50 %에서 3/6, RH >= 75 %에서 5/6입니다.

따라서 5/6와 안전계수 결과를 쓸 때는 **RH 75 % 가정**을 함께 써야 합니다.

### 센서 아크로 단면 평균을 만들 수 없음

30 m 센서는 고정된 `x = 30 m` 평면의 횡방향 배열이 아니라 반경 30 m의
극좌표 아크입니다. 풍향 좌표계로 회전하면:

| 시험 | 센서의 하류방향 x 범위 |
|---|---|
| FFI 4 | 18.88--29.84 m |
| FFI 6 | 10.26--29.97 m |

기존 0.34--0.41은 이 아크를 고정-x 단면처럼 적분했고 시간평균을 시간최대와
나누었습니다. 공간 단면의 peak-to-bulk 비로 해석할 수 없으므로 철회합니다.
센서 상단 1.8 m보다 모델 구름 깊이도 크기 때문에 연직 평균 역시 식별되지
않습니다. `sensor_audit.csv`의 세 식별 플래그는 모두 0입니다.

### 유입량 비교는 조건부 시나리오만 유지

모델 쪽 총 유량 `2 * R_flux`는 정의가 명확합니다. 관측 쪽 단면평균은 위
센서 배열로 식별되지 않습니다. 따라서 다음 값은 측정된 오차나 불확실성
구간이 아닙니다.

| 시험 | bulk = 0.5 peak, illustrative | bulk = peak, extreme |
|---|---:|---:|
| FFI 4 | 2.076 | 4.547 |
| FFI 6 | 2.479 | 5.560 |

`bulk = 0.5 peak`는 검증된 Gaussian 형상이 아닙니다. `bulk = peak`는 관측
유량을 최소화하고 모델/관측 비를 최대화하므로 **하한이 아닙니다**. 논문에서
필요하면 “두 명시적 가정 아래의 조건부 진단값”으로만 제시합니다.

## 54.2 논문에 사용 가능한 주장

| 사용 가능 | 사용 금지 |
|---|---|
| RH 전 범위에서 수평 두 시험의 근거리 농도 과소예측이 유지됨 | 모든 습도에서 수평/하향 결과가 완전히 분리됨 |
| RH 75 %에서 LFL 구간 5/6, 필요 배율 1.1138 | LFL 거리가 습도에 둔감하거나 불변 |
| 수소 전용 폭 gate는 LNG 10건에서 bit-identical | LNG 물 효과를 음성대조 실패로 표현 |
| 물 처리의 LNG 영향은 deliberate cross-fluid ablation | slabx 1.0.6이 여전히 13% 결함이라고 표현 |
| 센서로 고정-x 단면평균을 식별할 수 없음 | 0.34--0.41을 측정된 peak-to-bulk로 사용 |
| 2.076--5.560은 조건부 시나리오 | 5.560을 hard lower bound로 사용 |
| 단일 FFI 4 p95 65.649 ms, 35건 순차 p95 4.197 s | CFD보다 빠르다는 정량 비교로 사용 |

계산시간은 해당 i9-12900K, Python 3.12.14 환경의 자체 지연시간입니다. 다른
코드와 같은 하드웨어·같은 문제 정의로 비교한 값이 아니므로 CFD 우월성
비교가 아니라 **5초 센서 갱신 주기 안에 35개 시나리오가 들어간다**는
운영 적합성 근거로만 씁니다.

이 조건은 2026-08-29 재측정으로 해소됐습니다. 최종 0.1.3 i9 원자료는
`paper_results/runtime_i9_0.1.3/`에 있고, 380행·실패 0건·p99/p50
1.015–1.092입니다. 최상위 `paper_results/runtime_raw.csv`는 여전히 별도의
Linux VM smoke run이므로 인용하지 않습니다. 최종 인용값은 문서 60과
`runtime_reference_summary.csv`를 사용합니다.

## 54.3 정본과 자동검사

정본 소스는 `source/slabx-lh2/`입니다. 주요 생성물은 다음과 같습니다.

- `results/results.json` 및 `paper_results/results.json`
- `paper_results/humidity_sensitivity.{csv,json}`
- `paper_results/sensor_audit.csv`
- `paper_results/entrainment_uncertainty.csv`
- `paper_results/negative_controls.csv`
- `paper_results/cross_fluid_water_effect.csv`
- `data/catalogue.{csv,json}`와 동일한 `paper_results/catalogue.{csv,json}`

공개 ZIP은 재배포 권한을 분리하기 위해 측정 CSV와 `paper_results/`를
포함하지 않습니다. 공개본에서는 해당 비교가 명시적으로 skip되고, 모델
출력·음성대조·적용성 진단은 그대로 실행됩니다.

`tests/test_release_audit.py`가 측정자료 포함 여부, 5/6 판정, 습도 플래그,
센서 좌표, 조건부 유입 시나리오, 음성대조/교차유체 분리를 고정합니다.

## 54.4 버전과 DOI

이미 공개된 0.1.2 아카이브의 내용과 이번 수정본은 같지 않습니다. 따라서
수정본은 **0.1.3**으로 분리했습니다.

- concept DOI: `10.5281/zenodo.22075011`
- 0.1.2 version DOI: 기존 공개본을 가리키므로 0.1.3에 재사용 금지
- 0.1.3 version DOI: 새 릴리스 후 발급된 값을 Methods/Data availability에
  추가. `CITATION.cff`는 릴리스 전체를 추적하는 concept DOI를 유지

릴리스 전에는 전체 테스트, 공개본의 측정자료 제외 테스트, 결과 해시와
배포 ZIP 내부 파일 목록을 다시 확인해야 합니다.

## 54.5 0.1.3 실행 검증 완료

2026-08-28에 정본과 공개본을 분리해 다음을 실행했습니다.

| 대상 | 결과 |
|---|---|
| 정본 fast | 194 passed, 6 skipped, 49 deselected |
| 정본 slow | 49 passed, 200 deselected |
| 정본 합계 | **243 passed, 6 skipped, 0 failed** |
| 공개본 fast, 측정자료 없음 | 164 passed, 36 skipped, 49 deselected |
| 공개본 slow, 측정자료 없음 | **36 passed, 13 skipped, 200 deselected** |

공개본의 13 skip은 재배포하지 않는 FFI/PRESLHY/RR986 측정 CSV가 없어서
발생하는 의도된 결과입니다. 공개 코드 경로의 느린 스크립트와 수치 검사는
모두 통과했습니다. 로그는 `release/public_pytest_slow_0.1.3.xml`에
보관했습니다.

## 54.6 2026-08-29 방법론·공개범위 수정 후 재검증

문서 58의 명명·방법론 수정과 임계풍속 계수 재생성 뒤, 이전 후보를
덮어쓰지 않고 새 공개 트리와 깨끗한 비공개 ZIP 복제본을 검사했습니다.

| 대상 | 결과 |
|---|---|
| 정본 fast | 195 passed, 6 skipped, 50 deselected |
| 비공개 ZIP 복제본 slow | 50 passed, 201 deselected |
| 정본 합계 | **245 passed, 6 skipped, 0 failed** |
| 공개본 fast, 측정자료 없음 | 164 passed, 37 skipped, 50 deselected |
| 공개본 slow, 측정자료 없음 | **37 passed, 13 skipped, 201 deselected** |

공개 slow 검사는 `paper_results/critical_wind_fit.json` 없이 24개 임계풍속
경계를 다시 계산하여 A--F 계수를 확인했습니다. 공개본에는 순수 모델
재현기 `fit_critical_wind.py`가 들어가지만, 측정값과 공개 FLACS 결과를
전사한 `same_test_flacs.py`는 비공개에만 남습니다. 공개 ZIP 포장기는
테스트가 다시 만든 `paper_results/`, `results/`, `figures/`와 캐시도 경로
수준에서 제외합니다.

로그는 `paper_results/pytest_*_0.1.3_20260829.xml`과
`release/public_pytest_slow_0.1.3-20260829.xml`에 보관했습니다.
