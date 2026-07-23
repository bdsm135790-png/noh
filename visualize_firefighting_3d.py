"""소방 드론 화재 대응 3D 시각화.

firefighting_drone.py의 실제 메서드를 그대로 구동해 드론의 움직임을
3차원 공간에서 애니메이션(GIF)으로 렌더링한다.

  1) SUPPRESSOR가 상공에서 화점(3D)으로 하강·접근해 소화탄을 투하하고
     GUIDE로 자율 전환한다. (FirefightingDrone.execute_suppression_routine)
  2) 요구조자가 다층 건물의 화염을 피해 층간(z=0->1->2) A* 경로로
     비상구까지 탈출한다. (FirefightingDrone.generate_escape_path, 3D)

실행:
    python3 visualize_firefighting_3d.py            # firefighting_3d.gif
    python3 visualize_firefighting_3d.py out.gif
"""

import sys

import numpy as np
import matplotlib

matplotlib.use("Agg")  # 헤드리스 렌더링
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter

from firefighting_drone import FirefightingDrone, DroneRole


def suppression_track_3d(fire_pos, start, payload=2, max_speed=4.0,
                         drop_range=3.0, steps=60):
    """SUPPRESSOR가 3D 화점으로 접근하는 궤적과 투하 스텝을 기록한다."""
    drone = FirefightingDrone("SUPP", role=DroneRole.SUPPRESSOR,
                              payload=payload, max_speed=max_speed)
    drone.pos = np.array(start, dtype=float)
    drone.fire_hotspot_pos = np.asarray(fire_pos, dtype=float)

    track = [drone.pos.copy()]
    drops = []
    for _ in range(steps):
        dropped = drone.execute_suppression_routine(drop_range=drop_range)
        track.append(drone.pos.copy())
        if dropped:
            drops.append(len(track) - 1)
        if drone.payload_extinguisher == 0 and dropped:
            break
    return np.array(track), drops, drone.role


def escape_path_3d(survivor_cell, exit_cell, hazard3d, cell_size=1.0):
    """3D A*로 층간 탈출 경로(월드 웨이포인트)를 만든다."""
    guide = FirefightingDrone("GUIDE", role=DroneRole.GUIDE)
    guide.target_survivor_pos = np.asarray(survivor_cell, dtype=float) * cell_size
    exit_world = np.asarray(exit_cell, dtype=float) * cell_size
    path = guide.generate_escape_path(hazard3d, exit_pos=exit_world,
                                      cell_size=cell_size)
    return np.array(path) if path is not None else np.empty((0, 3))


def build_scene():
    # 3개 층(z=0,1,2), 각 층 6x6. 0층에 화염 벽, 요구조자는 0층 구석.
    hazard3d = np.zeros((3, 6, 6))
    hazard3d[0, 0:5, 3] = 1  # 0층 화염 벽(계단으로 우회 필요)

    # 화점(3D): 0층 화염 벽 중앙 부근 상공에서 진압.
    fire = np.array([3.0, 2.0, 0.0])
    supp_start = np.array([0.0, 5.0, 6.0])  # 상공에서 진입

    supp_track, supp_drops, final_role = suppression_track_3d(fire, supp_start)

    # 요구조자: 0층 (0,0,0) -> 비상구 2층 (5,5,2).
    path = escape_path_3d(survivor_cell=(0, 0, 0), exit_cell=(5, 5, 2),
                          hazard3d=hazard3d)

    return {
        "hazard3d": hazard3d,
        "fire": fire,
        "supp_track": supp_track,
        "supp_drops": supp_drops,
        "final_role": final_role,
        "path": path,
        "exit": np.array([5.0, 5.0, 2.0]),
        "survivor_start": np.array([0.0, 0.0, 0.0]),
    }


def render_gif(out_path="firefighting_3d.gif", fps=6):
    s = build_scene()
    supp_track = s["supp_track"]
    path = s["path"]
    hazard3d = s["hazard3d"]

    n_supp = len(supp_track)
    n_path = len(path)
    total = n_supp + n_path + 4

    # 축 범위(건물 전체 + 진압 드론 진입 고도 포함).
    all_pts = np.vstack([
        supp_track,
        path if n_path else np.empty((0, 3)),
        s["fire"][None, :],
        s["exit"][None, :],
    ])
    lo = all_pts.min(axis=0) - 1
    hi = all_pts.max(axis=0) + 1

    # 층별 화염 셀 좌표(막대 표시용).
    fire_cells = np.argwhere(hazard3d > 0)  # (z, row, col)

    fig = plt.figure(figsize=(8, 8))
    ax = fig.add_subplot(111, projection="3d")

    def draw(frame):
        ax.clear()
        ax.set_xlim(lo[0], hi[0])
        ax.set_ylim(lo[1], hi[1])
        ax.set_zlim(min(lo[2], 0), hi[2])
        ax.set_xlabel("X (m)")
        ax.set_ylabel("Y (m)")
        ax.set_zlabel("Z / floor (m)")

        # 건물 층 바닥(반투명 평면)으로 다층 구조를 표현.
        xx, yy = np.meshgrid(np.linspace(0, 5, 2), np.linspace(0, 5, 2))
        for z in range(hazard3d.shape[0]):
            ax.plot_surface(xx, yy, np.full_like(xx, z), alpha=0.06,
                            color="gray", zorder=0)

        # 화염 셀(빨강 마커).
        if len(fire_cells):
            fz, fr, fc = fire_cells[:, 0], fire_cells[:, 1], fire_cells[:, 2]
            ax.scatter(fc, fr, fz, color="red", marker="s", s=55, alpha=0.6,
                       label="Hazard/Fire cells")

        # 화점 / 비상구 / 요구조자 시작점.
        fire, exit_p, sv = s["fire"], s["exit"], s["survivor_start"]
        ax.scatter(*fire, marker="*", s=360, color="orangered",
                   edgecolors="k", linewidths=0.5, label="Fire hotspot")
        ax.scatter(*exit_p, marker="s", s=140, color="limegreen",
                   edgecolors="k", linewidths=0.5, label="Exit (floor 2)")

        phase = "Suppression"
        if frame < n_supp:
            k = frame
            seg = supp_track[:k + 1]
            ax.plot(seg[:, 0], seg[:, 1], seg[:, 2], "-", color="darkorange",
                    lw=1.8, alpha=0.9)
            cur = supp_track[k]
            ax.scatter(*cur, marker="^", s=200, color="darkorange",
                       edgecolors="k", linewidths=0.6, label="SUPPRESSOR")
            drops_done = sum(1 for d in s["supp_drops"] if d <= k)
            remaining = 2 - drops_done
            if drops_done:
                ax.scatter(*fire, marker="o", s=120, facecolors="none",
                           edgecolors="yellow", linewidths=2.0)
            if remaining == 0:
                phase = "Suppression (payload empty -> GUIDE)"
            info = f"Approaching fire in 3D  |  extinguisher left: {remaining}"
        else:
            phase = "Escape guidance (multi-floor)"
            k = min(frame - n_supp, n_path - 1) if n_path else 0
            if n_path:
                ax.plot(path[:, 0], path[:, 1], path[:, 2], "--",
                        color="royalblue", lw=1.2, alpha=0.4)
                seg = path[:k + 1]
                ax.plot(seg[:, 0], seg[:, 1], seg[:, 2], "-",
                        color="royalblue", lw=2.6, alpha=0.95)
                cur = path[k]
                ax.scatter(*cur, marker="P", s=200, color="deepskyblue",
                           edgecolors="k", linewidths=0.6,
                           label="Survivor moving")
                floor = int(round(cur[2]))
                info = (f"Climbing floors via A*  |  waypoint {k + 1}/{n_path}"
                        f"  (floor z={floor})")
            else:
                info = "no path"

        ax.scatter(*sv, marker="P", s=90, color="deepskyblue", alpha=0.4)
        ax.set_title(f"Firefighting drones (3D)  |  {phase}\n{info}",
                     fontsize=11)
        ax.legend(loc="upper left", fontsize=8, framealpha=0.85)
        ax.view_init(elev=22, azim=-60 + frame * 1.5)  # 천천히 회전
        return ax,

    anim = FuncAnimation(fig, draw, frames=total, interval=1000 / fps)
    anim.save(out_path, writer=PillowWriter(fps=fps))
    plt.close(fig)

    print(f"[OK] {out_path} 생성 완료 ({total} frames)")
    print(f"     진압 궤적 {n_supp} 스텝, 투하 {len(s['supp_drops'])}회, "
          f"최종 역할 {s['final_role']}")
    floors = sorted({int(round(z)) for z in path[:, 2]}) if n_path else []
    print(f"     탈출 경로 웨이포인트 {n_path}개, 경유 층: {floors}")


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "firefighting_3d.gif"
    render_gif(out_path=out)
