"""가정집 화재 — 드론 군집 SOP-D 대응 미션(3D, 장애물 포함).

「드론 군집체계 재난현장 SOP」를 단독주택 화재에 적용한다.
  - SOP 105-D 4편대(정찰/수색구조/진압/통신) + GCS 지휘.
  - SOP 102-D 공중 3D 스캐닝으로 화점·요구조자 탐지.
  - SOP 103-D 무중단 배터리 릴레이(25% 이하 예비기 전진배치·임무 이양·RTH).
  - SSG-D 100 기체 간 3m 반발 회피 + 장애물(벽/가구) 회피.
  - 각 편대의 실시간 담당 임무를 프레임마다 기록한다.
"""

import numpy as np

from integrated_mission import MissionDrone, min_pairwise_distance
from house_scene import HouseScene
import sop_doctrine as sop
from sop_doctrine import Squad


def _unit(squad, label, pos, battery=100.0, state="active"):
    d = MissionDrone(label, squad, np.array(pos, float), np.zeros(3))
    d.label = label
    d.squad = squad
    d.battery = float(battery)
    d.state = state          # active | spare | rth | ground
    return d


def _step(units, goals, house, dt=0.5):
    """편대를 goal로 이동 + 장애물/기체 반발 회피(SSG-D 100)."""
    movers = [u for u in units if u.state in ("active", "rth")]
    for u in movers:
        nb = [o for o in units if o is not u]
        u.flock_step(nb, goals[u.label], dt=dt, safe_dist=3.5, goal_w=0.85)
        # 장애물(벽/가구) 회피.
        u.pos = u.pos + house.repel(u.pos)
        # 기체 간 3m 반발(Fail-Safe).
        u.pos = u.pos + 0.5 * sop.repulsive_avoidance(
            u.pos, [o.pos for o in nb])
    return min_pairwise_distance(units) if len(units) > 1 else 9.9


def _drain(u):
    """상태별 배터리 갱신."""
    if u.state == "active":
        u.battery = max(0.0, u.battery - 0.7)
    elif u.state == "rth":
        u.battery = max(0.0, u.battery - 0.4)
    elif u.state in ("spare", "ground"):
        u.battery = min(100.0, u.battery + 2.0)   # 패드에서 충전


def _perimeter(center, radius, ang, z):
    return np.array([center[0] + radius * np.cos(ang),
                     center[1] + radius * np.sin(ang), z])


def run_house_mission():
    h = HouseScene()
    Z = h.transit_alt
    center = np.array([h.W / 2, h.D / 2, 0])
    pad = h.pad

    gcs = _unit(Squad.GCS, "GCS", pad + [3.5, 3.5, 1])
    recon_a = _unit(Squad.RECON, "정찰-A", pad + [0, 2, 1], battery=42.0)
    recon_b = _unit(Squad.RECON, "정찰-B(예비)", pad + [2.5, 0, 1],
                    battery=100.0, state="spare")
    sar = _unit(Squad.SAR, "수색구조", pad + [-2.5, 2, 1])
    sup = _unit(Squad.SUPPRESSION, "진압", pad + [-2.5, -1, 1])
    comms = _unit(Squad.COMMS, "통신조명", pad + [0, -2.5, 1])
    units = [gcs, recon_a, recon_b, sar, sup, comms]

    # 요구조자 대피 경로(침실→현관→집 밖 집결지).
    vic_path = [h.survivor.copy(), np.array([2.0, 3.0, 0.0]),
                h.door.copy(), h.exit.copy()]

    positions = {u.label: [u.pos.copy()] for u in units}
    roles = {u.label: [u.role] for u in units}
    labels = {u.label: u.label for u in units}
    status = []
    unit_status = []
    min_dist = [9.9]
    extras = {"survivor": [], "drops": [], "fire_level": []}

    Td, Ta, To, Tc = 10, 12, 30, 8
    total = Td + Ta + To + Tc
    relay_started = None
    relay_done = False
    drops = 0
    last_drop = -10
    fire_level = 1.0

    for step in range(1, total + 1):
        goals = {}
        # 지휘부는 패드 지휘소 고정.
        goals["GCS"] = pad + [3.5, 3.5, 1.5]

        # 기본 단계 판정.
        if step <= Td:
            phase = "deploy"
        elif step <= Td + Ta:
            phase = "assess"
        elif step <= Td + Ta + To:
            phase = "operate"
        else:
            phase = "clear"

        # ---- 배터리 릴레이 판정(SOP 103-D) ----
        if (relay_started is None and recon_a.state == "active"
                and sop.needs_relay(recon_a.battery) and phase in ("operate",)):
            relay_started = step
            recon_b.state = "active"          # 예비기 전진 배치
            recon_a.state = "rth"             # 기존기 복귀 준비
        relay_active = (relay_started is not None and not relay_done
                        and step <= (relay_started or 0) + 8)
        if relay_active:
            phase = "relay"

        # ---- 정찰 편대 순회 각도 ----
        ang = 0.6 * step
        recon_post = _perimeter(center, 11.0, ang, Z)

        # ---- 단계별 목표 배정 ----
        if phase == "deploy":
            head = "GCS 공중지휘권 확립 — 편대 이륙·현장 전개"
            goals["정찰-A"] = _perimeter(center, 11.0, ang, Z)
            goals["수색구조"] = center + [-11, 4, Z]
            goals["진압"] = center + [4, -11, Z]
            goals["통신조명"] = center + [0, 0, Z + 4]
        elif phase == "assess":
            head = "1편대 3D 스캐닝 — 화점·고립 구조대상자 탐지"
            goals["정찰-A"] = recon_post
            goals["수색구조"] = np.array([-3.0, 9.5, Z])   # 침실1 창 대기
            goals["진압"] = np.array([12.0, -3.0, Z])       # 주방 창 대기
            goals["통신조명"] = center + [0, 0, Z + 4]
        elif phase in ("operate", "relay"):
            head = "동시 대응 — 진압/구조/정찰/통신 병행"
            # 진압: 주방 창으로 접근, 사거리 도달 시 소화탄 투하(쿨다운 4스텝).
            goals["진압"] = h.windows["kitchen"] + [0, -0.5, 0]
            if (np.linalg.norm(sup.pos - h.windows["kitchen"]) < 2.5
                    and step - last_drop >= 4 and drops < 3):
                drops += 1
                last_drop = step
                fire_level = max(0.0, fire_level - 0.34)
            # 수색구조: 침실 창 접근 후 요구조자 대피 유도.
            goals["수색구조"] = h.windows["bed1"] + [0, 0, 0]
            # 정찰: 순회 감시(릴레이 중이면 A는 복귀).
            if recon_a.state == "rth":
                goals["정찰-A"] = pad + [0, 2, sop.rth_altitude(Squad.RECON) / 10]
                if np.linalg.norm(recon_a.pos[:2] - pad[:2]) < 2.0:
                    recon_a.state = "ground"; relay_done = True
            else:
                goals["정찰-A"] = recon_post
            goals["정찰-B(예비)"] = recon_post if recon_b.state == "active" \
                else pad + [2.5, 0, 1]
            goals["통신조명"] = center + [0, 0, Z + 4]
        else:  # clear
            head = "화점 진압·요구조자 대피 완료 — 편대 감시 유지/RTH"
            goals["정찰-A"] = pad + [0, 2, 1] if recon_a.state == "ground" \
                else recon_post
            goals["정찰-B(예비)"] = recon_post
            goals["수색구조"] = h.exit + [0, -1, Z - 2]
            goals["진압"] = h.windows["kitchen"] + [0, -2, 2]
            goals["통신조명"] = center + [0, 0, Z + 4]

        # ---- 요구조자 이동(구조 착수 후) ----
        victim_pos = None
        op_start = Td + Ta
        if step > op_start + 6:   # 키트 투하·안내 시작 후
            prog = np.clip((step - op_start - 6) / (To + Tc - 6), 0, 1)
            seg = prog * (len(vic_path) - 1)
            i = int(np.floor(seg)); frac = seg - i
            i = min(i, len(vic_path) - 2)
            victim_pos = vic_path[i] * (1 - frac) + vic_path[i + 1] * frac

        md = _step(units, goals, h)
        for u in units:
            _drain(u)

        # ---- 기록 ----
        for u in units:
            positions[u.label].append(u.pos.copy())
            roles[u.label].append(u.role)
        min_dist.append(md)
        status.append({"phase": phase, "headline": head})
        extras["survivor"].append(victim_pos.copy() if victim_pos is not None else None)
        extras["drops"].append(drops)
        extras["fire_level"].append(fire_level)

        # ---- 실시간 편대 담당 임무 ----
        us = {}
        for u in units:
            task, code = sop.squad_task(u.squad, phase)
            if u.label == "정찰-A" and u.state in ("rth", "ground"):
                task, code = "임무 이양 후 RTH(복귀고도 50m)", "109-D"
            if u.label == "정찰-B(예비)":
                if u.state == "active":
                    task, code = "정찰 임무 인계·화점 모니터링", "103-D"
                else:
                    task, code = "패드 대기·충전(예비기)", "103-D"
            if u.label == "진압" and phase in ("operate", "relay"):
                task = f"창문 파쇄·소화탄 투하 (투하 {drops}회)"
            us[u.label] = {"task": task, "code": code,
                           "battery": round(u.battery, 1), "state": u.state}
        unit_status.append(us)

    landmarks = {
        "fire": ("화점(주방)", h.fire, "fire"),
        "survivor0": ("요구조자(침실1)", h.survivor, "victim"),
        "exit": ("대피 집결지", h.exit, "exit"),
        "pad": ("GCS/드론 패드", h.pad, "safe"),
    }
    return {
        "name": "house", "title": "가정집 화재 — 드론 군집 SOP-D 대응",
        "subtitle": "SOP 105-D 4편대 · 103-D 배터리 릴레이 · SSG-D 100 장애물/충돌 회피",
        "positions": {k: np.array(v) for k, v in positions.items()},
        "roles": roles, "labels": labels,
        "landmarks": landmarks, "house": h,
        "frame_status": [status[0]] + status,
        "unit_status": [unit_status[0]] + unit_status,
        "min_dist_series": np.array(min_dist),
        "extras": extras,
        "roster_note": "GCS·1편대(정찰A+예비B)·2편대(수색구조)·3편대(진압)·4편대(통신조명)",
    }


def main():
    r = run_house_mission()
    print(r["title"])
    print(f"  frames={len(r['frame_status'])}  units={len(r['labels'])}  "
          f"min_dist={r['min_dist_series'].min():.2f} m")
    # 릴레이 발생 확인.
    a_states = [fr["정찰-A"]["state"] for fr in r["unit_status"]]
    print(f"  정찰-A 상태 변화: {sorted(set(a_states))}")
    print(f"  최종 소화탄 투하: {r['extras']['drops'][-1]}회, "
          f"화재 강도: {r['extras']['fire_level'][-1]:.2f}")


if __name__ == "__main__":
    main()
