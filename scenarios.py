"""화재 현장 드론 대응 5대 시나리오.

「소방청훈령 제119호」의 현장 안전관리 원칙(firefighting_doctrine)을 편대 행동으로
적용한 5개 케이스를 시뮬레이션한다. 이동/충돌회피는 기존 SwarmDrone·
FirefightingDrone 로직을 위임하는 MissionDrone 을 그대로 재사용한다.

  1) rescue    인명구조 (수색 → 발견 → 응급 → 호위 탈출)
  2) suppress  화재 초기대응 (사이즈업 → 초동 진압)
  3) flashover 플래시오버 경계·대피 (위험 상승 → 활동중지·대피 → 인원확인)  [제25조]
  4) mayday    대원 조난·신속동료구조 (조난 → RIT 전개 → 구출)             [제24·25조]
  5) hazmat    유해가스 누출 대응 (플룸 매핑 → 경계구역 → 풍상 대피/구조)   [제7·26조]

각 시나리오는 표준화된 결과 dict를 돌려주며 visualize_scenarios가 그린다.
"""

import numpy as np

from integrated_mission import MissionDrone, min_pairwise_distance
import firefighting_doctrine as doc
from firefighting_doctrine import Role


# ------------------------------------------------------------------
# 공통 헬퍼
# ------------------------------------------------------------------
def _agent(role, label, pos, payload=0):
    d = MissionDrone(label, role, np.array(pos, float), np.zeros(3), payload=payload)
    d.label = label
    d.accounted = True
    return d


def ring(center, radius, i, n, z=None):
    ang = 2 * np.pi * i / max(n, 1)
    c = np.asarray(center, float)
    p = c + np.array([radius * np.cos(ang), radius * np.sin(ang), 0.0])
    if z is not None:
        p[2] = z
    return p


def step_all(agents, goals, dt=0.5, safe_dist=4.5, goal_w=0.7, frozen=()):
    """각 에이전트를 자기 goal로 편대 이동(충돌 회피 포함)시킨다."""
    for a in agents:
        if a.label in frozen:
            continue
        nb = [o for o in agents if o is not a]
        goal = goals.get(a.label, a.pos)  # 미지정 기체는 현재 위치 유지
        a.flock_step(nb, goal, dt=dt, safe_dist=safe_dist, goal_w=goal_w)
    return min_pairwise_distance(agents)


class Recorder:
    """프레임별 위치/역할/상태를 축적한다."""

    def __init__(self, agents):
        self.positions = {a.label: [a.pos.copy()] for a in agents}
        self.roles = {a.label: [a.role] for a in agents}
        self.labels = {a.label: a.label for a in agents}
        self.status = []
        self.min_dist = [min_pairwise_distance(agents)]
        self.extras = {}

    def snap(self, agents, phase, headline, directive_key, **extra):
        for a in agents:
            self.positions[a.label].append(a.pos.copy())
            self.roles[a.label].append(a.role)
        self.min_dist.append(min_pairwise_distance(agents))
        self.status.append({"phase": phase, "headline": headline,
                            "directive": directive_key})
        for k, v in extra.items():
            self.extras.setdefault(k, []).append(v)

    def result(self, name, title, subtitle, landmarks, roster_note,
               hazard=None):
        return {
            "name": name, "title": title, "subtitle": subtitle,
            "positions": {k: np.array(v) for k, v in self.positions.items()},
            "roles": self.roles, "labels": self.labels,
            "landmarks": landmarks, "hazard": hazard,
            "frame_status": [self.status[0]] + self.status,  # step0 정렬
            "min_dist_series": np.array(self.min_dist),
            "extras": self.extras, "roster_note": roster_note,
        }


# ==================================================================
# 1) 인명구조
# ==================================================================
def scenario_rescue():
    fire = np.array([44.0, 40.0, 0.0])
    victim = np.array([16.0, 44.0, 0.0])
    exit_p = np.array([52.0, 12.0, 0.0])
    safe = np.array([50.0, 50.0, 12.0])   # 지휘 거점
    cmd = _agent(Role.COMMANDER, "CMD", safe)
    saf = _agent(Role.SAFETY, "SAF", [40, 50, 10])
    scouts = [_agent(Role.SCOUT, f"SCT{i+1}", ring([30, 30, 9], 8, i, 3))
              for i in range(3)]
    guide = _agent(Role.GUIDE, "GDE", [48, 48, 8])
    medic = _agent(Role.MEDIC, "MED", [50, 46, 8])
    rit = _agent(Role.RIT, "RIT", [52, 48, 8])
    agents = [cmd, saf] + scouts + [guide, medic, rit]

    rec = Recorder(agents)
    guide.plan_escape(_hazard_wall(fire), victim, exit_p)
    T_search, T_move, T_escort, T_clear = 26, 10, 22, 8
    found = False
    for step in range(1, T_search + T_move + T_escort + T_clear + 1):
        goals = {}
        # 정지 인원: 지휘/안전(안전은 선회).
        goals["CMD"] = safe
        goals["SAF"] = np.array([32, 40, 10]) + 6 * np.array(
            [np.cos(step * 0.25), np.sin(step * 0.25), 0])
        goals["RIT"] = [52, 48, 8]
        victim_pos = None

        if step <= T_search:
            phase, head, dkey = "search", \
                "SCOUTs sweeping the structure for survivors", "HAZARD_WATCH"
            # 좌우 스윕 수색 패턴.
            sweep_x = 12 + (step / T_search) * 26
            for i, s in enumerate(scouts):
                goals[s.label] = [sweep_x, 24 + i * 10, 9]
            goals["GDE"] = [48, 46, 8]; goals["MED"] = [50, 44, 8]
        elif step <= T_search + T_move:
            if not found:
                found = True
            phase, head, dkey = "found", \
                "Survivor located — MEDIC & GUIDE moving in", "INJURED_FIRST"
            for i, s in enumerate(scouts):
                goals[s.label] = ring(victim + [0, 0, 8], 9, i, 3)
            goals["GDE"] = victim + [3, 3, 6]; goals["MED"] = victim + [-3, 3, 6]
        elif step <= T_search + T_move + T_escort:
            phase, head, dkey = "escort", \
                "Escorting the survivor out along a safe path", "ACCOUNTABILITY"
            victim_pos = guide.escort_step(dt=1.0)
            goals["GDE"] = guide.pos  # escort_step가 직접 이동시킴
            goals["MED"] = guide.pos + [-1.5, 0, 0]
            for i, s in enumerate(scouts):
                goals[s.label] = ring([30, 30, 10], 8, i, 3)
        else:
            phase, head, dkey = "clear", \
                "Survivor at exit — all units accounted for", "SAFETY_FIRST"
            victim_pos = exit_p
            goals["GDE"] = exit_p + [1, 1, 5]; goals["MED"] = exit_p + [-1, 1, 5]
            for i, s in enumerate(scouts):
                goals[s.label] = ring([30, 30, 10], 8, i, 3)

        md = step_all(agents, goals, frozen=("GDE",) if victim_pos is not None else ())
        rec.snap(agents, phase, head, dkey,
                 victim=(victim_pos.copy() if victim_pos is not None else None))

    landmarks = {
        "fire": ("SMOKE", fire, "fire"),
        "victim0": ("last-seen", victim, "victim"),
        "exit": ("EXIT", exit_p, "exit"),
        "safe": ("Command", safe, "safe"),
    }
    return rec.result(
        "rescue", "Case 1 — Life Rescue (인명구조)",
        "Search -> locate -> triage -> escort out",
        landmarks, "CMD·SAF·SCT×3·GDE·MED·RIT",
        hazard=_hazard_wall(fire))


# ==================================================================
# 2) 화재 초기대응
# ==================================================================
def scenario_suppress():
    fire = np.array([40.0, 40.0, 2.0])
    safe = np.array([18.0, 20.0, 12.0])
    cmd = _agent(Role.COMMANDER, "CMD", safe)
    saf = _agent(Role.SAFETY, "SAF", [26, 30, 10])
    scout = _agent(Role.SCOUT, "SCT", [22, 26, 9])
    sup = [_agent(Role.SUPPRESSOR, f"SUP{i+1}", ring([20, 22, 8], 4, i, 2),
                  payload=3) for i in range(2)]
    ow = [_agent(Role.OVERWATCH, f"OW{i+1}", ring([20, 22, 11], 6, i, 2))
          for i in range(2)]
    agents = [cmd, saf, scout] + sup + ow

    rec = Recorder(agents)
    T_size, T_supp, T_clear = 14, 30, 8
    drops = 0
    for step in range(1, T_size + T_supp + T_clear + 1):
        goals = {"CMD": safe}
        goals["SAF"] = fire[:3] * 0 + np.array([30, 30, 10]) + 5 * np.array(
            [np.cos(step * 0.3), np.sin(step * 0.3), 0])
        # 비진압 기체는 위험도에 따른 안전 이격 밖에서 대기(제25·26조).
        standoff = doc.exclusion_radius(0.4)
        if step <= T_size:
            phase, head, dkey = "size-up", \
                "SCOUT sizing up the fire seat; crew staged at standoff", \
                "HAZARD_WATCH"
            goals["SCT"] = fire + [ -standoff, 2, 7]
            for i, s in enumerate(sup):
                goals[s.label] = ring([22, 24, 8], 4, i, 2)
        elif step <= T_size + T_supp:
            phase, head, dkey = "suppress", \
                "SUPPRESSORs knocking down the fire from separated angles", \
                "ROLE_IDENTIFICATION"
            goals["SCT"] = fire + [-standoff, 6, 7]
            for i, s in enumerate(sup):
                # 화점을 서로 다른 방향에서 접근.
                atk = fire + ring([0, 0, 0], 3.0, i, 2) + [0, 0, 0.5]
                goals[s.label] = atk
                if np.linalg.norm(s.pos - fire) < 3.5 and s.payload > 0 \
                        and step % 4 == 0:
                    s.payload -= 1; drops += 1
        else:
            phase, head, dkey = "overhaul", \
                "Knockdown complete — overhaul & accountability", \
                "ACCOUNTABILITY"
            for i, s in enumerate(sup):
                goals[s.label] = ring([24, 26, 8], 5, i, 2)
            goals["SCT"] = [26, 28, 8]
        for i, o in enumerate(ow):
            goals[o.label] = ring(fire + [0, 0, 9], standoff + 2, i, 2)

        md = step_all(agents, goals)
        rec.snap(agents, phase, head, dkey, drops=drops)

    landmarks = {
        "fire": ("FIRE seat", fire, "fire"),
        "safe": ("Command", safe, "safe"),
    }
    return rec.result(
        "suppress", "Case 2 — Fire Initial Response (화재 초기대응)",
        "Size-up -> early suppression -> overhaul",
        landmarks, "CMD·SAF·SCT·SUP×2·OW×2", hazard=None)


# ==================================================================
# 3) 플래시오버 경계·대피  [제25조]
# ==================================================================
def scenario_flashover():
    fire = np.array([40.0, 40.0, 2.0])
    safe = np.array([12.0, 12.0, 11.0])
    cmd = _agent(Role.COMMANDER, "CMD", [14, 14, 12])
    saf = _agent(Role.SAFETY, "SAF", [30, 30, 10])
    sup = [_agent(Role.SUPPRESSOR, f"SUP{i+1}", ring(fire, 5, i, 2, z=3),
                  payload=3) for i in range(2)]
    gde = _agent(Role.GUIDE, "GDE", [34, 34, 8])
    ow = [_agent(Role.OVERWATCH, f"OW{i+1}", ring([26, 26, 11], 5, i, 2))
          for i in range(2)]
    agents = [cmd, saf] + sup + [gde] + ow

    rec = Recorder(agents)
    T_work, T_warn, T_evac, T_acct = 18, 6, 20, 8
    total = T_work + T_warn + T_evac + T_acct
    for step in range(1, total + 1):
        # 위험지수: 작업이 진행될수록 상승.
        hazard_index = min(1.0, 0.15 + 0.9 * step / (T_work + T_warn))
        evac = doc.should_evacuate(hazard_index)
        excl = doc.exclusion_radius(hazard_index)
        goals = {"CMD": [14, 14, 12]}
        goals["SAF"] = np.array([30, 30, 10]) + 5 * np.array(
            [np.cos(step * 0.3), np.sin(step * 0.3), 0])

        if step <= T_work:
            phase, head, dkey = "working", \
                "Crew working the fire; SAFETY watching conditions", \
                "HAZARD_WATCH"
            for i, s in enumerate(sup):
                goals[s.label] = fire + ring([0, 0, 0], 4.0, i, 2) + [0, 0, 1]
            goals["GDE"] = fire + [-5, 5, 6]
        elif step <= T_work + T_warn:
            phase, head, dkey = "WARNING", \
                f"Flashover signs! hazard={hazard_index:.2f} — SAFETY broadcasts", \
                "HAZARD_WATCH"
            for s in sup:
                goals[s.label] = s.pos  # 잠깐 정지(경보 인지)
            goals["GDE"] = gde.pos
        elif step <= T_work + T_warn + T_evac:
            phase, head, dkey = "EVACUATE", \
                "Commander orders STOP-WORK — all units fall back to safe zone", \
                "STOP_WORK_AND_EVACUATE"
            # 전원 안전지대로 대피(경계구역 밖).
            for i, a in enumerate(agents):
                if a.role in (Role.COMMANDER,):
                    continue
                goals[a.label] = ring(safe, 6, i, len(agents), z=safe[2])
        else:
            phase, head, dkey = "accounted", \
                "All units clear of the collapse zone — accountability check", \
                "ACCOUNTABILITY"
            for i, a in enumerate(agents):
                if a.role in (Role.COMMANDER,):
                    continue
                goals[a.label] = ring(safe, 6, i, len(agents), z=safe[2])

        md = step_all(agents, goals, goal_w=0.85 if evac else 0.7)
        rec.snap(agents, phase, head, dkey,
                 hazard_index=hazard_index, exclusion=excl)

    landmarks = {
        "fire": ("FIRE / collapse zone", fire, "fire"),
        "safe": ("SAFE zone", safe, "safe"),
    }
    return rec.result(
        "flashover", "Case 3 — Flashover Watch & Evacuation (플래시오버 경계·대피)",
        "Work -> danger signs -> STOP-WORK & evacuate -> accountability  [Art.25]",
        landmarks, "CMD·SAF·SUP×2·GDE·OW×2", hazard=None)


# ==================================================================
# 4) 대원 조난·신속동료구조 (RIT)  [제24·25조]
# ==================================================================
def scenario_mayday():
    fire = np.array([42.0, 42.0, 2.0])
    safe = np.array([14.0, 16.0, 11.0])
    exit_p = np.array([10.0, 40.0, 0.0])
    cmd = _agent(Role.COMMANDER, "CMD", [14, 14, 12])
    saf = _agent(Role.SAFETY, "SAF", [30, 28, 10])
    sup = [_agent(Role.SUPPRESSOR, f"SUP{i+1}", ring(fire, 5, i, 2, z=3),
                  payload=3) for i in range(2)]
    rit = _agent(Role.RIT, "RIT", safe)      # 상시 대기(제24조2항)
    gde = _agent(Role.GUIDE, "GDE", [24, 22, 8])
    agents = [cmd, saf] + sup + [rit, gde]

    rec = Recorder(agents)
    T_work, T_mayday, T_reach, T_extract, T_clear = 14, 4, 12, 16, 6
    down_pos = None
    downed_label = "SUP2"
    gde.plan_escape(_hazard_wall(fire), fire + [-6, -4, 0], exit_p)
    total = T_work + T_mayday + T_reach + T_extract + T_clear
    for step in range(1, total + 1):
        goals = {"CMD": [14, 14, 12]}
        goals["SAF"] = np.array([30, 28, 10]) + 5 * np.array(
            [np.cos(step * 0.3), np.sin(step * 0.3), 0])
        frozen = ()
        downed_pt = down_pos

        if step <= T_work:
            phase, head, dkey = "working", \
                "Suppression underway; RIT staged & ready", "RIT_READY"
            for i, s in enumerate(sup):
                goals[s.label] = fire + ring([0, 0, 0], 4.0, i, 2) + [0, 0, 1]
            goals["RIT"] = safe; goals["GDE"] = [24, 22, 8]
        elif step <= T_work + T_mayday:
            if down_pos is None:
                down_pos = sup[1].pos.copy(); down_pos[2] = 0.0
                downed_pt = down_pos
                sup[1].role = "DOWNED"  # 드론 아이콘 대신 '조난 대원'으로 표시
            phase, head, dkey = "MAYDAY", \
                f"MAYDAY — {downed_label} down at the fire! RIT deploying", \
                "INJURED_FIRST"
            goals["SUP1"] = sup[0].pos  # 남은 진압대 잠깐 정지
            goals["RIT"] = down_pos + [0, 0, 6]
            goals["GDE"] = [22, 34, 7]
            frozen = (downed_label,)
        elif step <= T_work + T_mayday + T_reach:
            phase, head, dkey = "reach", \
                "RIT pushing in to the downed crew (injured-first)", \
                "INJURED_FIRST"
            goals["RIT"] = down_pos + [0, 0, 3]
            goals["SUP1"] = fire + [-6, 2, 3]
            goals["GDE"] = exit_p + [4, 2, 6]
            frozen = (downed_label,)
        elif step <= T_work + T_mayday + T_reach + T_extract:
            phase, head, dkey = "extract", \
                "RIT + GUIDE extracting the downed crew to the exit", \
                "INJURED_FIRST"
            wp = gde.escort_step(dt=1.0)
            downed_pt = wp
            goals["GDE"] = gde.pos
            goals["RIT"] = gde.pos + [0.5, -0.5, 2]
            goals["SUP1"] = fire + [-8, 0, 3]
            frozen = (downed_label, "GDE")
        else:
            phase, head, dkey = "clear", \
                "Downed crew rescued — all accounted for", "ACCOUNTABILITY"
            downed_pt = exit_p
            goals["GDE"] = exit_p + [2, 2, 5]; goals["RIT"] = exit_p + [-2, 2, 5]
            goals["SUP1"] = safe + [4, 0, 0]

        md = step_all(agents, goals, frozen=frozen)
        rec.snap(agents, phase, head, dkey,
                 downed=(downed_pt.copy() if downed_pt is not None else None))

    landmarks = {
        "fire": ("FIRE", fire, "fire"),
        "safe": ("Staging/Safe", safe, "safe"),
        "exit": ("EXIT", exit_p, "exit"),
    }
    return rec.result(
        "mayday", "Case 4 — Downed Crew & RIT Rescue (대원 조난·신속동료구조)",
        "Work -> MAYDAY -> RIT deploy -> extract downed crew  [Art.24/25]",
        landmarks, "CMD·SAF·SUP×2·RIT·GDE", hazard=_hazard_wall(fire))


# ==================================================================
# 5) 유해가스 누출 대응 (HAZMAT)  [제7·26조]
# ==================================================================
def scenario_hazmat():
    leak = np.array([38.0, 42.0, 0.0])       # 누출원
    victim = np.array([30.0, 26.0, 0.0])
    safe = np.array([10.0, 12.0, 11.0])      # 풍상(upwind) 안전지대
    wind = np.array([-1.0, -1.0, 0.0]) / np.sqrt(2)  # 풍향(남서로 확산)
    cmd = _agent(Role.COMMANDER, "CMD", [12, 14, 12])
    saf = _agent(Role.SAFETY, "SAF", [24, 24, 10])
    haz = _agent(Role.HAZMAT, "HZM", [30, 34, 9])
    scout = _agent(Role.SCOUT, "SCT", [26, 22, 9])
    gde = _agent(Role.GUIDE, "GDE", [22, 20, 8])
    ow = _agent(Role.OVERWATCH, "OW", [20, 18, 11])
    agents = [cmd, saf, haz, scout, gde, ow]

    rec = Recorder(agents)
    T_detect, T_zone, T_rescue, T_clear = 12, 10, 22, 8
    total = T_detect + T_zone + T_rescue + T_clear
    for step in range(1, total + 1):
        # 플룸: 누출원에서 시작해 시간에 따라 반경 확대 + 풍향으로 이동.
        prog = min(1.0, step / (T_detect + T_zone))
        plume_r = 4 + 12 * prog
        plume_c = leak + wind * (6 * prog)
        excl = plume_r + 3.0  # 경계구역 = 플룸 + 여유
        goals = {"CMD": [12, 14, 12]}
        goals["SAF"] = np.array([22, 22, 10]) + 5 * np.array(
            [np.cos(step * 0.3), np.sin(step * 0.3), 0])
        victim_pos = None

        def keep_upwind(target, z):
            """경계구역 안이면 풍상 쪽으로 밀어 안전 이격을 유지."""
            t = np.array([target[0], target[1], z], float)
            d = np.linalg.norm(t[:2] - plume_c[:2])
            if d < excl:
                push = (t[:2] - plume_c[:2])
                push = push / (np.linalg.norm(push) + 1e-9)
                t[:2] = plume_c[:2] + push * excl
            return t

        if step <= T_detect:
            phase, head, dkey = "detect", \
                "HAZMAT drone mapping the gas plume from the leak", \
                "HAZARD_WATCH"
            goals["HZM"] = keep_upwind(plume_c[:2] + [ -1, -1], 8)
            goals["SCT"] = keep_upwind([28, 24], 8)
            goals["GDE"] = keep_upwind([22, 20], 8)
            goals["OW"] = keep_upwind([20, 18], 11)
        elif step <= T_detect + T_zone:
            phase, head, dkey = "zone", \
                "Exclusion zone set — units pushed upwind of the plume", \
                "STOP_WORK_AND_EVACUATE"
            goals["HZM"] = keep_upwind(plume_c[:2] + [-2, -2], 8)
            goals["SCT"] = keep_upwind(victim[:2] + [2, -4], 8)
            goals["GDE"] = keep_upwind(victim[:2] + [-2, -4], 8)
            goals["OW"] = keep_upwind([18, 16], 11)
        elif step <= T_detect + T_zone + T_rescue:
            phase, head, dkey = "rescue", \
                "SCOUT found a civilian; GUIDE escorts upwind, clear of gas", \
                "INJURED_FIRST"
            # 요구조자를 풍상 안전지대로 유도(플룸 회피).
            frac = (step - T_detect - T_zone) / T_rescue
            victim_pos = victim + (safe - victim) * frac
            victim_pos = keep_upwind(victim_pos[:2], 0.0)
            goals["GDE"] = np.array([victim_pos[0], victim_pos[1], 6])
            goals["SCT"] = keep_upwind(victim_pos[:2] + [3, 1], 8)
            goals["HZM"] = keep_upwind(plume_c[:2] + [-2, -2], 8)
            goals["OW"] = keep_upwind([16, 14], 11)
        else:
            phase, head, dkey = "clear", \
                "Civilian upwind & safe; plume monitored — area controlled", \
                "SAFETY_FIRST"
            victim_pos = safe.copy(); victim_pos[2] = 0.0
            goals["GDE"] = safe + [2, 2, -3]; goals["SCT"] = safe + [4, 0, -3]
            goals["HZM"] = keep_upwind(plume_c[:2] + [-2, -2], 8)
            goals["OW"] = safe + [-2, 2, 0]

        md = step_all(agents, goals)
        rec.snap(agents, phase, head, dkey,
                 plume=(plume_c.copy(), float(plume_r)),
                 victim=(victim_pos.copy() if victim_pos is not None else None))

    landmarks = {
        "leak": ("LEAK", leak, "fire"),
        "victim0": ("civilian", victim, "victim"),
        "safe": ("Upwind SAFE", safe, "safe"),
    }
    return rec.result(
        "hazmat", "Case 5 — Hazmat Gas Leak (유해가스 누출 대응)",
        "Map plume -> exclusion zone -> upwind rescue  [Art.7/26]",
        landmarks, "CMD·SAF·HZM·SCT·GDE·OW", hazard=None)


def _hazard_wall(fire, shape=(60, 60)):
    """화점 주변 통행 불가(화염) 벽 — A* 경로가 우회하도록."""
    h = np.zeros(shape)
    fx, fy = int(fire[0]), int(fire[1])
    h[max(0, fy - 6):fy + 6, max(0, fx - 2):fx + 2] = 1
    return h


ALL_SCENARIOS = {
    "rescue": scenario_rescue,
    "suppress": scenario_suppress,
    "flashover": scenario_flashover,
    "mayday": scenario_mayday,
    "hazmat": scenario_hazmat,
}


def main():
    for name, fn in ALL_SCENARIOS.items():
        r = fn()
        print(f"[{name:9s}] {r['title']}")
        print(f"            frames={len(r['frame_status'])}  "
              f"min_dist={r['min_dist_series'].min():.2f} m  "
              f"units={len(r['labels'])}")


if __name__ == "__main__":
    main()
