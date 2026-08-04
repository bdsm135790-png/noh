"""통합 임무(스웜 + 소방) 시나리오 검증 테스트."""

import numpy as np

from firefighting_drone import DroneRole
from integrated_mission import run_mission, make_scene_hazard, MissionDrone


def test_no_collision_during_mission():
    """전 구간에서 어떤 두 기체도 겹치지 않는다(최소 간격 > 0)."""
    res = run_mission()
    assert res["min_dist_series"].min() > 0.0


def test_fleet_converges_on_approach():
    """접근 단계가 끝나면 편대가 집결점 근처로 모인다(초기보다 뭉침)."""
    res = run_mission()
    approach = res["approach_steps"]
    ids = list(res["positions"].keys())

    def spread(step):
        pts = np.array([res["positions"][i][step] for i in ids])
        return np.linalg.norm(pts - pts.mean(axis=0), axis=1).mean()

    assert spread(approach) < spread(0)


def test_suppressors_deplete_and_switch_to_guide():
    """진압 드론은 소화탄을 모두 쓰고 GUIDE로 자율 전환한다."""
    res = run_mission()
    # 초기 진압 드론 수.
    initial_supp = sum(1 for i in res["roles"] if res["roles"][i][0] == DroneRole.SUPPRESSOR)
    assert initial_supp == 2
    # 종료 시 진압 드론은 남지 않고 모두 GUIDE로 전환.
    final_supp = sum(1 for d in res["fleet"] if d.role == DroneRole.SUPPRESSOR)
    assert final_supp == 0
    assert all(d.payload == 0 for d in res["fleet"]
               if res["roles"][d.id][0] == DroneRole.SUPPRESSOR)


def test_guide_plans_escape_path():
    """GUIDE는 화염을 회피하는 탈출 경로를 만들어낸다."""
    res = run_mission()
    assert any("탈출 경로" in txt for _, txt in res["events"])


def test_escape_path_avoids_hazard():
    """계획된 탈출 경로는 화염(위험) 셀을 통과하지 않는다."""
    hazard = make_scene_hazard()
    guide = MissionDrone("g", DroneRole.GUIDE, [0, 0, 0], [0, 0, 0])
    path = guide.plan_escape(hazard, survivor_pos=[36, 44, 0], exit_pos=[50, 50, 0])
    assert path is not None
    for wp in path:
        col, row = int(round(wp[0])), int(round(wp[1]))
        assert hazard[row, col] <= 0


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
