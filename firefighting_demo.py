"""소방 드론 대응 시나리오 데모.

화재 현장에 SCOUT/SUPPRESSOR/GUIDE 드론을 투입해
탐지 → 진압 → 탈출 경로 안내로 이어지는 흐름을 시연한다.
"""

import numpy as np

from firefighting_drone import FirefightingDrone, DroneRole
from camera import CameraModel


def make_thermal_scene(shape=(20, 20)):
    frame = np.full(shape, 22.0)   # 상온 배경
    frame[3:6, 14:17] = 520.0      # 화점
    frame[12:15, 3:6] = 36.5       # 요구조자
    return frame


def make_hazard_map(shape=(20, 20)):
    """화점 주변을 위험(화염) 셀로 표시한 탈출용 그리드."""
    hazard = np.zeros(shape)
    hazard[2:8, 13:18] = 1  # 화점 주변 통행 불가
    return hazard


def main():
    thermal = make_thermal_scene()
    hazard = make_hazard_map()
    exit_pos = [19.0, 19.0, 0.0]  # 비상구(우하단)

    scout = FirefightingDrone("SCOUT-1", role=DroneRole.SCOUT)
    suppressor = FirefightingDrone("SUPP-1", role=DroneRole.SUPPRESSOR,
                                   payload=2, max_speed=6.0)
    guide = FirefightingDrone("GUIDE-1", role=DroneRole.GUIDE)

    print("=== 1) 수색: SCOUT가 화점·요구조자 탐지 ===")
    detection = scout.process_thermal_and_vision(thermal)
    print("  탐지 결과:", {k: (v.tolist() if v is not None else None)
                        for k, v in detection.items()})

    print("\n=== 2) 진압: SUPPRESSOR가 화점 접근·소화탄 투하 ===")
    suppressor.fire_hotspot_pos = detection["fire"]
    for _ in range(20):
        if suppressor.execute_suppression_routine(drop_range=3.0):
            if suppressor.payload_extinguisher == 0:
                break
    print(f"  최종 상태: {suppressor}")

    print("\n=== 3) 안내: GUIDE가 요구조자 탈출 경로 계산 ===")
    guide.target_survivor_pos = detection["survivor"]
    path = guide.generate_escape_path(hazard, exit_pos)
    if path is None:
        print("  안전 경로를 찾지 못했습니다.")
    else:
        print(f"  웨이포인트 {len(path)}개 (화염 회피):")
        for i, wp in enumerate(path):
            print(f"    {i:>2}: {np.round(wp, 1).tolist()}")

    print("\n=== 4) 픽셀→월드 변환: 고도 40m 드론의 열화상 탐지 ===")
    cam = CameraModel.from_fov(thermal.shape, hfov_deg=90.0)
    scout_hi = FirefightingDrone("SCOUT-HI", role=DroneRole.SCOUT, camera=cam)
    scout_hi.pos = np.array([100.0, 60.0, 40.0])  # 현장 상공
    det = scout_hi.process_thermal_and_vision(thermal, ground_z=0.0)
    print(f"  드론 위치 {scout_hi.pos.tolist()} 기준 월드 좌표")
    print(f"    화점(월드): {np.round(det['fire'], 2).tolist()}")
    print(f"    요구조자(월드): {np.round(det['survivor'], 2).tolist()}")

    print("\n=== 5) 3D 경로: 다층 건물 층간 탈출 ===")
    # 3개 층(z=0,1,2), 각 층 6x6. 0층 화염 벽 일부, 2층에 비상구.
    hazard3d = np.zeros((3, 6, 6))
    hazard3d[0, 0:5, 3] = 1  # 0층 화염 벽
    guide3d = FirefightingDrone("GUIDE-3D", role=DroneRole.GUIDE)
    guide3d.target_survivor_pos = np.array([0.0, 0.0, 0.0])  # 0층
    path3d = guide3d.generate_escape_path(hazard3d, exit_pos=[5.0, 5.0, 2.0])
    if path3d is None:
        print("  안전 경로를 찾지 못했습니다.")
    else:
        floors = sorted({int(wp[2]) for wp in path3d})
        print(f"  웨이포인트 {len(path3d)}개, 경유 층: {floors}")
        for i, wp in enumerate(path3d):
            print(f"    {i:>2}: (층 z={int(wp[2])}) {np.round(wp, 1).tolist()}")


if __name__ == "__main__":
    main()
