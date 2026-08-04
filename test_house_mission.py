"""가정집 SOP-D 미션 및 SOP 지침 검증 테스트."""

import numpy as np

import sop_doctrine as sop
from sop_doctrine import Squad
from house_scene import HouseScene
from house_mission import run_house_mission


def test_sop_rth_altitudes_are_tiered():
    """SOP 109-D: 편대별 복귀 고도가 서로 다르다(공중 충돌 방지)."""
    alts = [sop.rth_altitude(s) for s in
            (Squad.RECON, Squad.SAR, Squad.SUPPRESSION, Squad.COMMS)]
    assert len(set(alts)) == 4
    assert sop.rth_altitude(Squad.RECON) < sop.rth_altitude(Squad.COMMS)


def test_battery_thresholds():
    """SOP 103-D / SSG-D 100 배터리 임계값 판정."""
    assert sop.needs_relay(25.0) and sop.needs_relay(20.0)
    assert not sop.needs_relay(40.0)
    assert sop.emergency_land(9.0) and not sop.emergency_land(15.0)


def test_repulsive_avoidance_pushes_apart():
    """SSG-D 100: 3m 이내 접근 시 반발 벡터가 멀어지는 방향."""
    f = sop.repulsive_avoidance([0, 0, 0], [[1.0, 0, 0]], dist=3.0)
    assert f[0] < 0  # +x의 이웃 → -x로 밀림
    # 3m 밖이면 반발 없음.
    assert np.allclose(sop.repulsive_avoidance([0, 0, 0], [[5, 0, 0]]), 0)


def test_house_has_obstacles_and_repels():
    """가정집에 장애물이 있고, 벽 안쪽에서는 밀어내는 힘이 작용한다."""
    h = HouseScene()
    assert len(h.obstacle_boxes()) >= 6
    # 외벽 내부 낮은 고도 지점 → 바깥으로 미는 벡터가 0이 아님.
    push = h.repel(np.array([0.2, 6.0, 1.0]))
    assert np.linalg.norm(push) > 0


def test_mission_runs_collision_free():
    """미션이 실행되고 기체 간 충돌이 없다(SSG-D 100 자율 회피)."""
    r = run_house_mission()
    assert r["min_dist_series"].min() > sop.REPULSE_DIST_M - 2.0  # >~1 m
    assert r["min_dist_series"].min() > 0.5
    T = len(r["frame_status"])
    for arr in r["positions"].values():
        assert len(arr) == T


def test_battery_relay_actually_happens():
    """SOP 103-D: 정찰-A가 25% 이하로 릴레이되어 RTH하고 예비기가 인계."""
    r = run_house_mission()
    a_states = {fr["정찰-A"]["state"] for fr in r["unit_status"]}
    b_states = {fr["정찰-B(예비)"]["state"] for fr in r["unit_status"]}
    assert "rth" in a_states          # A는 복귀 상태를 거친다
    assert "active" in b_states       # 예비기 B가 활성화(전진 배치)된다


def test_realtime_tasks_present_for_every_unit():
    """모든 프레임에서 편대별 실시간 담당 임무가 기록된다."""
    r = run_house_mission()
    for fr in r["unit_status"]:
        for label, info in fr.items():
            assert info["task"] and info["code"]
            assert 0 <= info["battery"] <= 100


def test_suppression_knocks_down_fire():
    """진압 편대가 소화탄을 투하해 화재 강도가 낮아진다."""
    r = run_house_mission()
    assert r["extras"]["drops"][-1] >= 1
    assert r["extras"]["fire_level"][-1] < 1.0


if __name__ == "__main__":
    import sys
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn(); print(f"PASS {name}")
            except AssertionError as exc:
                failures += 1; print(f"FAIL {name}: {exc}")
    sys.exit(1 if failures else 0)
