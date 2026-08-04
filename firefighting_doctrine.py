"""소방 드론 행동 지침(Doctrine).

「소방공무원 현장 소방활동 안전관리에 관한 규정」(소방청훈령 제119호, 2020.1.23.)의
현장 안전관리 원칙을 **드론 편대의 활동 지침**으로 변형해 코드화한 것이다.
각 지침은 근거 조항을 함께 기록한다.

핵심 매핑
---------
  제3조제1항제14호 (안전관리: 예방 + 피해 최소화)  -> SAFETY_FIRST
  제3조제1항제 7호 (아차사고)                       -> NEAR_MISS 기록
  제3조제1항제21호 / 제24조제2항 (신속동료구조팀)   -> RIT_READY / RIT 전개
  제7조제2·3항 (위험요인 관측·보고·전파)            -> HAZARD_WATCH (상시 감시·전파)
  제7조제4항 (안전점검관은 구분되게 착용)           -> ROLE_IDENTIFICATION (역할별 아이콘)
  제24조제1항 (대원 수·위치·시간 파악·관리)         -> ACCOUNTABILITY
  제25조제1·2항 (위험 시 활동 중지·대피)            -> STOP_WORK_AND_EVACUATE
  제25조제3항 (사고 대원 최우선 응급조치)           -> INJURED_FIRST
  제28조 (안전수칙 위반 즉시 시정)                  -> CORRECTIVE_ACTION
"""

import numpy as np


# ------------------------------------------------------------------
# 역할(현장 편성) — 제7조/제24조의 지휘·안전 편성을 드론 역할로 반영
# ------------------------------------------------------------------
class Role:
    COMMANDER = "COMMANDER"      # 현장지휘관: 지휘·통제, 안전 거점에서 총괄
    SAFETY = "SAFETY"            # 현장안전점검관/안전담당: 위험요인 관측·전파
    SCOUT = "SCOUT"              # 정찰·탐지: 화점/요구조자 수색
    SUPPRESSOR = "SUPPRESSOR"    # 진압: 화점 초동 진압
    GUIDE = "GUIDE"              # 안내·호위: 요구조자/대원 탈출 유도
    RIT = "RIT"                  # 신속동료구조팀: 조난 대원 구조
    HAZMAT = "HAZMAT"            # 유해가스·위험물 탐지, 경계구역 설정
    OVERWATCH = "OVERWATCH"      # 경계: 편대 유지, 상공 감시
    MEDIC = "MEDIC"             # 구급: 요구조자 응급 처치 지원


# ------------------------------------------------------------------
# 활동 지침(Guideline) 메타데이터 — 근거 조항 포함
# ------------------------------------------------------------------
GUIDELINES = {
    "SAFETY_FIRST": (
        "안전 최우선", "제3조제1항제14호",
        "사고를 예방하고 발생 시 피해를 최소화한다."),
    "HAZARD_WATCH": (
        "위험요인 관측·보고·전파", "제7조제2·3항",
        "SAFETY 드론이 위험요인을 상시 관측하고 전 편대에 전파한다."),
    "ROLE_IDENTIFICATION": (
        "역할 식별", "제7조제4항",
        "역할마다 구분되는 아이콘으로 임무를 즉시 식별할 수 있게 한다."),
    "ACCOUNTABILITY": (
        "대원 관리체계", "제24조제1항",
        "전 기체의 수·위치·활동시간을 상시 파악·관리한다."),
    "RIT_READY": (
        "신속동료구조팀 대기", "제3조제1항제21호·제24조제2항",
        "조난 발생에 대비해 RIT 드론을 상시 대기시킨다."),
    "STOP_WORK_AND_EVACUATE": (
        "위험 시 활동 중지·대피", "제25조제1·2항",
        "위험 판단 시 즉시 활동을 중지하고 안전지대로 대피한다."),
    "INJURED_FIRST": (
        "사고 대원 최우선", "제25조제3항",
        "조난·부상 대원에 대한 구조·응급조치를 최우선으로 한다."),
    "CORRECTIVE_ACTION": (
        "즉시 시정", "제28조",
        "안전수칙 위반·위험 상황을 확인하면 즉시 시정한다."),
    "NEAR_MISS": (
        "아차사고 기록", "제3조제1항제7호",
        "충돌·근접 등 아차사고를 기록해 재발을 방지한다."),
}


# 역할별 기본 활동 지침(현장 표시용 영어 문구 + 근거).
ROLE_DIRECTIVE = {
    Role.COMMANDER: ("Command & control from a safe vantage", "제24조"),
    Role.SAFETY: ("Watch & broadcast hazards to the team", "제7조"),
    Role.SCOUT: ("Search for fire seat & survivors", "제7조"),
    Role.SUPPRESSOR: ("Knock down the fire seat early", "제3조"),
    Role.GUIDE: ("Lead survivors/crew out along a safe path", "제25조"),
    Role.RIT: ("Rescue downed crew first", "제24·25조"),
    Role.HAZMAT: ("Map the plume, set the exclusion zone", "제7·26조"),
    Role.OVERWATCH: ("Hold formation, keep watch", "제24조"),
    Role.MEDIC: ("Triage & stabilize the survivor", "제25조"),
}


# ------------------------------------------------------------------
# 지침을 실제로 구현하는 헬퍼(행동에 영향을 주는 규칙)
# ------------------------------------------------------------------
# 위험도(0~1)에 따른 안전 이격 거리(m). 위험할수록 더 멀리 선다.
#   제25조: 위험 시 대피 / 제26조: 안전장애요인 제거
BASE_STANDOFF = 6.0
MAX_STANDOFF = 16.0


def exclusion_radius(hazard_level):
    """위험도(0~1)에 대한 안전 이격(경계구역) 반경(m). 제25·26조."""
    h = float(np.clip(hazard_level, 0.0, 1.0))
    return BASE_STANDOFF + (MAX_STANDOFF - BASE_STANDOFF) * h


def should_evacuate(hazard_index, threshold=0.75):
    """위험지수가 임계값을 넘으면 활동 중지·대피 판단. 제25조제1·2항."""
    return float(hazard_index) >= float(threshold)


def rit_should_deploy(mayday):
    """조난(매몰·고립·실종) 신호가 있으면 RIT 전개. 제24조제2항."""
    return bool(mayday)


def accountability_report(agents):
    """전 기체의 수·위치를 요약(대원 관리체계). 제24조제1항.

    Returns
    -------
    dict : {"count", "by_role", "all_accounted"}
    """
    by_role = {}
    for a in agents:
        by_role[a.role] = by_role.get(a.role, 0) + 1
    return {
        "count": len(agents),
        "by_role": by_role,
        "all_accounted": all(getattr(a, "accounted", True) for a in agents),
    }


def directive_for(role):
    """역할의 현장 표시용 지침 문구와 근거 조항."""
    return ROLE_DIRECTIVE.get(role, ("Support the mission", "제3조"))
