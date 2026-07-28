"""기상 연동 출동/비행 시나리오 데모.

실시간 기상을 조회해(실패 시 예시 기상으로 폴백) 출동 판단을 내리고,
그 결과를 군집·소방 드론의 비행 파라미터에 반영하는 흐름을 보여준다.

실행:  python3 weather_ops_demo.py [지명]
"""

import sys

import numpy as np

from weather import WeatherInfo, get_weather
import weather_ops as wo
from weather_ops import assess_dispatch, apply_to_swarm, compensate_velocity_for_wind
from swarm_drone import SwarmDrone
from firefighting_drone import FirefightingDrone, DroneRole


def _sample_weather(name):
    """네트워크 없이도 데모가 돌도록 하는 예시 기상(고온·건조·강풍)."""
    return WeatherInfo(
        name=name, latitude=37.57, longitude=126.98,
        temperature=36.0, humidity=18.0, wind_speed=9.5, wind_direction=270.0,
        precipitation=0.0, weather_code=1, observed_at="2026-07-28T14:00 (예시)",
    )


def load_weather(place):
    try:
        info = get_weather(place)
        print(f"[기상] 실시간 조회 성공")
        return info
    except Exception as exc:  # noqa: BLE001
        print(f"[기상] 실시간 조회 실패({exc}) → 예시 기상 사용")
        return _sample_weather(place)


def main(place="서울"):
    info = load_weather(place)
    print(info.summary())
    print()

    decision = assess_dispatch(info)
    print(decision.summary())
    print()

    if not decision.can_fly:
        print("→ 비행 금지 조건. 전 기체 대기, 기상 호전 시 재평가.")
        return

    # --- 군집(SCOUT) 드론: 기상 속도/간격 보정 후 한 스텝 비행 ---
    swarm = [
        SwarmDrone("scout-1", position=[0, 0, 30], velocity=[5, 0, 0], max_speed=10.0),
        SwarmDrone("scout-2", position=[6, 0, 30], velocity=[5, 0, 0], max_speed=10.0),
        SwarmDrone("scout-3", position=[3, 5, 30], velocity=[5, 0, 0], max_speed=10.0),
    ]
    params = apply_to_swarm(swarm, decision, base_safe_dist=5.0)
    print(f"[군집] 기상 보정 → max_speed={params['max_speed']:.2f} m/s, "
          f"safe_dist={params['safe_dist']:.2f} m")
    for d in swarm:
        d.update_swarm_behavior(swarm, safe_dist=params["safe_dist"], dt=0.1)
    print(f"       한 스텝 후 대표 기체: {swarm[0]}")
    print()

    # --- 소방(SUPPRESSOR) 드론: 화점 접근 시 바람 드리프트 보정 ---
    sup = FirefightingDrone("sup-1", role=DroneRole.SUPPRESSOR, payload=2, max_speed=10.0)
    wo.apply_flight_limits(sup, decision)
    sup.fire_hotspot_pos = np.array([50.0, 0.0, 0.0])
    print(f"[진압] 기상 보정 → max_speed={sup.max_speed:.2f} m/s")

    # 화점 방향 지상 속도 명령 → 바람 보정된 대기속도 명령.
    to_fire = sup.fire_hotspot_pos - sup.pos
    ground_cmd = to_fire / np.linalg.norm(to_fire) * sup.max_speed
    air_cmd = compensate_velocity_for_wind(ground_cmd, info, gain=0.8)
    wind = wo.wind_vector(info)
    print(f"       바람 벡터(동,북)={np.round(wind[:2], 2).tolist()} m/s")
    print(f"       지상 속도 명령={np.round(ground_cmd[:2], 2).tolist()} → "
          f"바람보정 명령={np.round(air_cmd[:2], 2).tolist()}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "서울")
