"""FirefightingDrone 동작 검증 테스트."""

import numpy as np

from firefighting_drone import FirefightingDrone, DroneRole, FIRE_TEMP
from camera import CameraModel


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


def test_camera_center_maps_below_drone():
    """이미지 중심 픽셀은 드론 바로 아래 지점으로 변환된다."""
    cam = CameraModel.from_fov((20, 20), hfov_deg=90.0)
    d = FirefightingDrone("c1", camera=cam)
    d.pos = np.array([7.0, 3.0, 30.0])  # 고도 30m
    # 중심 픽셀 (cx, cy) = (10, 10)
    world = d._pixel_to_world([10.0, 10.0], target_z=0.0)
    assert np.allclose(world, [7.0, 3.0, 0.0], atol=1e-6)


def test_camera_offset_pixel_scales_with_altitude():
    """중심에서 벗어난 픽셀은 고도에 비례해 지면상 거리가 커진다."""
    cam = CameraModel.from_fov((20, 20), hfov_deg=90.0)
    d = FirefightingDrone("c2", camera=cam)
    # HFOV 90° → fx = (W/2)/tan(45°) = 10. 픽셀 u=20이면 (20-10)/10=1.0 rad ratio.
    d.pos = np.array([0.0, 0.0, 10.0])
    w10 = d._pixel_to_world([20.0, 10.0], target_z=0.0)
    d.pos = np.array([0.0, 0.0, 20.0])
    w20 = d._pixel_to_world([20.0, 10.0], target_z=0.0)
    # 고도가 2배면 지면상 x변위도 2배.
    assert np.isclose(w20[0], 2 * w10[0])
    assert w10[0] > 0


def test_detection_uses_camera_when_present():
    """카메라가 있으면 탐지 결과가 월드 좌표(드론 위치 반영)로 나온다."""
    cam = CameraModel.from_fov((20, 20), hfov_deg=90.0)
    d = FirefightingDrone("c3", camera=cam)
    d.pos = np.array([100.0, 50.0, 40.0])
    frame = _thermal_with_fire_and_survivor()  # 화점: row~2, col~15
    result = d.process_thermal_and_vision(frame, ground_z=0.0)
    # 픽셀 좌표(col~15)가 아니라 드론 부근(x~100)의 월드 좌표여야 한다.
    assert result["fire"][0] > 50
    assert np.isclose(result["fire"][2], 0.0)


def test_no_camera_returns_pixel_coords():
    """카메라가 없으면 기존처럼 픽셀 좌표를 반환한다(하위 호환)."""
    d = FirefightingDrone("c4")  # camera=None
    frame = _thermal_with_fire_and_survivor()
    result = d.process_thermal_and_vision(frame)
    assert result["fire"][0] < 20  # 픽셀 col 범위 내


def test_astar_3d_climbs_floors():
    """다층 건물에서 위층 비상구까지 층 간 이동 경로를 찾는다."""
    d = FirefightingDrone("v1", role=DroneRole.GUIDE)
    hazard = np.zeros((3, 4, 4))  # 3개 층, 4x4
    d.target_survivor_pos = np.array([0.0, 0.0, 0.0])   # 0층 (z=0)
    path = d.generate_escape_path(hazard, exit_pos=[3.0, 3.0, 2.0])  # 2층 비상구
    assert path is not None
    assert np.allclose(path[0], [0.0, 0.0, 0.0])
    assert np.allclose(path[-1], [3.0, 3.0, 2.0])
    # 경로가 실제로 층을 오른다(z 값이 증가하는 지점이 있다).
    z_values = [wp[2] for wp in path]
    assert max(z_values) == 2.0


def test_astar_3d_avoids_blocked_floor():
    """한 층이 완전히 막히면 그 층을 통해서는 못 가고 None 또는 우회."""
    d = FirefightingDrone("v2", role=DroneRole.GUIDE)
    hazard = np.zeros((2, 3, 3))
    hazard[1, :, :] = 1  # 1층(위층) 전체가 화염 → 진입 불가
    d.target_survivor_pos = np.array([0.0, 0.0, 0.0])
    path = d.generate_escape_path(hazard, exit_pos=[2.0, 2.0, 1.0])  # 막힌 층 목표
    assert path is None


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
