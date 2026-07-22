"""소방 드론 군집: 역할 기반 화재 대응 로직.

열화상/RGB 분석으로 화점(Fire)과 요구조자(Survivor)를 탐지하고, 역할에 따라
- SCOUT: 수색 및 경로 탐색
- SUPPRESSOR: 화점 초동 진압(시간 확보)
- GUIDE: 요구조자 탈출 안내
동작을 수행한다. 소화탄 소진 시 자율적으로 역할을 전환한다(Self-Healing).

원본 프로토타입 대비:
- 미사용/미설치 `cv2` 하드 의존 제거(있으면 사용, 없어도 동작).
- 스텁이던 A* 를 화염 회피 실제 A* 로 구현.
- 항상 True를 반환하던 탐지를 열화상 임계값 기반 탐지로 구현.
- 화점으로 접근하는 이동 로직 추가(없으면 투하 조건이 성립 불가).
- 소화탄 개수/역할 전환 방어 로직 보강.
"""

import heapq

import numpy as np

try:  # cv2는 선택 의존성. 없으면 numpy만으로 동작한다.
    import cv2  # noqa: F401
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False


# 열화상 임계값(섭씨)
FIRE_TEMP = 300.0          # 이 온도 이상은 화점으로 판단
SURVIVOR_TEMP_MIN = 30.0   # 연기/의복 감쇠를 고려한 인체 하한
SURVIVOR_TEMP_MAX = 42.0   # 인체 상한


class DroneRole:
    SCOUT = "SCOUT"           # 수색 및 경로 탐색
    SUPPRESSOR = "SUPPRESSOR"  # 화점 초동 진압 (시간 확보)
    GUIDE = "GUIDE"           # 요구조자 탈출 안내 및 보호


class FirefightingDrone:
    def __init__(self, drone_id, role=DroneRole.SCOUT, payload=2, max_speed=5.0):
        self.id = drone_id
        self.role = role
        self.pos = np.array([0.0, 0.0, 0.0])  # [x, y, z]
        self.vel = np.array([0.0, 0.0, 0.0])
        self.payload_extinguisher = int(payload)  # 소화탄 보유 개수
        self.max_speed = float(max_speed)
        self.target_survivor_pos = None
        self.fire_hotspot_pos = None

    # ------------------------------------------------------------------
    # [1] 센서 처리
    # ------------------------------------------------------------------
    def process_thermal_and_vision(self, thermal_frame, rgb_frame=None):
        """열화상(Thermal)/RGB 분석으로 화점·요구조자를 동시 추적한다.

        Returns
        -------
        dict
            {"fire": coords or None, "survivor": coords or None}
        """
        fire_detected, fire_coords = self._detect_fire_hotspot(thermal_frame)
        survivor_detected, survivor_coords = self._detect_survivor(
            thermal_frame, rgb_frame
        )

        if fire_detected:
            self.fire_hotspot_pos = fire_coords
            # 동적 역할 재배정: 진압 드론이 소화탄을 보유하면 진압 루틴 수행.
            if self.role == DroneRole.SUPPRESSOR and self.payload_extinguisher > 0:
                self.execute_suppression_routine()

        if survivor_detected:
            self.target_survivor_pos = survivor_coords
            print(f"[Drone {self.id}] 요구조자 발견! 위치: {survivor_coords}")

        return {
            "fire": fire_coords if fire_detected else None,
            "survivor": survivor_coords if survivor_detected else None,
        }

    # ------------------------------------------------------------------
    # [2] 진압
    # ------------------------------------------------------------------
    def execute_suppression_routine(self, drop_range=3.0):
        """화점으로 접근하고, 사거리 도달 시 소화탄을 투하한다.

        Returns
        -------
        bool
            이번 호출에서 소화탄을 투하했으면 True.
        """
        if self.fire_hotspot_pos is None or self.payload_extinguisher <= 0:
            return False

        # 화점을 향해 한 스텝 접근.
        self.move_toward(self.fire_hotspot_pos)

        dist_to_fire = np.linalg.norm(self.pos - self.fire_hotspot_pos)
        if dist_to_fire < drop_range:
            self.payload_extinguisher -= 1
            print(
                f"[Drone {self.id}] 화점에 소화탄 투하! "
                f"잔여 소화탄: {self.payload_extinguisher}"
            )
            # 소화탄 소진 시 안내(GUIDE) 모드로 자율 전환.
            if self.payload_extinguisher == 0:
                self.role = DroneRole.GUIDE
                print(f"[Drone {self.id}] 소화탄 소진 → 역할 전환: GUIDE")
            return True
        return False

    def move_toward(self, target, dt=1.0):
        """target 방향으로 max_speed 이내에서 한 스텝 이동한다."""
        target = np.asarray(target, dtype=float)
        direction = target - self.pos
        dist = np.linalg.norm(direction)
        if dist == 0:
            self.vel = np.zeros(3)
            return
        step = min(self.max_speed * dt, dist)
        self.vel = direction / dist * (step / dt)
        self.pos = self.pos + direction / dist * step

    # ------------------------------------------------------------------
    # [3] 탈출 경로 안내
    # ------------------------------------------------------------------
    def generate_escape_path(self, hazard_map, exit_pos, cell_size=1.0):
        """요구조자 → 비상구까지 화염을 회피하는 최단 경로(A*)를 만든다.

        Parameters
        ----------
        hazard_map : np.ndarray, shape (H, W)
            0=안전, 1 이상=위험(화염/장애물)인 2D 그리드.
        exit_pos : array-like, shape (2,) 또는 (3,)
            비상구 월드 좌표. (x, y)만 경로 탐색에 사용.
        cell_size : float
            그리드 한 칸의 실제 크기(m). 월드↔그리드 변환에 사용.

        Returns
        -------
        list[np.ndarray] or None
            월드 좌표 웨이포인트 목록. 경로가 없으면 None.
        """
        if self.target_survivor_pos is None:
            return None

        start_cell = self._world_to_cell(self.target_survivor_pos, cell_size)
        goal_cell = self._world_to_cell(exit_pos, cell_size)

        cell_path = self._astar_pathfinding(start_cell, goal_cell, hazard_map)
        if cell_path is None:
            print(f"[Drone {self.id}] 안전 경로 없음 — 재탐색 필요")
            return None

        # 그리드 경로를 월드 웨이포인트로 변환(고도 z는 요구조자 높이 유지).
        z = float(np.asarray(self.target_survivor_pos, dtype=float)[2]) \
            if len(np.atleast_1d(self.target_survivor_pos)) > 2 else 0.0
        return [
            np.array([c * cell_size, r * cell_size, z]) for (r, c) in cell_path
        ]

    # ------------------------------------------------------------------
    # 탐지 (열화상 임계값 기반)
    # ------------------------------------------------------------------
    def _detect_fire_hotspot(self, thermal_img):
        """열화상에서 FIRE_TEMP 이상 최고온 지점의 좌표를 반환한다."""
        thermal = np.asarray(thermal_img, dtype=float)
        mask = thermal >= FIRE_TEMP
        if not mask.any():
            return False, None
        r, c = np.unravel_index(np.argmax(thermal), thermal.shape)
        return True, np.array([float(c), float(r), 0.0])

    def _detect_survivor(self, thermal_img, rgb_img=None):
        """인체 온도 대역([MIN, MAX]) 영역의 무게중심 좌표를 반환한다."""
        thermal = np.asarray(thermal_img, dtype=float)
        mask = (thermal >= SURVIVOR_TEMP_MIN) & (thermal <= SURVIVOR_TEMP_MAX)
        if not mask.any():
            return False, None
        rows, cols = np.nonzero(mask)
        return True, np.array([float(cols.mean()), float(rows.mean()), 0.0])

    # ------------------------------------------------------------------
    # A* 경로 탐색 (실제 구현)
    # ------------------------------------------------------------------
    @staticmethod
    def _world_to_cell(world_pos, cell_size):
        p = np.asarray(world_pos, dtype=float)
        # 월드 (x, y) → 그리드 (row=y, col=x)
        col = int(round(p[0] / cell_size))
        row = int(round(p[1] / cell_size))
        return (row, col)

    @staticmethod
    def _astar_pathfinding(start, goal, hazard_map):
        """8방향 A*. hazard_map에서 값>0인 칸은 통과 불가.

        Returns
        -------
        list[tuple[int, int]] or None
            (row, col) 셀 경로. 시작=목표 포함. 경로 없으면 None.
        """
        grid = np.asarray(hazard_map)
        h, w = grid.shape

        def passable(cell):
            r, c = cell
            return 0 <= r < h and 0 <= c < w and grid[r, c] <= 0

        if not passable(start) or not passable(goal):
            return None

        def heuristic(a, b):
            # 대각 이동을 허용하므로 옥타일 거리 사용.
            dr, dc = abs(a[0] - b[0]), abs(a[1] - b[1])
            return (dr + dc) + (np.sqrt(2) - 2) * min(dr, dc)

        neighbors = [(-1, 0), (1, 0), (0, -1), (0, 1),
                     (-1, -1), (-1, 1), (1, -1), (1, 1)]

        open_heap = [(heuristic(start, goal), 0.0, start)]
        came_from = {}
        g_score = {start: 0.0}
        closed = set()

        while open_heap:
            _, g, current = heapq.heappop(open_heap)
            if current == goal:
                path = [current]
                while current in came_from:
                    current = came_from[current]
                    path.append(current)
                path.reverse()
                return path
            if current in closed:
                continue
            closed.add(current)

            for dr, dc in neighbors:
                nxt = (current[0] + dr, current[1] + dc)
                if not passable(nxt) or nxt in closed:
                    continue
                # 대각 이동 시 모서리를 파고들지 않도록 두 변 모두 통과 가능해야 함.
                if dr != 0 and dc != 0:
                    if not passable((current[0] + dr, current[1])) or \
                       not passable((current[0], current[1] + dc)):
                        continue
                step_cost = np.sqrt(2) if (dr and dc) else 1.0
                tentative = g + step_cost
                if tentative < g_score.get(nxt, np.inf):
                    came_from[nxt] = current
                    g_score[nxt] = tentative
                    f = tentative + heuristic(nxt, goal)
                    heapq.heappush(open_heap, (f, tentative, nxt))

        return None  # 도달 불가

    def __repr__(self):
        return (
            f"FirefightingDrone(id={self.id!r}, role={self.role}, "
            f"payload={self.payload_extinguisher}, "
            f"pos={np.round(self.pos, 2).tolist()})"
        )
