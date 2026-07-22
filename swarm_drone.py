"""드론 군집(Swarm) 자율 비행 로직.

Reynolds의 Boids 규칙(분리/정렬/결합)을 3차원 공간의 드론 군집에 적용한다.
각 드론은 주변 이웃(neighbors)의 상태만 보고 자신의 가속도를 계산하는
분산(decentralized) 방식으로 동작한다.
"""

import numpy as np


class SwarmDrone:
    """군집 비행에 참여하는 개별 드론.

    Parameters
    ----------
    drone_id : Any
        드론 식별자.
    position : array-like, shape (3,)
        초기 위치 [x, y, z] (m).
    velocity : array-like, shape (3,)
        초기 속도 [vx, vy, vz] (m/s).
    max_speed : float
        최대 속력 (m/s). 물리적으로 낼 수 있는 속도의 상한.
    max_force : float
        한 스텝에 가할 수 있는 최대 조향(가속) 크기.
    perception : float
        이웃으로 인식하는 반경 (m). 이 거리보다 먼 드론은 무시한다.
    """

    def __init__(
        self,
        drone_id,
        position,
        velocity,
        max_speed=10.0,
        max_force=2.0,
        perception=20.0,
    ):
        self.id = drone_id
        self.pos = np.array(position, dtype=float)  # [x, y, z]
        self.vel = np.array(velocity, dtype=float)  # [vx, vy, vz]
        self.max_speed = float(max_speed)
        self.max_force = float(max_force)
        self.perception = float(perception)

    # ------------------------------------------------------------------
    # 헬퍼
    # ------------------------------------------------------------------
    @staticmethod
    def _limit(vec, max_norm):
        """벡터의 크기를 max_norm 이하로 제한한다(방향은 유지)."""
        norm = np.linalg.norm(vec)
        if norm > max_norm and norm > 0:
            return vec * (max_norm / norm)
        return vec

    def compute_acceleration(self, neighbors, safe_dist=5.0, weights=None):
        """Boids 3규칙으로 이번 스텝의 가속도를 계산한다.

        위치/속도를 바꾸지 않고 순수하게 가속도 벡터만 반환하므로
        테스트와 재사용이 쉽다.

        Parameters
        ----------
        neighbors : list[SwarmDrone]
            주변 드론 객체 리스트(자기 자신 제외).
        safe_dist : float
            최소 안전 유지 거리 (m). 이보다 가까우면 분리력이 작용한다.
        weights : dict, optional
            {"separation", "alignment", "cohesion"} 가중치. 생략 시 기본값.

        Returns
        -------
        np.ndarray, shape (3,)
            max_force로 제한된 가속도 벡터.
        """
        w = {"separation": 1.5, "alignment": 0.2, "cohesion": 0.1}
        if weights:
            w.update(weights)

        sep_force = np.zeros(3)  # 분리(Separation) - 충돌 방지
        ali_force = np.zeros(3)  # 정렬(Alignment) - 속도 일치
        coh_force = np.zeros(3)  # 결합(Cohesion) - 중심 이동

        center_mass = np.zeros(3)
        avg_vel = np.zeros(3)
        neighbor_count = 0  # perception 반경 안의 이웃 수

        for other in neighbors:
            if other is self:
                continue
            offset = self.pos - other.pos
            dist = np.linalg.norm(offset)

            # perception 밖의 드론은 아예 무시한다.
            if dist > self.perception:
                continue

            # 1. 분리: 너무 가까운 드론과 반대 방향으로, 거리가 가까울수록 강하게.
            if dist < safe_dist:
                if dist > 0:
                    sep_force += offset / (dist ** 2)
                else:
                    # 정확히 같은 위치면 임의의 방향으로 밀어낸다.
                    sep_force += np.random.uniform(-1.0, 1.0, size=3)

            center_mass += other.pos
            avg_vel += other.vel
            neighbor_count += 1

        if neighbor_count > 0:
            # 2. 결합: 이웃 무게중심 방향으로.
            center_mass /= neighbor_count
            coh_force = center_mass - self.pos

            # 3. 정렬: 이웃 평균 속도에 맞춤.
            avg_vel /= neighbor_count
            ali_force = avg_vel - self.vel

        total_acceleration = (
            sep_force * w["separation"]
            + coh_force * w["cohesion"]
            + ali_force * w["alignment"]
        )

        return self._limit(total_acceleration, self.max_force)

    def update_swarm_behavior(self, neighbors, safe_dist=5.0, dt=1.0, weights=None):
        """가속도를 계산하고 속도/위치를 dt만큼 적분한다.

        Parameters
        ----------
        neighbors : list[SwarmDrone]
            주변 드론 객체 리스트.
        safe_dist : float
            최소 안전 유지 거리 (m).
        dt : float
            시간 간격 (s). 물리 적분에 사용한다.
        weights : dict, optional
            Boids 가중치.

        Returns
        -------
        np.ndarray
            적용된 가속도 벡터.
        """
        acc = self.compute_acceleration(neighbors, safe_dist=safe_dist, weights=weights)

        # 속도 및 위치 업데이트 (반암시적 오일러 적분).
        self.vel = self._limit(self.vel + acc * dt, self.max_speed)
        self.pos = self.pos + self.vel * dt
        return acc

    def __repr__(self):
        return (
            f"SwarmDrone(id={self.id!r}, "
            f"pos={np.round(self.pos, 2).tolist()}, "
            f"vel={np.round(self.vel, 2).tolist()})"
        )
