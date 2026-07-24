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

### 군집 비행 (Boids)
- `swarm_drone.py` — `SwarmDrone` 클래스 (핵심 로직)
- `simulate.py` — 군집 시뮬레이션 데모 (콘솔 지표 출력)
- `visualize_swarm.py` — 군집 비행을 3D 애니메이션(GIF)으로 렌더링
- `test_swarm_drone.py` — 동작 검증 테스트

### 소방 대응 (역할 기반)
- `firefighting_drone.py` — `FirefightingDrone` 클래스: 열화상 탐지, 화점 진압,
  화염 회피 A* 탈출 경로 안내(2D/3D). 소화탄 소진 시 SUPPRESSOR→GUIDE 자율 전환.
- `camera.py` — `CameraModel`: 핀홀 카메라 + 드론 자세로 픽셀→월드 좌표 변환.
- `firefighting_demo.py` — 탐지→진압→안내→(픽셀변환/3D경로) 통합 시나리오 데모
- `visualize_firefighting.py` — 진압·탈출 시나리오를 2D 애니메이션(GIF)으로 렌더링
- `visualize_firefighting_3d.py` — 3D 비행 진압 + 다층(층간) 탈출을 3D 애니메이션으로 렌더링
- `test_firefighting_drone.py` — 동작 검증 테스트

### 통합 임무 (스웜 + 소방 협력)
- `integrated_mission.py` — 여러 드론이 **동시에 협력**하는 통합 시나리오.
  전 기체가 Boids 편대(`SwarmDrone`)로 현장에 접근한 뒤, 역할(`FirefightingDrone`)에
  따라 진압/호위/선회를 분담한다. 두 클래스에 로직을 **위임(delegate)** 하여 재사용.
- `visualize_integrated.py` — 통합 임무를 역할별 색상으로 3D 애니메이션 렌더링
- `test_integrated_mission.py` — 무충돌·편대 수렴·역할 전환·경로 안전성 검증

### 표준 절차 기반 5대 시나리오 (행동 지침 적용)
「소방공무원 현장 소방활동 안전관리에 관한 규정」(소방청훈령 제119호, 2020)의
현장 안전관리 원칙을 **드론 편대의 활동 지침**으로 변형해 코드에 적용했다.

- `firefighting_doctrine.py` — 규정 조항을 드론 지침으로 코드화(근거 조항 포함).
  안전최우선(제3조14호), 위험요인 관측·전파(제7조), 역할 식별(제7조④),
  대원 관리체계(제24조), 위험 시 중지·대피(제25조), 사고대원 우선(제25조③),
  신속동료구조팀(제24조②) 등. 위험도별 안전 이격/대피 판단 등 **행동에 영향**을 주는 헬퍼 포함.
- `drone_icons.py` — 역할을 형태로 보여주는 벡터 아이콘(제7조④ 식별 취지):
  진압=물방울, 정찰=눈, 안내=화살표, 경계=방패, 안전=경고삼각, 구조/구급=십자,
  지휘=별, 유해물=육각형.
- `scenarios.py` — 5대 케이스 시뮬레이션(이동/충돌회피는 기존 클래스 재사용):

  | 케이스 | 흐름 | 핵심 근거 |
  |--------|------|-----------|
  | ① 인명구조 `rescue` | 수색→발견→응급→호위 탈출 | 제7·24·25조 |
  | ② 화재 초기대응 `suppress` | 사이즈업→초동 진압→잔불정리 | 제3·7조 |
  | ③ 플래시오버 경계·대피 `flashover` | 작업→위험징후→활동중지·대피→인원확인 | **제25조** |
  | ④ 대원 조난·신속동료구조 `mayday` | 진압→MAYDAY→RIT 전개→구출 | **제24·25조** |
  | ⑤ 유해가스 누출 `hazmat` | 플룸 매핑→경계구역→풍상 대피/구조 | **제7·26조** |

- `visualize_scenarios.py` — 5개 시나리오를 한 렌더러로 GIF화(한글 지침 패널 포함):
  역할 아이콘, 실시간 내레이션, **적용 중인 지침과 근거 조항**, 역할 범례, 진행 타임라인.
- `test_scenarios.py` — 무충돌, 아이콘/지침 정합성, 대피·RIT·플룸 등 단계 발생 검증.

#### 역할 (DroneRole)

| 역할 | 임무 |
|------|------|
| `SCOUT` | 수색 및 경로 탐색 |
| `SUPPRESSOR` | 화점 초동 진압(소화탄 투하로 시간 확보) |
| `GUIDE` | 요구조자 탈출 안내 및 보호 |

#### 원본 소방 드론 프로토타입 대비 개선점

1. **`cv2` 하드 의존 제거** — 미설치·미사용이던 `import cv2`가 모듈 임포트 자체를
   실패시키던 문제 해결(있으면 사용, 없어도 동작).
2. **A* 실제 구현** — 고정 웨이포인트만 반환하던 스텁을 8방향 화염 회피 A* 로 교체.
3. **임계값 기반 탐지** — 항상 `True`를 반환하던 탐지를 열화상 온도 임계값 기반으로 구현.
4. **이동 로직 추가** — 화점 접근 로직이 없어 `dist < 3m` 투하 조건이 성립 불가능하던 문제 해결.
5. **방어 로직 보강** — 소화탄 개수 음수 방지 및 역할 전환 안전 처리.

#### 좌표계·3D 확장

앞선 버전의 두 한계(2D 평면 한정, 픽셀 좌표를 월드 좌표로 그대로 사용)를 해소했다.

- **픽셀→월드 변환 (`camera.py`)** — 핀홀 카메라 모델과 드론 자세(위치·요)로
  탐지 픽셀에서 나온 광선을 지면 평면과 교차시켜 실제 월드 좌표를 복원한다.
  카메라를 지정하지 않으면 기존처럼 픽셀 좌표를 반환하여 하위 호환을 유지한다.

  ```python
  from camera import CameraModel
  cam = CameraModel.from_fov(image_shape=(480, 640), hfov_deg=90.0)
  drone = FirefightingDrone("scout", camera=cam, yaw=0.0)
  drone.pos = np.array([100.0, 60.0, 40.0])  # 고도 40m
  result = drone.process_thermal_and_vision(thermal_frame, ground_z=0.0)
  # result["fire"], result["survivor"] 는 월드 좌표
  ```

- **3D A* (다층 건물)** — `generate_escape_path`에 3D hazard map(shape `(Z, H, W)`)을
  넘기면 층 간 이동(계단/개구부)을 포함한 6방향 3D A* 로 탈출 경로를 계산한다.
  2D map(shape `(H, W)`)을 넘기면 기존 8방향 2D A* 로 동작한다.

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
# 군집 비행
python3 simulate.py               # 시뮬레이션 데모(콘솔)
python3 visualize_swarm.py        # 3D 애니메이션 렌더링 -> swarm.gif
python3 test_swarm_drone.py       # 테스트
# 소방 대응
python3 firefighting_demo.py      # 시나리오 데모(콘솔)
python3 visualize_firefighting.py # 2D 시나리오 애니메이션 -> firefighting.gif
python3 visualize_firefighting_3d.py # 3D 비행·층간 탈출 -> firefighting_3d.gif
python3 test_firefighting_drone.py  # 테스트
# 통합 임무 (스웜 + 소방)
python3 integrated_mission.py     # 통합 시나리오 콘솔 요약
python3 visualize_integrated.py   # 통합 임무 3D 애니메이션 -> integrated_mission.gif
python3 test_integrated_mission.py  # 테스트
# 표준 절차 기반 5대 시나리오
python3 scenarios.py              # 5개 시나리오 콘솔 요약
python3 visualize_scenarios.py    # 5개 GIF 모두 생성(scenario_*.gif)
python3 visualize_scenarios.py rescue mayday  # 특정 시나리오만
python3 test_scenarios.py         # 테스트
```
