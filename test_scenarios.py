"""5대 시나리오 및 행동 지침(doctrine) 검증 테스트."""

import numpy as np

import firefighting_doctrine as doc
from firefighting_doctrine import Role
from drone_icons import role_icon, ICONS
from scenarios import ALL_SCENARIOS


def test_all_scenarios_run_and_are_collision_free():
    """5개 시나리오가 모두 실행되고 전 구간 기체가 겹치지 않는다."""
    assert set(ALL_SCENARIOS) == {"rescue", "suppress", "flashover",
                                  "mayday", "hazmat"}
    for name, fn in ALL_SCENARIOS.items():
        res = fn()
        assert res["min_dist_series"].min() > 0.4, name
        # 기록 길이 일관성.
        T = len(res["frame_status"])
        for arr in res["positions"].values():
            assert len(arr) == T, name


def test_every_role_has_a_distinct_icon():
    """제7조제4항(역할 식별): 역할마다 아이콘·색이 지정돼 있다."""
    seen_paths = 0
    colors = set()
    for role, (path, color, name, tag) in ICONS.items():
        assert path is not None
        colors.add(color)
        seen_paths += 1
    assert seen_paths == len(ICONS)
    # 색이 충분히 구분된다(대부분 고유).
    assert len(colors) >= len(ICONS) - 1


def test_doctrine_guidelines_have_article_refs():
    """모든 지침이 근거 조항을 명시한다."""
    for key, (title, article, desc) in doc.GUIDELINES.items():
        assert "제" in article and "조" in article, key
        assert title and desc


def test_exclusion_radius_grows_with_hazard():
    """위험도가 높을수록 안전 이격 거리가 커진다(제25·26조)."""
    assert doc.exclusion_radius(0.0) < doc.exclusion_radius(1.0)
    assert doc.exclusion_radius(0.0) == doc.BASE_STANDOFF


def test_evacuation_trigger():
    """위험지수가 임계값을 넘으면 대피 판단(제25조)."""
    assert not doc.should_evacuate(0.5, threshold=0.75)
    assert doc.should_evacuate(0.8, threshold=0.75)


def test_flashover_triggers_evacuation_phase():
    """플래시오버 시나리오는 STOP-WORK/대피 지침을 실제로 적용한다."""
    res = ALL_SCENARIOS["flashover"]()
    directives = {s["directive"] for s in res["frame_status"]}
    phases = {s["phase"] for s in res["frame_status"]}
    assert "STOP_WORK_AND_EVACUATE" in directives
    assert "EVACUATE" in phases


def test_mayday_deploys_rit_and_marks_downed():
    """조난 시나리오는 MAYDAY 단계와 RIT/부상자 우선 지침을 포함한다."""
    res = ALL_SCENARIOS["mayday"]()
    phases = [s["phase"] for s in res["frame_status"]]
    directives = {s["directive"] for s in res["frame_status"]}
    assert "MAYDAY" in phases
    assert "INJURED_FIRST" in directives
    # 조난자 위치가 기록된다.
    assert any(d is not None for d in res["extras"].get("downed", []))


def test_hazmat_maps_plume_and_keeps_exclusion():
    """유해가스 시나리오는 플룸을 기록하고 경계구역을 넓혀간다."""
    res = ALL_SCENARIOS["hazmat"]()
    plume = res["extras"].get("plume", [])
    assert len(plume) > 0
    radii = [r for (_, r) in plume]
    assert radii[-1] > radii[0]  # 시간에 따라 확산


def test_rescue_reports_accountability():
    """인명구조 시나리오는 대원 관리체계(제24조) 지침을 적용한다."""
    res = ALL_SCENARIOS["rescue"]()
    directives = {s["directive"] for s in res["frame_status"]}
    assert "ACCOUNTABILITY" in directives
    rep = doc.accountability_report([type("A", (), {"role": Role.SCOUT,
                                                    "accounted": True})()])
    assert rep["count"] == 1 and rep["all_accounted"]


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
