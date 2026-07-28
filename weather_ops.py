"""기상정보 → 드론 출동/비행 로직 연동.

`weather.WeatherInfo`(실시간 기상)를 받아
1. **출동 판단**: 풍속(비행 안전)과 화재기상 위험도(긴급도)를 결합해
   GO / CAUTION / NO_GO 를 결정하고 투입 진압 드론 수·우선순위를 권고한다.
2. **비행 파라미터 조정**: 강풍일수록 최대 속력을 낮춰(제어 여유 확보) 안전
   유지 거리를 넓힌다(돌풍 드리프트 충돌 방지).
3. **풍향 드리프트 보정**: 지상 궤적을 유지하도록 속도 명령을 바람만큼 보정한다.

좌표계는 프로젝트 관례를 따른다: 월드 x=동(East), y=북(North), z=상(Up).
기상학 풍향(`wind_direction`)은 '바람이 불어오는' 방향(0=북, 90=동)이다.
"""

import math
from dataclasses import dataclass, field

import numpy as np

# 비행 안전 풍속 임계값 (m/s). 소형 멀티로터 운용 기준의 보수적 예시값.
WIND_CAUTION = 8.0    # 이상: 주의 비행(속도↓·간격↑)
WIND_NO_FLY = 12.0    # 이상: 비행 금지(안전상 이륙 보류)


def _clamp(x, lo, hi):
    return max(lo, min(hi, x))


def wind_vector(info):
    """바람이 '불어가는' 방향의 속도 벡터(m/s)를 월드 좌표로 반환한다.

    기상학 풍향은 불어오는 방향이므로 180도를 더해 불어가는 방향으로 바꾼다.
    반환 벡터는 공기가 드론에 실어주는 속도(드리프트)로 해석한다.

    Returns
    -------
    np.ndarray, shape (3,)
        [동, 북, 0] 성분의 바람 속도. 데이터 결측 시 영벡터.
    """
    if math.isnan(info.wind_speed) or math.isnan(info.wind_direction):
        return np.zeros(3)
    toward = math.radians((info.wind_direction + 180.0) % 360.0)
    east = math.sin(toward) * info.wind_speed
    north = math.cos(toward) * info.wind_speed
    return np.array([east, north, 0.0])


@dataclass
class DispatchDecision:
    """기상 기반 출동/비행 권고."""

    status: str               # "GO" / "CAUTION" / "NO_GO"
    can_fly: bool             # 풍속상 비행 가능 여부
    fire_level: str           # 화재기상 위험 등급
    fire_score: float         # 화재기상 위험 점수(0~100)
    priority: str             # 대응 우선순위: 긴급/높음/보통/낮음
    recommended_suppressors: int  # 권고 진압 드론 수
    speed_factor: float       # 최대 속력에 곱할 계수(0~1)
    safe_dist_factor: float   # 안전 유지 거리에 곱할 계수(>=1)
    reasons: list = field(default_factory=list)

    def summary(self):
        r = " / ".join(self.reasons)
        return (
            f"[출동판단] {self.status} · 우선순위 {self.priority} · "
            f"화재위험 {self.fire_level}({self.fire_score}) · "
            f"진압드론 {self.recommended_suppressors}기 권고 · "
            f"속도×{self.speed_factor:.2f} 간격×{self.safe_dist_factor:.2f}"
            + (f"\n           사유: {r}" if r else "")
        )


def assess_dispatch(info):
    """기상정보로 출동/비행 권고를 산출한다.

    - 풍속이 `WIND_NO_FLY` 이상이면 안전상 NO_GO(이륙 보류).
    - 풍속이 `WIND_CAUTION` 이상이면 CAUTION(속도·간격 조정 후 비행).
    - 그 외에는 GO.
    화재기상 위험도는 우선순위와 투입 진압 드론 수 권고에 반영한다.

    Parameters
    ----------
    info : weather.WeatherInfo

    Returns
    -------
    DispatchDecision
    """
    level, score = info.fire_weather_risk()
    reasons = []

    wind = info.wind_speed
    wind_known = not math.isnan(wind)

    # --- 비행 가능성(풍속 기반 안전 판단) ---
    if wind_known and wind >= WIND_NO_FLY:
        can_fly = False
        status = "NO_GO"
        reasons.append(f"풍속 {wind:.1f} m/s ≥ 비행금지 {WIND_NO_FLY:.0f} m/s")
    elif wind_known and wind >= WIND_CAUTION:
        can_fly = True
        status = "CAUTION"
        reasons.append(f"풍속 {wind:.1f} m/s ≥ 주의 {WIND_CAUTION:.0f} m/s (속도·간격 조정)")
    else:
        can_fly = True
        status = "GO"
        if not wind_known:
            status = "CAUTION"
            reasons.append("풍속 결측 → 보수적으로 주의 운용")

    # --- 강수/시정 경고(비행 자체는 허용하되 사유로 남김) ---
    if info.precipitation >= 5.0:
        reasons.append(f"강수 {info.precipitation:.1f} mm — 센서·비행 저하 주의")

    # --- 화재기상 위험도 → 우선순위/진압 드론 수 ---
    if score >= 75:
        priority, base_suppressors = "긴급", 3
    elif score >= 50:
        priority, base_suppressors = "높음", 2
    elif score >= 25:
        priority, base_suppressors = "보통", 1
    else:
        priority, base_suppressors = "낮음", 0
    reasons.append(f"화재기상 {level}({score}) → 우선순위 {priority}")

    # 비행 불가면 실제 투입은 0기(대기), 권고 수는 참고용으로 유지.
    recommended = 0 if not can_fly else base_suppressors

    # --- 비행 파라미터 계수(풍속 비례) ---
    if wind_known:
        w = _clamp(wind / WIND_NO_FLY, 0.0, 1.0)
    else:
        w = WIND_CAUTION / WIND_NO_FLY  # 결측 시 주의 수준으로 가정
    speed_factor = _clamp(1.0 - 0.5 * w, 0.5, 1.0)   # 최대 50%까지 감속
    safe_dist_factor = 1.0 + w                         # 최대 2배까지 간격 확대

    return DispatchDecision(
        status=status,
        can_fly=can_fly,
        fire_level=level,
        fire_score=score,
        priority=priority,
        recommended_suppressors=recommended,
        speed_factor=round(speed_factor, 3),
        safe_dist_factor=round(safe_dist_factor, 3),
        reasons=reasons,
    )


def _base_speed(drone):
    """드론의 '원래' 최대 속력을 반환(최초 1회 저장해 반복 적용 시 누적 방지)."""
    base = getattr(drone, "_weather_base_max_speed", None)
    if base is None:
        base = float(drone.max_speed)
        drone._weather_base_max_speed = base
    return base


def apply_flight_limits(drone, decision):
    """단일 드론(FirefightingDrone/SwarmDrone)에 기상 속도 제한을 적용한다.

    원래 최대 속력을 기준으로 계수를 곱하므로, 기상 갱신 때마다 반복 호출해도
    값이 누적되지 않는다.

    Returns
    -------
    float
        적용된 최대 속력.
    """
    base = _base_speed(drone)
    drone.max_speed = base * decision.speed_factor
    return drone.max_speed


def apply_to_swarm(drones, decision, base_safe_dist=5.0):
    """군집 전체에 속도 제한을 적용하고, 권고 안전 유지 거리를 반환한다.

    Parameters
    ----------
    drones : Iterable[SwarmDrone]
    decision : DispatchDecision
    base_safe_dist : float
        기상 보정 전 기본 안전 유지 거리(m).

    Returns
    -------
    dict
        {"safe_dist": float, "max_speed": float} — update_swarm_behavior 에
        그대로 넘길 수 있는 값.
    """
    max_speed = None
    for d in drones:
        max_speed = apply_flight_limits(d, decision)
    return {
        "safe_dist": base_safe_dist * decision.safe_dist_factor,
        "max_speed": max_speed,
    }


def compensate_velocity_for_wind(velocity_cmd, info, gain=1.0):
    """지상 궤적을 유지하도록 속도 명령을 바람만큼 보정한다.

    목표 지상 속도를 유지하려면 대기속도(airspeed) = 지상속도 − 바람속도 이어야
    한다. 즉 바람이 실어주는 드리프트를 상쇄하는 방향으로 명령을 조정한다.

    Parameters
    ----------
    velocity_cmd : array-like, shape (3,)
        원하는 지상 기준 속도 명령.
    info : weather.WeatherInfo
    gain : float
        보정 강도(0=보정 안 함, 1=완전 상쇄). 돌풍 과보정 방지용으로 <1 권장.

    Returns
    -------
    np.ndarray, shape (3,)
        바람 보정된 속도 명령.
    """
    cmd = np.asarray(velocity_cmd, dtype=float)
    return cmd - gain * wind_vector(info)
