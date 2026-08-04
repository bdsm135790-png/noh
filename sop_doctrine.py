"""드론 군집체계 재난현장 표준작전절차(SOP-D)의 코드화.

「소방청 표준작전절차 — 드론 군집체계 재난현장 SOP(2026)」변형판을 편대 편성과
행동 규칙으로 코드화한다. 근거 SOP 코드를 함께 기록한다.

핵심 매핑
---------
  SOP 101-D  GCS 지상통제소 구축·공중지휘권        -> Squad.GCS, Cold Zone 배치
  SOP 102-D  공중 정밀 상황평가·3D 매핑            -> RECON 편대 정찰/열화상
  SOP 103-D  무중단 배터리 릴레이                  -> needs_relay(), 예비기 전진배치
  SOP 105-D  편대 역할분담(4편대)                  -> Squad, SQUAD_NAME/PAYLOAD
  SOP 109-D  비상탈출·RTH(편대별 다단계 복귀고도)  -> rth_altitude()
  SSG-D 100  Fail-Safe(3m 반발 회피, 링크두절 RTH) -> repulsive_avoidance(), emergency_land()
"""

import numpy as np


class Squad:
    """SOP 105-D 군집 편대(Squadron)."""
    GCS = "GCS"                  # 지상통제소/현장지휘(공중지휘권)
    RECON = "RECON"             # 1편대 공중정찰대 (EO/IR·LiDAR, 3D 매핑)
    SAR = "SAR"                 # 2편대 인명수색·구조대 (확성기·키트 투하)
    SUPPRESSION = "SUPPRESSION"  # 3편대 화재진압대 (창문 파쇄·소화탄 투하)
    COMMS = "COMMS"             # 4편대 통신중계·조명대 (Mesh 중계·LED 조명)


SQUAD_NAME = {
    Squad.GCS: "GCS 지상통제소",
    Squad.RECON: "1편대 공중정찰대",
    Squad.SAR: "2편대 인명수색·구조대",
    Squad.SUPPRESSION: "3편대 화재진압대",
    Squad.COMMS: "4편대 통신중계·조명대",
}

SQUAD_PAYLOAD = {
    Squad.GCS: "Mesh Wi-Fi / LTE·5G 데이터링크",
    Squad.RECON: "EO/IR 열화상, LiDAR",
    Squad.SAR: "고배율 광학, 확성기, 생명유지 키트 투하장치",
    Squad.SUPPRESSION: "소화탄 투하 랙, 소화 겔 분사기",
    Squad.COMMS: "Mesh 통신 중계기, 대형 LED 조명",
}

# SOP 109-D: 편대별 다단계 복귀 고도(m). 공중 충돌 방지.
RTH_ALTITUDE = {
    Squad.RECON: 50.0, Squad.SAR: 70.0, Squad.SUPPRESSION: 90.0,
    Squad.COMMS: 110.0, Squad.GCS: 0.0,
}

# SOP 103-D / SSG-D 100 임계값.
BATTERY_RELAY_PCT = 25.0       # 이하 시 예비기 릴레이 발사
BATTERY_EMERGENCY_PCT = 10.0   # 이하 시 현위치 비상 착륙
REPULSE_DIST_M = 3.0           # 기체 간 3m 이내 접근 시 반발 회피
NOTAM_RADIUS_M = 1000.0        # 공중 통제구역 반경
CONTROL_CEILING_M = 150.0      # 통제 고도 상한

SOP_REFS = {
    "101-D": "GCS 구축·공중지휘권 확립",
    "102-D": "공중 정밀 상황평가·3D 매핑",
    "103-D": "무중단 배터리 릴레이",
    "105-D": "군집 편대 역할분담",
    "109-D": "비상탈출·RTH(다단계 복귀고도)",
    "222-D": "고층 건축물 화재 대응",
    "310-D": "유해화학물질 누출 대응",
    "SSG-D 100": "Fail-Safe 매트릭스(3m 반발 회피)",
}


def rth_altitude(squad):
    """편대별 복귀 고도(m). SOP 109-D."""
    return RTH_ALTITUDE.get(squad, 60.0)


def needs_relay(battery_pct):
    """배터리 25% 이하면 무중단 릴레이 필요. SOP 103-D."""
    return float(battery_pct) <= BATTERY_RELAY_PCT


def emergency_land(battery_pct):
    """배터리 10% 이하면 현위치 비상 착륙. SSG-D 100."""
    return float(battery_pct) <= BATTERY_EMERGENCY_PCT


def repulsive_avoidance(pos, others, dist=REPULSE_DIST_M):
    """기체 간 3m 이내 접근 시 반발력 벡터. SSG-D 100(자율 충돌회피).

    Parameters
    ----------
    pos : (3,) 현재 기체 위치
    others : list[(3,)] 다른 기체 위치들
    """
    pos = np.asarray(pos, float)
    f = np.zeros(3)
    for o in others:
        d = pos - np.asarray(o, float)
        n = np.linalg.norm(d)
        if 0 < n < dist:
            f += (d / n) * (dist - n) / dist
    return f


# 편대별 실시간 담당 임무(현장 상태 표시용) — 단계(phase)에 따라 달라진다.
_TASK = {
    Squad.GCS: {
        "deploy": ("공중지휘권 선언·NOTAM 설정", "101-D"),
        "assess": ("3D 매핑 데이터 융합·지휘", "102-D"),
        "operate": ("편대 통합 제어·자원 관리", "101-D"),
        "relay": ("배터리 릴레이 지시", "103-D"),
        "clear": ("작전 종결·디브리핑", "113-D"),
    },
    Squad.RECON: {
        "deploy": ("정찰 편대 출격·상승", "102-D"),
        "assess": ("사방 3D 스캐닝·열화상 화점 탐지", "102-D"),
        "operate": ("화점·연소확대선 지속 모니터링", "105-D"),
        "relay": ("임무 이양 후 RTH(고도 50m)", "109-D"),
        "clear": ("현장 감시 유지", "105-D"),
    },
    Squad.SAR: {
        "deploy": ("수색·구조 편대 전개", "105-D"),
        "assess": ("고립 구조대상자 자동 식별", "102-D"),
        "operate": ("생명유지 키트 투하·대피 안내 방송", "105-D"),
        "relay": ("요구조자 호위 지속", "105-D"),
        "clear": ("대피 완료 확인", "105-D"),
    },
    Squad.SUPPRESSION: {
        "deploy": ("진압 편대 전개", "105-D"),
        "assess": ("창문·진입점 파악", "222-D"),
        "operate": ("창문 파쇄 후 정밀 소화탄 투하", "222-D"),
        "relay": ("외벽 연소차단 유지", "105-D"),
        "clear": ("잔불 감시", "105-D"),
    },
    Squad.COMMS: {
        "deploy": ("고공 진입·조명 점등", "105-D"),
        "assess": ("Mesh 통신망 형성", "107-D"),
        "operate": ("음영지역 신호 중계·광역 조명", "105-D"),
        "relay": ("통신 중계 유지", "107-D"),
        "clear": ("통신망 유지", "107-D"),
    },
}


def squad_task(squad, phase):
    """편대가 지금 담당하는 임무 문구와 근거 SOP 코드."""
    table = _TASK.get(squad, {})
    return table.get(phase, ("대기", "105-D"))
