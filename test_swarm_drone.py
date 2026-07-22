"""SwarmDrone 동작 검증 테스트."""

import numpy as np

from swarm_drone import SwarmDrone
from simulate import build_swarm, min_pairwise_distance, swarm_spread


def test_no_neighbors_holds_course():
    """이웃이 없으면 가속도는 0이고 등속으로 직진한다."""
    d = SwarmDrone("solo", [0, 0, 0], [1, 0, 0])
    acc = d.update_swarm_behavior([], dt=1.0)
    assert np.allclose(acc, 0.0)
    assert np.allclose(d.pos, [1, 0, 0])
    assert np.allclose(d.vel, [1, 0, 0])


def test_separation_pushes_apart():
    """안전거리보다 가까운 이웃과는 반대 방향으로 밀려난다."""
    a = SwarmDrone("a", [0, 0, 0], [0, 0, 0])
    b = SwarmDrone("b", [1, 0, 0], [0, 0, 0])
    acc = a.compute_acceleration([b], safe_dist=5.0)
    # b가 +x에 있으므로 a는 -x 방향으로 가속해야 한다.
    assert acc[0] < 0


def test_speed_is_limited():
    """어떤 상황에서도 속력은 max_speed를 넘지 않는다."""
    d = SwarmDrone("a", [0, 0, 0], [0, 0, 0], max_speed=10.0)
    far = SwarmDrone("b", [1000, 0, 0], [50, 0, 0])
    for _ in range(50):
        d.update_swarm_behavior([far], dt=1.0)
        assert np.linalg.norm(d.vel) <= d.max_speed + 1e-9


def test_force_is_limited():
    """가속도 크기는 max_force로 제한된다."""
    d = SwarmDrone("a", [0, 0, 0], [0, 0, 0], max_force=2.0)
    far = SwarmDrone("b", [1000, 0, 0], [0, 0, 0])
    acc = d.compute_acceleration([far])
    assert np.linalg.norm(acc) <= d.max_force + 1e-9


def test_perception_ignores_distant_drones():
    """perception 반경 밖의 드론은 무시된다."""
    d = SwarmDrone("a", [0, 0, 0], [0, 0, 0], perception=10.0)
    outside = SwarmDrone("b", [100, 0, 0], [5, 5, 5])
    acc = d.compute_acceleration([outside])
    assert np.allclose(acc, 0.0)


def test_coincident_drones_do_not_crash():
    """정확히 같은 위치에 있어도 NaN/예외 없이 분리력이 계산된다."""
    a = SwarmDrone("a", [0, 0, 0], [0, 0, 0])
    b = SwarmDrone("b", [0, 0, 0], [0, 0, 0])
    acc = a.compute_acceleration([b], safe_dist=5.0)
    assert np.all(np.isfinite(acc))


def test_swarm_converges_without_collision():
    """시뮬레이션 후 군집은 더 뭉치되(퍼짐 감소) 서로 충돌하지 않는다."""
    drones = build_swarm(n=15, seed=1)
    start_spread = swarm_spread(drones)
    dt, safe = 0.1, 5.0
    for _ in range(300):
        snapshot = [SwarmDrone(d.id, d.pos, d.vel) for d in drones]
        for d in drones:
            neighbors = [s for s in snapshot if s.id != d.id]
            d.update_swarm_behavior(neighbors, safe_dist=safe, dt=dt)
    end_spread = swarm_spread(drones)
    assert end_spread < start_spread  # 결합력으로 더 뭉쳤다.
    assert min_pairwise_distance(drones) > 0.5  # 겹치지 않는다.


if __name__ == "__main__":
    import sys

    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"PASS {name}")
            except AssertionError as exc:
                failures += 1
                print(f"FAIL {name}: {exc}")
    sys.exit(1 if failures else 0)
