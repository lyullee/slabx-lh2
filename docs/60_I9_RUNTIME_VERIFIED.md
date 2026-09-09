# 60. i9-12900K 계산시간 최종 검증 — slabx-lh2 0.1.3

> **계산시간 최종 정본 — 2026-08-29.** 과거 0.1.2 집계값과 문서 53의
> 수치는 이력입니다. 논문·표·초록·카탈로그는 이 문서의 0.1.3 값을
> 사용합니다.

## 60.1 실행과 계보

- CPU: 12th Gen Intel Core i9-12900K, 16 physical cores, 24 logical processors
- OS: Microsoft Windows 11 Pro 10.0.26200
- Python 3.12.14; slabx 1.0.6; slabx-lh2 0.1.3
- NumPy 2.5.2; CoolProp 8.0.0
- package hash: `f02763515da7e4ac`, 현재 정본과 일치
- 명령: repeats 100, batch repeats 30, cold repeats 20, warm-up 10,
  35-case sequential repeats 30, parallel 0
- 정본: `paper_results/runtime_i9_0.1.3/`

내부 `SHA256SUMS.txt`는 raw, summary, environment와 validation 네 파일에
대해 4/4 일치했습니다. 380개 raw 행에서 summary를 독립 재계산한 결과 모든
통계의 최대 차이는 0이었습니다. 실패는 0건이고 p99/p50은 1.015–1.092입니다.

## 60.2 최종 통계

| Case and path | n | p50 (ms) | p95 (ms) | p99 (ms) | p99/p50 |
|---|---:|---:|---:|---:|---:|
| FFI Test 4, warm end-to-end | 100 | 63.009 | **65.649** | 68.061 | 1.080 |
| FFI Test 6, warm end-to-end | 100 | 112.640 | **117.070** | 118.649 | 1.053 |
| NASA Test 6, warm end-to-end (OUT_OF_SCOPE) | 100 | 139.204 | **149.077** | 151.994 | 1.092 |
| Six-FFI-case warm batch | 30 | 430.547 | **444.903** | 445.237 | 1.034 |
| 35-scenario sequential batch | 30 | 4140.734 | **4196.882** | 4203.282 | 1.015 |
| FFI Test 4, cold process start | 20 | 1487.061 | **1526.257** | 1569.977 | 1.056 |

35개 순차 계산의 최대 반복값도 4.205 s로 5초 센서 갱신주기 안에 들어갑니다.
이는 동일 하드웨어·동일 문제의 CFD 속도비가 아니라 이 구현과 이 호스트의
운영 지연시간 근거입니다.

## 60.3 논문 교체값

- Abstract: warm single-case p95 **65.6–149.1 ms**; 35 cases **4.20 s**
- Results prose: 65.6, 117.1, 149.1, 444.9, 4196.9, 1526.3 ms
- Conclusions: single-case p95 **65.6–149.1 ms**; six-case **444.9 ms**;
  35-case **4.197 s**; cold start **1.526 s**
- Table 5: §60.2 값을 소수점 한 자리로 반올림

이전 73.2 ms, 124.7 ms, 153.3 ms, 460.9 ms, 4413.1 ms와 1520.6 ms는
0.1.2 이력값이며 최종 원고에서 사용하지 않습니다.

