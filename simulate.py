"""드론 군집 시뮬레이션 데모.

무작위로 흩어진 드론들이 Boids 규칙에 따라 뭉치면서도 서로 충돌하지 않고
비행하는 과정을 콘솔에 요약 출력한다.
"""

import numpy as np

from swarm_drone import SwarmDrone


def build_swarm(n=15, spread=15.0, seed=0):
    rng = np.random.default_rng(seed)
    drones = []
    for i in range(n):
        pos = rng.uniform(-spread, spread, size=3)
        vel = rng.uniform(-2.0, 2.0, size=3)
        drones.append(SwarmDrone(i, pos, vel))
    return drones


def swarm_spread(drones):
    """군집의 퍼짐 정도(무게중심으로부터의 평균 거리)."""
    positions = np.array([d.pos for d in drones])
    center = positions.mean(axis=0)
    return np.linalg.norm(positions - center, axis=1).mean()


def min_pairwise_distance(drones):
    positions = np.array([d.pos for d in drones])
    n = len(positions)
    best = np.inf
    for i in range(n):
        for j in range(i + 1, n):
            best = min(best, np.linalg.norm(positions[i] - positions[j]))
    return best


def run(steps=200, dt=0.1, safe_dist=5.0):
    # 드론들이 서로의 인식 반경(perception) 안에서 편대 이륙하는 상황을 가정한다.
    drones = build_swarm()
    print(f"{'step':>5} {'spread(m)':>10} {'min_dist(m)':>12}")
    for step in range(steps + 1):
        if step % 20 == 0:
            print(f"{step:>5} {swarm_spread(drones):>10.2f} "
                  f"{min_pairwise_distance(drones):>12.2f}")
        # 동시 업데이트를 위해 이번 스텝의 이웃은 갱신 전 스냅샷으로 본다.
        snapshot = [SwarmDrone(d.id, d.pos, d.vel) for d in drones]
        for d in drones:
            neighbors = [s for s in snapshot if s.id != d.id]
            d.update_swarm_behavior(neighbors, safe_dist=safe_dist, dt=dt)
    return drones


if __name__ == "__main__":
    run()
