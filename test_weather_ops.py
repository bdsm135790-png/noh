"""weather_ops(기상↔드론 연동) 동작 검증 테스트(네트워크 불필요)."""

import numpy as np

from weather import WeatherInfo
import weather_ops as wo
from weather_ops import (
    assess_dispatch, apply_flight_limits, apply_to_swarm,
    wind_vector, compensate_velocity_for_wind,
)
from swarm_drone import SwarmDrone


def _wx(**over):
    base = dict(
        name="테스트시", latitude=37.0, longitude=127.0,
        temperature=20.0, humidity=50.0, wind_speed=3.0,
        wind_direction=0.0, precipitation=0.0, weather_code=0,
        observed_at="2026-07-28T12:00",
    )
    base.update(over)
    return WeatherInfo(**base)


# --- wind_vector -----------------------------------------------------------

def test_wind_vector_from_north_blows_south():
    v = wind_vector(_wx(wind_speed=5.0, wind_direction=0.0))
    assert np.allclose(v, [0.0, -5.0, 0.0], atol=1e-9)


def test_wind_vector_from_east_blows_west():
    v = wind_vector(_wx(wind_speed=4.0, wind_direction=90.0))
    assert np.allclose(v, [-4.0, 0.0, 0.0], atol=1e-9)


def test_wind_vector_nan_is_zero():
    assert np.allclose(wind_vector(_wx(wind_speed=float("nan"))), np.zeros(3))


# --- assess_dispatch -------------------------------------------------------

def test_no_go_when_wind_over_no_fly():
    d = assess_dispatch(_wx(wind_speed=wo.WIND_NO_FLY + 1))
    assert d.status == "NO_GO"
    assert d.can_fly is False
    assert d.recommended_suppressors == 0  # 비행 불가 → 실제 투입 0


def test_caution_when_wind_in_band():
    d = assess_dispatch(_wx(wind_speed=(wo.WIND_CAUTION + wo.WIND_NO_FLY) / 2))
    assert d.status == "CAUTION"
    assert d.can_fly is True
    assert d.speed_factor < 1.0
    assert d.safe_dist_factor > 1.0


def test_go_when_calm():
    d = assess_dispatch(_wx(wind_speed=1.0))
    assert d.status == "GO"
    assert d.speed_factor <= 1.0 and d.speed_factor >= 0.5


def test_high_fire_risk_raises_priority_and_suppressors():
    # 고온·극저습 + 주의 임계값 미만 바람(7 m/s) → 긴급이지만 비행은 가능.
    hot = _wx(temperature=42.0, humidity=5.0, wind_speed=7.0)
    d = assess_dispatch(hot)
    assert d.status in ("GO", "CAUTION")
    assert d.priority == "긴급"
    assert d.recommended_suppressors == 3


def test_low_fire_risk_low_priority():
    mild = _wx(temperature=12.0, humidity=90.0, wind_speed=1.0)
    d = assess_dispatch(mild)
    assert d.priority == "낮음"
    assert d.recommended_suppressors == 0


def test_missing_wind_is_conservative():
    d = assess_dispatch(_wx(wind_speed=float("nan")))
    assert d.status == "CAUTION"
    assert any("결측" in r for r in d.reasons)


# --- apply_flight_limits (누적 방지) ---------------------------------------

def test_apply_flight_limits_scales_from_base():
    drone = SwarmDrone("a", position=[0, 0, 0], velocity=[0, 0, 0], max_speed=10.0)
    dec = assess_dispatch(_wx(wind_speed=wo.WIND_NO_FLY))  # speed_factor=0.5
    applied = apply_flight_limits(drone, dec)
    assert np.isclose(applied, 5.0)
    # 다시 온화한 기상으로 갱신해도 원래 10 기준으로 재계산(누적 X).
    dec2 = assess_dispatch(_wx(wind_speed=0.0))
    applied2 = apply_flight_limits(drone, dec2)
    assert np.isclose(applied2, 10.0)


def test_apply_to_swarm_returns_flight_params():
    drones = [SwarmDrone(i, [0, 0, 0], [0, 0, 0], max_speed=10.0) for i in range(3)]
    dec = assess_dispatch(_wx(wind_speed=wo.WIND_NO_FLY))  # factor 0.5 / dist 2x
    params = apply_to_swarm(drones, dec, base_safe_dist=5.0)
    assert np.isclose(params["max_speed"], 5.0)
    assert np.isclose(params["safe_dist"], 10.0)
    assert all(np.isclose(d.max_speed, 5.0) for d in drones)


# --- 바람 드리프트 보정 ----------------------------------------------------

def test_compensate_offsets_wind():
    info = _wx(wind_speed=3.0, wind_direction=0.0)  # 북→남, wind=[0,-3,0]
    cmd = np.array([0.0, 0.0, 0.0])
    out = compensate_velocity_for_wind(cmd, info)
    # 남향 드리프트를 상쇄하려면 북쪽(+y)으로 명령해야 한다.
    assert np.allclose(out, [0.0, 3.0, 0.0], atol=1e-9)


def test_compensate_gain_zero_is_noop():
    info = _wx(wind_speed=9.0, wind_direction=45.0)
    cmd = np.array([1.0, 2.0, 0.0])
    assert np.allclose(compensate_velocity_for_wind(cmd, info, gain=0.0), cmd)


if __name__ == "__main__":
    import types

    passed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and isinstance(fn, types.FunctionType):
            fn()
            print(f"  ok  {name}")
            passed += 1
    print(f"\n{passed} passed")
