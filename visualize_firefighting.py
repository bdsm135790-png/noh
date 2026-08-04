"""소방 드론 화재 대응 시나리오 3D/2D 시각화.

Gazebo 같은 GUI 없이도 다음 흐름을 애니메이션(GIF)으로 확인한다.
  1) SUPPRESSOR가 화점으로 접근해 소화탄을 투하하고 GUIDE로 전환
  2) GUIDE가 계산한 화염 회피 A* 경로를 따라 요구조자가 비상구로 탈출

demo(firefighting_demo.py)의 장면 구성을 그대로 재사용한다.

실행:
    python3 visualize_firefighting.py            # firefighting.gif 생성
    python3 visualize_firefighting.py out.gif
"""

import sys

import numpy as np
import matplotlib

matplotlib.use("Agg")  # 헤드리스 렌더링
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.colors import ListedColormap

from firefighting_drone import FirefightingDrone, DroneRole
from firefighting_demo import make_thermal_scene, make_hazard_map


def _suppression_track(fire_pos, start=(0.0, 0.0, 0.0), payload=2,
                       max_speed=6.0, drop_range=3.0, steps=40):
    """SUPPRESSOR가 화점으로 접근하는 위치 궤적과 투하 스텝을 기록한다."""
    drone = FirefightingDrone("SUPP", role=DroneRole.SUPPRESSOR,
                              payload=payload, max_speed=max_speed)
    drone.pos = np.array(start, dtype=float)
    drone.fire_hotspot_pos = np.asarray(fire_pos, dtype=float)

    track = [drone.pos.copy()]
    drops = []  # (frame_index, remaining_payload)
    for i in range(steps):
        dropped = drone.execute_suppression_routine(drop_range=drop_range)
        track.append(drone.pos.copy())
        if dropped:
            drops.append((len(track) - 1, drone.payload_extinguisher))
        if drone.payload_extinguisher == 0 and dropped:
            break
    return np.array(track), drops, drone.role


def build_frames():
    """시나리오를 풀어 프레임별 상태를 만든다."""
    thermal = make_thermal_scene()
    hazard = make_hazard_map()
    exit_pos = [19.0, 19.0, 0.0]

    scout = FirefightingDrone("SCOUT", role=DroneRole.SCOUT)
    det = scout.process_thermal_and_vision(thermal)
    fire = det["fire"]
    survivor = det["survivor"]

    # 1) 진압 궤적.
    supp_track, drops, final_role = _suppression_track(fire)

    # 2) 탈출 경로.
    guide = FirefightingDrone("GUIDE", role=DroneRole.GUIDE)
    guide.target_survivor_pos = survivor
    path = guide.generate_escape_path(hazard, exit_pos)
    path = np.array(path) if path is not None else np.empty((0, 3))

    return {
        "thermal": thermal,
        "hazard": hazard,
        "fire": np.asarray(fire, dtype=float),
        "survivor": np.asarray(survivor, dtype=float),
        "exit": np.asarray(exit_pos, dtype=float),
        "supp_track": supp_track,
        "drops": drops,
        "path": path,
        "final_role": final_role,
    }


def render_gif(out_path="firefighting.gif", fps=6):
    s = build_frames()
    supp_track = s["supp_track"]
    path = s["path"]

    # 타임라인: [진압 단계] 이어서 [탈출 단계].
    n_supp = len(supp_track)
    n_path = len(path)
    total = n_supp + n_path + 4  # 마지막 여유 프레임

    hazard = s["hazard"]
    h, w = hazard.shape

    # 위험 셀을 반투명 빨강으로 오버레이할 컬러맵.
    hazard_cmap = ListedColormap([(1, 1, 1, 0.0), (1, 0.2, 0.1, 0.55)])

    fig, ax = plt.subplots(figsize=(7.5, 7.5))

    def draw(frame):
        ax.clear()
        ax.set_xlim(-1, w)
        ax.set_ylim(-1, h)
        ax.set_aspect("equal")
        ax.invert_yaxis()  # 행(row) 증가 = 아래로 (이미지 좌표계)
        ax.set_xlabel("X (col, m)")
        ax.set_ylabel("Y (row, m)")

        # 위험(화염) 영역.
        ax.imshow(hazard, cmap=hazard_cmap, origin="upper",
                  extent=(-0.5, w - 0.5, h - 0.5, -0.5), zorder=0)

        # 화점 / 요구조자(시작) / 비상구.
        fire, survivor, exit_p = s["fire"], s["survivor"], s["exit"]
        ax.scatter(fire[0], fire[1], marker="*", s=380, color="orangered",
                   edgecolors="k", linewidths=0.5, zorder=5, label="Fire")
        ax.scatter(survivor[0], survivor[1], marker="P", s=160, color="deepskyblue",
                   edgecolors="k", linewidths=0.5, zorder=5, label="Survivor")
        ax.scatter(exit_p[0], exit_p[1], marker="s", s=150, color="limegreen",
                   edgecolors="k", linewidths=0.5, zorder=5, label="Exit")

        phase = "Suppression"
        # --- 진압 단계 ---
        if frame < n_supp:
            k = frame
            seg = supp_track[:k + 1]
            ax.plot(seg[:, 0], seg[:, 1], "-", color="darkorange",
                    lw=1.8, alpha=0.9, zorder=4)
            cur = supp_track[k]
            ax.scatter(cur[0], cur[1], marker="^", s=180, color="darkorange",
                       edgecolors="k", linewidths=0.6, zorder=6,
                       label="SUPPRESSOR")
            # 이미 발생한 투하 표시.
            remaining = None
            for f_idx, rem in s["drops"]:
                if f_idx <= k:
                    ax.scatter(s["fire"][0], s["fire"][1], marker="o", s=90,
                               facecolors="none", edgecolors="yellow",
                               linewidths=2.0, zorder=7)
                    remaining = rem
            if remaining == 0:
                phase = "Suppression (payload empty -> switch to GUIDE)"
            info = "Dropping extinguisher  |  remaining: " \
                   f"{remaining if remaining is not None else '2'}"
        # --- 탈출 단계 ---
        else:
            phase = "Escape guidance"
            k = min(frame - n_supp, n_path - 1) if n_path else 0
            # 전체 계획 경로(연하게) + 지나온 경로(진하게).
            if n_path:
                ax.plot(path[:, 0], path[:, 1], "--", color="royalblue",
                        lw=1.2, alpha=0.4, zorder=3)
                seg = path[:k + 1]
                ax.plot(seg[:, 0], seg[:, 1], "-", color="royalblue",
                        lw=2.4, alpha=0.95, zorder=4)
                cur = path[k]
                ax.scatter(cur[0], cur[1], marker="P", s=180,
                           color="deepskyblue", edgecolors="k",
                           linewidths=0.6, zorder=6, label="Survivor moving")
            info = f"Following fire-avoiding A* path  |  waypoint {k + 1}/{n_path}"

        ax.set_title(
            f"Firefighting drone response  |  {phase}\n{info}",
            fontsize=11,
        )
        ax.legend(loc="upper left", fontsize=8, framealpha=0.85)
        ax.grid(True, alpha=0.15)
        return ax,

    anim = FuncAnimation(fig, draw, frames=total, interval=1000 / fps)
    anim.save(out_path, writer=PillowWriter(fps=fps))
    plt.close(fig)

    print(f"[OK] {out_path} 생성 완료 ({total} frames)")
    print(f"     진압 궤적 {n_supp} 스텝, 투하 {len(s['drops'])}회, "
          f"최종 역할 {s['final_role']}")
    print(f"     탈출 경로 웨이포인트 {n_path}개 (화염 회피)")


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "firefighting.gif"
    render_gif(out_path=out)
