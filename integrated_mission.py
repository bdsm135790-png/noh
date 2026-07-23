"""스웜 + 소방 통합 임무 시나리오.

여러 대의 드론이 **동시에 협력**하는 하나의 임무를 시뮬레이션한다.
기존 두 모듈을 그대로 재사용한다.

  - 편대 비행(이동/충돌 회피): ``swarm_drone.SwarmDrone`` 의 Boids 규칙
  - 역할 임무(탐지/진압/안내):   ``firefighting_drone.FirefightingDrone``

각 드론은 ``MissionDrone`` 으로, 위 두 동작을 상황(phase)과 역할(role)에 따라
번갈아 사용한다. MissionDrone 은 두 클래스의 로직을 새로 구현하지 않고,
필요한 순간에 해당 클래스 인스턴스에 위임(delegate)한다.

임무 흐름
---------
  1) 접근(Approach): 전 기체가 Boids 편대로 화재 현장 상공까지 함께 이동.
     서로 부딪히지 않으면서 목표점으로 이동(migration)한다.
  2) 대응(On-scene): SCOUT가 화점·요구조자를 탐지하면
       - SUPPRESSOR : 화점으로 하강·접근해 소화탄 투하 → 소진 시 GUIDE 전환
       - GUIDE      : 화염 회피 A* 경로로 요구조자를 비상구까지 호위
       - PATROL/SCOUT : 현장 상공에서 편대 선회(loiter) 유지

실행:
    python3 integrated_mission.py       # 콘솔 요약
"""

import numpy as np

from swarm_drone import SwarmDrone
from firefighting_drone import FirefightingDrone, DroneRole


# 임무 지형(월드 좌표, m) -------------------------------------------------
GOAL_APPROACH = np.array([40.0, 40.0, 8.0])   # 현장 상공 집결점
LOITER = np.array([40.0, 40.0, 9.0])          # 선회 대기 지점
FIRE = np.array([41.0, 39.0, 2.0])            # 화점(3D)
SURVIVOR = np.array([36.0, 44.0, 0.0])        # 요구조자(지상)
EXIT = np.array([50.0, 50.0, 0.0])            # 비상구


def make_scene_hazard(shape=(60, 60)):
    """현장 지상 격자. 화점 주변에 통행 불가(화염) 벽을 세운다."""
    hazard = np.zeros(shape)
    hazard[34:46, 40:43] = 1  # 요구조자와 비상구 사이를 막는 화염 벽
    return hazard


class MissionDrone:
    """편대 비행 + 역할 임무를 함께 수행하는 드론.

    두 기존 클래스에 로직을 위임한다:
      - 편대 가속도: SwarmDrone.compute_acceleration
      - 화점 접근/투하: FirefightingDrone.execute_suppression_routine
      - 탈출 경로: FirefightingDrone.generate_escape_path
    """

    def __init__(self, drone_id, role, pos, vel, payload=2,
                 max_speed=6.0, max_force=2.0, perception=25.0):
        self.id = drone_id
        self.role = role
        self.pos = np.array(pos, dtype=float)
        self.vel = np.array(vel, dtype=float)
        self.payload = int(payload)
        self.max_speed = float(max_speed)
        self.max_force = float(max_force)
        self.perception = float(perception)
        # GUIDE 호위 상태.
        self.escape_path = None
        self.escape_idx = 0
        # SUPPRESSOR가 화점을 공격하는 상대 위치(기체끼리 겹치지 않도록).
        self.attack_offset = np.zeros(3)

    # -- 편대 비행(Boids) : SwarmDrone에 위임 ---------------------------
    def _swarm_body(self):
        return SwarmDrone(self.id, self.pos, self.vel,
                          max_speed=self.max_speed, max_force=self.max_force,
                          perception=self.perception)

    def flock_step(self, neighbors, goal, dt=0.5, safe_dist=4.0, goal_w=0.7):
        """이웃과 편대를 유지하며 goal 방향으로 한 스텝 이동한다."""
        body = self._swarm_body()
        # compute_acceleration은 other.pos/other.vel만 읽으므로 MissionDrone을
        # 그대로 이웃으로 넘길 수 있다.
        acc = body.compute_acceleration(neighbors, safe_dist=safe_dist)
        # 목표점으로의 이동(migration) 성분을 더한다.
        to_goal = np.asarray(goal, dtype=float) - self.pos
        d = np.linalg.norm(to_goal)
        if d > 1e-9:
            acc = acc + (to_goal / d) * goal_w * self.max_force
        acc = body._limit(acc, self.max_force)
        self.vel = body._limit(self.vel + acc * dt, self.max_speed)
        self.pos = self.pos + self.vel * dt

    # -- 진압 : FirefightingDrone에 위임 -------------------------------
    def suppress_step(self, fire, drop_range=3.0):
        """화점으로 한 스텝 접근하고 사거리면 투하한다. 투하 시 True."""
        ff = FirefightingDrone(self.id, role=self.role, payload=self.payload,
                               max_speed=self.max_speed)
        ff.pos = self.pos.copy()
        ff.fire_hotspot_pos = np.asarray(fire, dtype=float)
        dropped = ff.execute_suppression_routine(drop_range=drop_range)
        # 결과 상태를 되돌려 받는다(자율 역할 전환 포함).
        self.pos, self.vel = ff.pos.copy(), ff.vel.copy()
        self.payload, self.role = ff.payload_extinguisher, ff.role
        return dropped

    # -- 탈출 경로 계산 : FirefightingDrone에 위임 ----------------------
    def plan_escape(self, hazard, survivor_pos, exit_pos, cell_size=1.0):
        ff = FirefightingDrone(self.id, role=DroneRole.GUIDE)
        ff.target_survivor_pos = np.asarray(survivor_pos, dtype=float)
        path = ff.generate_escape_path(hazard, exit_pos, cell_size=cell_size)
        self.escape_path = np.array(path) if path is not None else None
        self.escape_idx = 0
        return self.escape_path

    def escort_step(self, dt=1.0, arrive=1.2):
        """탈출 경로의 현재 웨이포인트를 향해 호위 비행한다.

        요구조자 위치(지상, z=0)를 반환한다. 경로 끝이면 마지막 지점 유지.
        """
        if self.escape_path is None or len(self.escape_path) == 0:
            return None
        target = self.escape_path[self.escape_idx]
        # GUIDE는 요구조자 위 상공을 호위하도록 z를 살짝 띄운다.
        ff = FirefightingDrone(self.id, role=self.role, max_speed=self.max_speed)
        ff.pos = self.pos.copy()
        ff.move_toward(target + np.array([0.0, 0.0, 2.0]), dt=dt)
        self.pos, self.vel = ff.pos.copy(), ff.vel.copy()
        if np.linalg.norm(self.pos[:2] - target[:2]) < arrive:
            self.escape_idx = min(self.escape_idx + 1, len(self.escape_path) - 1)
        return target  # 요구조자는 이 지점(지상)에 있다고 본다


def build_fleet():
    """역할을 배분한 편대를 무작위 위치에서 생성한다."""
    rng = np.random.default_rng(7)
    roster = ([DroneRole.SCOUT]
              + [DroneRole.SUPPRESSOR] * 2
              + [DroneRole.GUIDE]
              + ["PATROL"] * 4)
    fleet = []
    supp_seen = 0
    for i, role in enumerate(roster):
        pos = rng.uniform(-6, 10, size=3) + np.array([0, 0, 8.0])
        vel = rng.uniform(-1, 1, size=3)
        payload = 2 if role == DroneRole.SUPPRESSOR else 0
        drone = MissionDrone(f"{role[:4]}-{i}", role, pos, vel, payload=payload)
        if role == DroneRole.SUPPRESSOR:
            # 진압 드론끼리 화점을 서로 다른 방향에서 공략하도록 표적을 분산.
            angle = supp_seen * (2 * np.pi / 2) + np.pi / 4
            drone.attack_offset = np.array([2.5 * np.cos(angle),
                                            2.5 * np.sin(angle), 0.0])
            supp_seen += 1
        fleet.append(drone)
    return fleet


def min_pairwise_distance(fleet):
    pts = np.array([d.pos for d in fleet])
    best = np.inf
    for i in range(len(pts)):
        for j in range(i + 1, len(pts)):
            best = min(best, np.linalg.norm(pts[i] - pts[j]))
    return best


def run_mission(approach_steps=40, onscene_steps=60, dt=0.5, record=True):
    """통합 임무를 시뮬레이션한다.

    Returns
    -------
    dict
        시각화/검증용 궤적과 메타데이터.
    """
    fleet = build_fleet()
    hazard = make_scene_hazard()

    # 시각화용 기록.
    positions = {d.id: [d.pos.copy()] for d in fleet}
    roles = {d.id: [d.role] for d in fleet}
    survivor_track = [None]
    events = []
    min_dist_series = [min_pairwise_distance(fleet)]

    detected = False
    escape_planned = False
    scout = next(d for d in fleet if d.role == DroneRole.SCOUT)

    total = approach_steps + onscene_steps
    for step in range(1, total + 1):
        on_scene = step > approach_steps

        # 1) 탐지: 접근 단계 종료 시 SCOUT가 현장을 탐지한다.
        if on_scene and not detected:
            thermal = np.full((20, 20), 22.0)
            thermal[3:6, 14:17] = 520.0    # 화점
            thermal[12:15, 3:6] = 36.5     # 요구조자
            ff_scout = FirefightingDrone(scout.id, role=DroneRole.SCOUT)
            ff_scout.pos = scout.pos.copy()
            result = ff_scout.process_thermal_and_vision(thermal)
            events.append((step, f"SCOUT 탐지: fire={result['fire']}, "
                                 f"survivor={result['survivor']}"))
            detected = True

        # 2) GUIDE 경로 계획(탐지 직후 1회).
        if detected and not escape_planned:
            guide = next((d for d in fleet if d.role == DroneRole.GUIDE), None)
            if guide is not None:
                path = guide.plan_escape(hazard, SURVIVOR, EXIT)
                if path is not None:
                    events.append((step, f"GUIDE 탈출 경로 {len(path)}개 웨이포인트"))
                escape_planned = True

        survivor_pos = None
        for d in fleet:
            neighbors = [o for o in fleet if o is not d]

            if not on_scene:
                # 접근: 전원 편대 비행으로 집결점 이동.
                d.flock_step(neighbors, GOAL_APPROACH, dt=dt)
            else:
                if d.role == DroneRole.SUPPRESSOR:
                    dropped = d.suppress_step(FIRE + d.attack_offset)
                    if dropped:
                        events.append((step, f"{d.id} 소화탄 투하 → 잔여 {d.payload}"))
                        if d.payload == 0:
                            events.append((step, f"{d.id} 소진 → GUIDE 전환"))
                elif d.role == DroneRole.GUIDE and d.escape_path is not None:
                    survivor_pos = d.escort_step(dt=1.0)
                else:
                    # PATROL / SCOUT / (전환된 GUIDE) : 현장 상공 선회.
                    d.flock_step(neighbors, LOITER, dt=dt, goal_w=0.4)

        if record:
            for d in fleet:
                positions[d.id].append(d.pos.copy())
                roles[d.id].append(d.role)
            survivor_track.append(survivor_pos.copy()
                                  if survivor_pos is not None else None)
            min_dist_series.append(min_pairwise_distance(fleet))

    return {
        "fleet": fleet,
        "positions": {k: np.array(v) for k, v in positions.items()},
        "roles": roles,
        "survivor_track": survivor_track,
        "events": events,
        "min_dist_series": np.array(min_dist_series),
        "approach_steps": approach_steps,
        "hazard": hazard,
        "landmarks": {"fire": FIRE, "survivor": SURVIVOR, "exit": EXIT,
                      "approach": GOAL_APPROACH},
    }


def main():
    res = run_mission()
    print("=== 통합 임무(스웜 + 소방) 요약 ===")
    print(f"편대 {len(res['fleet'])}기, "
          f"접근 {res['approach_steps']} 스텝 후 현장 대응")
    print(f"전 구간 최소 기체 간격: {res['min_dist_series'].min():.2f} m "
          f"(>0 이면 무충돌)")
    print("\n주요 이벤트:")
    for step, txt in res["events"]:
        print(f"  [step {step:>3}] {txt}")
    print("\n최종 역할 분포:")
    final = {}
    for d in res["fleet"]:
        final[d.role] = final.get(d.role, 0) + 1
    for role, n in sorted(final.items()):
        print(f"  {role:<11}: {n}기")


if __name__ == "__main__":
    main()
