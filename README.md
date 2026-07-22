# Swarm Drone Behavior

드론 군집(swarm)을 위한 Reynolds Boids 기반 자율 비행 로직입니다. 각 드론은
주변 이웃의 위치·속도만 보고 스스로 가속도를 정하는 **분산(decentralized)**
방식으로 동작하며, 중앙 제어기가 없습니다.

## 규칙 (Boids 3 rules)

| 규칙 | 설명 | 기본 가중치 |
|------|------|-------------|
| 분리 (Separation) | 안전거리(`safe_dist`)보다 가까운 이웃을 밀어내 충돌 방지 | `1.5` |
| 정렬 (Alignment)  | 이웃의 평균 속도에 맞춤 | `0.2` |
| 결합 (Cohesion)   | 이웃 무게중심 방향으로 이동 | `0.1` |

## 구성

- `swarm_drone.py` — `SwarmDrone` 클래스 (핵심 로직)
- `simulate.py` — 군집 시뮬레이션 데모
- `test_swarm_drone.py` — 동작 검증 테스트

## 원본 코드 대비 개선점

초기 프로토타입에서 다음 문제들을 수정했습니다.

1. **속력 제한 (`max_speed`)** — 가속도가 무제한 누적되어 발산하던 문제 해결.
2. **조향력 제한 (`max_force`)** — 한 스텝에 가할 수 있는 가속 크기를 제한.
3. **시간 간격 (`dt`)** — `dt=1` 가정을 없애고 프레임 레이트와 독립적으로 적분.
4. **인식 반경 (`perception`)** — 너무 먼 드론이 무게중심을 왜곡하지 않도록 제한.
5. **동일 위치 예외 처리** — 두 드론이 정확히 같은 좌표일 때 발생하던 0으로 나눗셈/NaN 제거.
6. **순수 함수 분리** — `compute_acceleration()`이 상태를 바꾸지 않고 가속도만
   반환하도록 하여 테스트와 재사용이 쉬워짐.

## 사용법

```python
from swarm_drone import SwarmDrone

a = SwarmDrone("a", position=[0, 0, 0], velocity=[1, 0, 0])
b = SwarmDrone("b", position=[3, 0, 0], velocity=[0, 1, 0])

# a가 이웃 b를 보고 한 스텝(dt=0.1초) 비행
a.update_swarm_behavior([b], safe_dist=5.0, dt=0.1)
print(a)
```

## 실행

```bash
pip install numpy
python3 simulate.py          # 시뮬레이션 데모
python3 test_swarm_drone.py  # 테스트
```
