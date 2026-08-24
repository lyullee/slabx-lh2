# 34. 자료 핸드오프 — 이 작업이 낸 모든 것

> **세 층입니다.** 원자료 CSV 7개(3,591행), 생성값 20키, 그리고 손으로 쓴
> 손으로 쓴 목록.
>
> 세 번째가 새로 만든 것입니다. **109개 수치가 문서 본문에만 있었고**,
> 그게 철회값이 살아남는 자리입니다.
>
> **철회된 6건도 포함했습니다.** 철회는 철회된 값이 옆에 적혀 있어야
> 쓸모가 있습니다.

---

## 34.1 층 구조

```
data/*.csv            전사된 실측.        안정적, 손으로 안 고침
results/results.json  그것으로 계산.      매번 재생성, 항상 현행
data/catalogue.json   손으로 쓴 목록.     산문에만 있던 것을 회수
```

**`results.json` 은 `.gitignore` 에 있습니다** — 생성물이지 저장물이
아닙니다. `python scripts/reproduce.py --json` 으로 언제든 만듭니다.

**`catalogue.json` 은 저장합니다** — 재생성할 수 없는 것들이 들어 있습니다.
다만 재생성 가능한 항목은 `tests/test_catalogue.py` 가 `results.json` 과
매번 대조합니다.

---

## 34.2 원자료 CSV — 7개, 3,591행

| 파일 | 행 | 열 | 출처 | 내용 |
|---|---|---|---|---|
| `lh2_ffi_sensors.csv` | **826** | 13 | FFI-RAPPORT 20/03101 부록 A | 센서별 농도·온도. 아크 30·50·100 m, 높이 0/0.1/1.0/1.8 m |
| `lh2_ffi_conditions.csv` | 7 | 15 | 동, Table 2.2~2.8 | 시험 조건. **습도 없음** |
| `lh2_e35_farfield_v2.csv` | **686** | 12 | PRESLHY E3.5, DOI 10.35097/1481 | 원거리 스탠드 H₂ 농도. `saturated` 플래그 포함 |
| `lh2_e35_conditions_v2.csv` | 24 | 22 | 동 | 방출 시각 창으로 자른 기상·유량 |
| `lh2_e34_rates.csv` | **289** | 12 | PRESLHY E3.4, DOI 10.35097/1319 | 국소 증발률. `t_ground_s` 는 표면 20 K 도달 기준 |
| `lh2_e34_traces.csv` | **1,754** | 24 | 동 | 기재 내부 4·9·14·54·98 mm 및 웅덩이 위 온도 |
| `lh2_e34_summary.csv` | 5 | 15 | 동 | 시험별. `pool_established` 플래그 포함 |

**전사본이지 재배포가 아닙니다.** 보고서 자체는 포함하지 않았습니다.
`scripts/extract/` 가 원본에서 재생성합니다.

### 각 파일이 아는 함정

| 파일 | 함정 |
|---|---|
| `lh2_ffi_*` | **습도가 없습니다.** 가정값에 따라 FAC2가 0.42~0.92로 흔들립니다 |
| `lh2_e35_farfield_v2` | **4 %vol 포화.** 686행 중 57행이 천장. `saturated` 열로 거르십시오 |
| `lh2_e34_rates` | 시간이 **`Orig.Time`**(저울 시계) 기준. `Sync.Time` 보다 7.67 s 빠릅니다 |
| `lh2_e34_traces` | 깊이가 `TG<숫자>` 의 **100 − 숫자** mm. `TG02` 는 98 mm |
| `lh2_e34_summary` | `Water01` 은 `pool_established = 0` — 웅덩이가 안 생겼습니다 |

---

## 34.3 생성값 — 20키

`results/results.json`. 논문·보고서에 들어가는 숫자는 **전부 여기서** 나와야
합니다.

| 키 | 내용 |
|---|---|
| `water_saturation_error` | 삼중점 고정의 크기, 5온도 |
| `negative_control_burro8` · `negative_control_lng_pool` | 밀도가스 영향 |
| `pool_radius` | 6사례 예측/관측 |
| `ffi` | 6시험 × 9항목 — 전제비, `L_p`, LFL 구간·모델·인수적용, 판정 |
| `nasa` | 4시험 × 상승 지수(4구성) + 잔차 분해 |
| `prereg_plume_width` | P-W1/P-W2 통과 수 |
| `ground_conduction_e34` · `ground_flux_vs_literature` | E3.4 네 구간 |
| `ground_rr986` | 깊이별 α 역산, 편향 |
| `critical_wind` | 안정도 6등급 계수 + 적합 구간 |
| `air_condensation` | N₂·O₂ 개시 |
| `briggs_e35` | 17시험 `L_p` + 순위상관 2건 |
| `safety_factor` · `safety_factor_required` · `lfl_in_bracket` | |

---

## 34.4 목록 ★ 새로 만든 것

`data/catalogue.{json,csv}`. **산문에만 있던 109개 수치를 회수**했습니다.

| | 건수 |
|---|---|
| `measurement` — 관측·문헌 상수 | 22 |
| `model` — 모델 출력 | 22 |
| `comparison` — 관측 대조 | 27 |
| `diagnostic` — 진단자 | 13 |
| **`withdrawn` — 철회** | **6** |

| 등급 | 건수 | 뜻 |
|---|---|---|
| **A** | 37 | 결정론적. 모델 내부 비교 또는 기준 상관식 |
| **B** | 19 | 관측 대조, 표적이 **길이·시간·이진 사건** |
| **C** | 11 | 관측 대조, 표적이 농도이거나 시험 수가 적거나 미측정 입력 의존 |
| **–** | 23 | 주장이 아님. 조건·입력·계보 |

각 레코드에 `key · value · unit · grade · kind · source · doc · note`.

### 철회 6건 — 인용 금지, 보관 필수

| 키 | 값 | 무엇이 대체했나 |
|---|---|---|
| `negctl.lng_pool.max_change.withdrawn` | **0.37 %** | 생성값 0.25 % |
| `ground.flux_vs_literature.withdrawn` | **0.97** | 단일 비가 없음. 60~800 s에서 2.48~0.68 |
| `rise.exponent.withdrawn_0869` | **0.869** | 물 수정 후 1.047 |
| `lfl.safety_factor_required.withdrawn` | **1.23** | 격자 보간 후 1.114 |
| `ucrit.withdrawn` | **2.5 q^0.15** | 안정도별 재적합. D는 2.674 q^0.135 |
| `provenance.nasa.detachment.withdrawn` | **20 m** | 원본은 지면 이동 50~100 m. **다른 양** |

> **키에 `withdrawn` 이 들어 있습니다.** 옛 초안에서 값을 발견한 사람이
> 키로 검색하면 상태가 바로 보입니다.

---

## 34.5 실패도 자료입니다 — 회수한 것

지시대로 **실패 결과를 전부 넣었습니다.** 그게 가장 값어치 있는 부분일 수
있습니다.

| 키 | 무엇 |
|---|---|
| `orientation.slabx_ratio` 1.03 대 `chen_rodi_ratio` 1.00 | **기준 상관식도 방출 방향을 구별 못 합니다.** slabx 고유 결함이 아님 |
| `orientation.pool_source_ratio` 13,684 | 기각된 `ImpingingJet`. 관측 2.69가 **네 자릿수로 감싸임** |
| `orientation.misreading` | **문서 18을 거꾸로 읽었음** — 하향은 이미 맞고 수평이 2.6배 낮음 |
| `rise.P_W1_pass` 1/4 | 두 보정을 다 켜도 기준 미달 |
| `rise.residual.dlnh_dlnz` 0.23~0.49 | **깊이가 상승에 결합돼 있지 않음.** 필요 1.0 |
| `ground.e34.full.sand02/03` 0.25·0.31 | 모래에서 4배 어긋남 |
| `ground.rr986.temperature_bias` +37.4 K | **콘크리트 물성이 실험 간에 안 옮겨감** |
| `briggs.threshold_transfers` False | 임계 20이 척도를 못 넘음 |
| `repeatability.ffi.peak_height_flips` True | **연직 최대 높이는 판정 변수가 될 수 없음** |
| `provenance.ffi.humidity` | 미보고. 그 위에서 모델을 판정했던 것이 세 번 |

---

## 34.6 그림

`figures/applicability.{png,pdf}` — **논문 Fig. 2.**

곡선은 선별식 `u_crit = a q^b`(안정도 A~F), 마커의 채움은 **측정된
`max w_c/u`**. 둘이 갈리는 것이 그림의 내용입니다 — 35시험 중 27건 일치,
불일치 8건은 전부 운동량 제트입니다.

`scripts/figure_applicability.py` 로 재생성.

---

## 34.7 오염 방지 — 무엇이 지키고 있나

| 검사 | 건수 | 무엇 |
|---|---|---|
| `test_catalogue.py` | **25** | 목록이 `results.json` 과 일치하는가, CSV 행·열이 온전한가, 철회 레코드가 등급을 안 달았는가 |
| `test_consistency.py` | 15 | 철회값이 코드·문서에서 **주장**되지 않는가, 모든 문서가 색인에 있는가 |
| 나머지 | 121 | 모듈·통합 |
| **합계** | **161** | |

**CSV 행·열 수를 고정했습니다** — 잘린 파일이 조용히 통과하지 않습니다.

```
lh2_ffi_sensors        826 x 13
lh2_e35_farfield_v2    686 x 12
lh2_e34_rates          289 x 12
lh2_e34_traces        1754 x 24
```

---

## 34.8 다시 만드는 법

```bash
pip install -e ".[test,extract]"

# 원자료 → CSV  (원 보고서·엑셀이 있어야 함)
python scripts/extract/parse_ffi.py      <FFI PDF>
python scripts/extract/extract_e35_v2.py <E3.5 폴더>
python scripts/extract/extract_e34.py    <E3.4 폴더>

# CSV → 생성값
python scripts/reproduce.py --json

# 목록
python scripts/build_dataset.py

# 그림
python scripts/figure_applicability.py

# 전부 검증
pytest
```

**`extract_e34.py` 는 여섯 엑셀 중 다섯만 씁니다** — `Concrete01` 은
저울 자료가 없고, `Gravel` 셋은 다공성 때문에 무게신호를 못 쓴다고 보고서가
명시합니다.

---

## 34.9 쓰기 전에 읽을 것

**숫자를 인용하기 전에 순서대로:**

1. **`data/catalogue.csv`** — 그 값이 무엇이고 어떤 등급인가
2. **`results/results.json`** — 재생성 가능하면 여기 값을 쓴다
3. **문서 26** — 무엇으로 주장할 수 있고 무엇으로 못 하는가

**문서 24는 초기 종합이고 정정 이력이 있습니다.** 거기서 옮겨 적지
마십시오.

### 절대 쓰면 안 되는 표현 — 문서 26 §26.8

| 쓰지 말 것 | 대신 |
|---|---|
| "검증되었다" | "관측이 묶은 구간 안" |
| "SLAB을 LH2로 확장했다" | "결함 하나를 고치고 결합 하나를 추가" |
| "검증된 안전율 1.25" | "최소 필요 1.114, 1.25는 반올림한 여유, 독립 검증 안 됨" |
| "리프트오프를 예측한다" | "리프트오프 경향을 정렬한다" |
| "NASA 20 m 분리" | 등고선 판독과 지면이동 50~100 m를 **분리 표기** |
| "방출 방향을 구별 못 한다" | "수평 고운동량 제트 최대값을 과소예측" |
| "지반 모델이 검증됐다" | "물성이 실험마다 3~5배 다르다" |

---

## 34.10 남은 자료 공백

| | 무엇 | 영향 |
|---|---|---|
| **DNV GL 853182 Rev.2** | FFI 습도 | 농도 통계를 못 씀. **LFL 거리 판정은 무관** |
| NASA 원 출처 [12] | 연직 LFL 53·27·65·9 m | 2차 인용이라 등급 C |
| URAHFREP 수치 | 헬륨 풍동 연직 프로파일 | 그림뿐. 결합 기구 독립 검증이 막힘 |
| Zhang Test 2 | 지속시간 | 유일한 고풍속 사례(3.0 m/s)를 못 씀 |
| E3.4 Gravel 3건 | — | **필요 없음.** 무게신호 사용 불가 |

**어느 것도 지금 결론을 바꾸지 않습니다.**
