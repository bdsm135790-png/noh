"""FirefightingDrone 동작 검증 테스트."""

import numpy as np

from firefighting_drone import FirefightingDrone, DroneRole, FIRE_TEMP


def _thermal_with_fire_and_survivor(shape=(20, 20)):
    """상온 배경에 화점 1개와 요구조자 영역 1개를 심은 열화상 프레임."""
    frame = np.full(shape, 20.0)   # 배경 20도
    frame[2:4, 15:17] = 450.0      # 화점 (>= FIRE_TEMP)
    frame[10:13, 4:7] = 36.5       # 요구조자 체온 대역
    return frame


def test_detects_fire_and_survivor():
    d = FirefightingDrone("s1", role=DroneRole.SCOUT)
    frame = _thermal_with_fire_and_survivor()
    result = d.process_thermal_and_vision(frame)
    assert result["fire"] is not None
    assert result["survivor"] is not None
    # 화점은 열화상 우상단(col~15, row~2) 부근이어야 한다.
    assert result["fire"][0] >= 14 and result["fire"][1] <= 4


def test_no_false_detection_on_cold_frame():
    d = FirefightingDrone("s2")
    cold = np.full((10, 10), 15.0)
    result = d.process_thermal_and_vision(cold)
    assert result["fire"] is None
    assert result["survivor"] is None


def test_suppressor_drops_and_switches_role():
    """진압 드론은 화점에 접근·투하하고, 소진 시 GUIDE로 전환된다."""
    d = FirefightingDrone("f1", role=DroneRole.SUPPRESSOR, payload=1, max_speed=100.0)
    d.fire_hotspot_pos = np.array([10.0, 0.0, 0.0])
    dropped = d.execute_suppression_routine(drop_range=3.0)
    assert dropped is True
    assert d.payload_extinguisher == 0
    assert d.role == DroneRole.GUIDE


def test_payload_never_goes_negative():
    d = FirefightingDrone("f2", role=DroneRole.SUPPRESSOR, payload=0)
    d.fire_hotspot_pos = np.array([0.0, 0.0, 0.0])
    dropped = d.execute_suppression_routine()
    assert dropped is False
    assert d.payload_extinguisher == 0


def test_move_toward_respects_max_speed():
    d = FirefightingDrone("m1", max_speed=5.0)
    d.move_toward([100.0, 0.0, 0.0], dt=1.0)
    assert np.isclose(np.linalg.norm(d.pos), 5.0)


def test_astar_avoids_fire_wall():
    """화염 벽을 우회하는 경로를 찾는다."""
    d = FirefightingDrone("g1", role=DroneRole.GUIDE)
    hazard = np.zeros((5, 5))
    hazard[0:4, 2] = 1  # 위쪽을 막는 화염 벽(아래 한 칸만 열림)
    d.target_survivor_pos = np.array([0.0, 0.0, 0.0])  # (row0,col0)
    path = d.generate_escape_path(hazard, exit_pos=[4.0, 0.0, 0.0])
    assert path is not None
    # 경로의 어떤 웨이포인트도 화염 셀을 밟지 않아야 한다.
    for wp in path:
        col, row = int(round(wp[0])), int(round(wp[1]))
        assert hazard[row, col] <= 0


def test_astar_returns_none_when_blocked():
    """완전히 막히면 None을 반환한다."""
    d = FirefightingDrone("g2", role=DroneRole.GUIDE)
    hazard = np.zeros((5, 5))
    hazard[:, 2] = 1  # 세로 벽으로 완전 차단
    d.target_survivor_pos = np.array([0.0, 0.0, 0.0])
    path = d.generate_escape_path(hazard, exit_pos=[4.0, 0.0, 0.0])
    assert path is None


def test_scout_does_not_suppress():
    """SCOUT는 화점을 탐지해도 소화탄을 투하하지 않는다."""
    d = FirefightingDrone("s3", role=DroneRole.SCOUT, payload=2)
    frame = _thermal_with_fire_and_survivor()
    d.process_thermal_and_vision(frame)
    assert d.payload_extinguisher == 2
    assert d.role == DroneRole.SCOUT


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
