# slabx 본체에 반영할 패치

> **이 저장소는 래퍼로 우회합니다. 본체는 아직 고쳐지지 않았습니다.**
>
> `pip install slabx` v1.0.4를 쓰는 사람은 **습한 대기로의 모든 극저온
> 방출에서 물 응결을 놓칩니다.** LH2 연구와 무관하게 고쳐야 할 것입니다.
>
> 우선순위대로 셋. **1번이 결함이고 나머지는 문서·경고입니다.**

---

## 패치 1 — 물 포화의 삼중점 고정 ★ **결함**

### 무엇이 문제인가

`thermo/coolprop.py` 의 `_clamp` 가 모든 포화 질의 전에 온도를 삼중점에
고정합니다. docstring이 이유를 밝힙니다:

> 포화선은 삼중점과 임계점 사이에만 존재하고, 평형 솔버는 훨씬 넓은
> 구간에서 근을 브래킷하므로 **비물리적 온도를 평가하게 된다.** 그 평가는
> 유한하고 단조이기만 하면 된다.

**방출물질에 대해서는 옳습니다** — 수소 삼중점 13.96 K, 메탄 90.7 K.

**물에 대해서는 틀립니다.** 물의 삼중점이 273.16 K이고 **모든 극저온 구름이
그 아래**입니다.

| T [K] | 현행 | IAPWS 승화 | **비** |
|---|---|---|---|
| 273.16 | 634.2 Pa | 611.7 | 1.04 |
| 260 | 634.2 | 195.8 | **3.2** |
| 240 | 634.2 | 27.27 | **23.3** |
| 200 | 634.2 | 0.1626 | **3,900** |
| 150 | 634.2 | 6.10e-6 | **1.0e8** |

**200 K 구름이 0 °C 공기만큼 수증기를 품는다고 계산합니다.**

### 영향 범위

| | |
|---|---|
| **LH2** | **결정적.** 접지·부양 판정이 부호까지 뒤집힘 |
| LNG | 0.25% (10시험 최대) — 구름이 190~253 K로 삼중점 아래인데도 물 질량분율이 작아 미미 |
| 상온 방출 | 없음 |

### 고치는 법

`slabx_lh2/water_ice.py` 의 `SublimationWater` 를 `thermo/coolprop.py` 로
옮깁니다. IAPWS 승화 곡선(Wagner, Riethmann, Feistel & Harvey 2011):

```
ln(p/p_t) = (a1 θ^b1 + a2 θ^b2 + a3 θ^b3) / θ ,   θ = T/T_t
T_t = 273.16 K,  p_t = 611.657 Pa
a = (-0.212144006e2, 0.273203819e2, -0.610598130e1)
b = ( 0.333333333e-2, 0.120666667e1, 0.170333333e1)
```

**자유 파라미터 0.** 230 K까지 참값의 3% 이내.

그리고 삼중점 아래에서는 상변화가 증기→고체이므로 **잠열을 승화열로**
바꿉니다 (융해열 333.4 kJ/kg 가산).

### 설계상 주의 셋

**① 제자리 변형 금지.** 래퍼를 돌려주고 인자는 건드리지 않아야 합니다.
같은 백엔드를 patched/unpatched 양쪽에 쓰는 음성 대조가 오염됩니다.

**② 멱등이어야 합니다.** 두 번 적용하면 융해열이 두 번 더해집니다
(2,833,122 → 3,166,522 J/kg, 조용한 12% 오차).

**③ 삼중점 위 호출은 거부.** 승화식은 그 위에서 발산하지 않고 **조용히 틀린
값**을 돌려줍니다 (300 K에서 4,566 Pa, 참값 3,537). 검출이 안 되므로
`ValueError` 를 던져야 합니다.

### 회귀 테스트

```python
def test_water_saturation_is_not_flat_below_the_triple_point():
    w = coolprop_water()
    assert w.saturation_ratio(200.0) != w.saturation_ratio(150.0)

def test_water_saturation_within_a_few_percent_of_iapws():
    w = coolprop_water()
    for T, p in ((270., 4.639e-3), (240., 2.691e-4), (200., 1.605e-6)):
        assert w.saturation_ratio(T) == pytest.approx(p, rel=0.05)

def test_dense_gas_set_moves_by_less_than_half_a_percent():
    # 열 LNG 웅덩이 시험, LFL 거리; 측정된 최대 변화는 0.25 %
    ...
```

`tests/test_water_ice.py` 26건이 그대로 옮겨집니다.

### 다른 성분은?

`N2` 삼중점 63.15 K, `O2` 54.36 K에서 같은 고정이 있습니다.
**다만 slabx는 공기 응축을 모델링하지 않으므로 질의되지 않습니다.**
`slabx_lh2/air_condensation.py` 가 개시가 **N₂ 90.3 / O₂ 88.2 mol%** 로
**수소 UFL 75% 밖**임을 보였으니, 추가할 이유도 없습니다.

**확장이 없는 성분에는 `ScopeWarning` 을 내는 것으로 충분합니다.**

---

## 패치 2 — `scope.py` 에 밀도비 경고

### 무엇이 문제인가

`VALIDATED` 가 `inv_L`, `u_ref`, `z0` 셋만 검사합니다. **구름이 주변보다
가벼운 경우에 대한 검사가 없습니다.**

야외 38시험 전건이 밀도가스라 **부력 분기가 한 번도 작동한 적이 없습니다.**
그런데 경가스 웅덩이를 넣으면 **경고 없이** 돌아가고, NASA 조건에서
`w_c/u` 가 3.68까지 갑니다 — 상승각 75°, 즉 x 전진 적분의 전제 밖입니다.

### 고치는 법

```python
VALIDATED["rho_ratio"] = Range(
    1.0, 4.5,
    "every one of the 38 validated field trials is a dense cloud; the "
    "buoyant branch of EQ 6a has never been exercised against data. "
    "Below 1.0 the cloud is lighter than ambient and the x-marching "
    "formulation may be outside its own premise -- see "
    "slabx_lh2.diagnostics.premise_summary",
    "validation/lng_pools, validation/desert_tortoise, validation/goldfish",
)
```

`check_scope` 에 `rho_ratio=` 를 추가하고, 소스 구성 시점에 호출합니다.

### 그리고 `describe_scope()` 문안 정정

현재 문안이 *"경가스 부력상승 미구현"* 이라 적고 있는데 **틀렸습니다.**
그건 `VerticalJet` 한정이고, **플룸 코어의 부력 분기는 작동 중**입니다 —
무한정 상승한다는 것이 문제이지 없는 것이 아닙니다.

---

## 패치 3 — `LIMITATIONS.md` 정정

| § | 현재 | 정정 |
|---|---|---|
| 1 | "경가스 부력상승 미구현" | **`VerticalJet` 한정.** 플룸 코어는 작동하며 상승이 무한정임을 명시 |
| 3 | 요구 조도 "200배" | **175배** |
| 신규 | — | **물 포화 삼중점 고정** (패치 1이 반영되면 삭제) |
| 신규 | — | **`w_c/u` 전제**: x 전진 적분이 풍하 이송을 가정하며, `u_crit = a q^b` 로 사전 판정 가능 |

---

## 우선순위와 근거

| | 무엇 | 왜 |
|---|---|---|
| **1** | **물 포화** | **결함입니다.** 확산 자료와 무관하게 IAPWS 대비 3,900배(200 K). LH2 사용자가 조용히 틀린 답을 받습니다 |
| 2 | `rho_ratio` 경고 | 경가스 방출이 경고 없이 전제 밖으로 갑니다 |
| 3 | 문서 정정 | 오귀속이 후속 작업을 세 번 헛돌게 했습니다 (§C7a 9번) |

**1번만이라도 먼저 내는 것을 권합니다.** 나머지는 문서이고, 1번은 결과를
바꿉니다.

---

## 반영 후 확인

```bash
pip install -e .
pytest                                  # 본체 회귀
python -c "
from slabx.thermo.coolprop import coolprop_water
w = coolprop_water()
assert w.saturation_ratio(200.) < w.saturation_ratio(240.)
print('삼중점 고정 해제 확인')
"
```

그리고 이 저장소에서:

```bash
python scripts/reproduce.py dense --json  # 밀도가스 0.25 % 재확인
pytest -m "not slow"                      # 래퍼가 멱등이므로 그대로 통과
```

**`slabx_lh2.water_ice.with_sublimation` 은 본체가 고쳐진 뒤에도
안전합니다** — 이미 승화 곡선을 쓰는 백엔드를 감싸도 값이 바뀌지 않도록
멱등으로 만들었습니다. 다만 본체 반영 후에는 **불필요해지므로 폐기 예정**
표시를 달아야 합니다.
