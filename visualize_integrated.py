"""스웜 + 소방 통합 임무 3D 시각화.

integrated_mission.run_mission() 의 궤적을 3D 애니메이션(GIF)으로 렌더링한다.
여러 드론이 편대로 접근한 뒤 역할별로 협력(진압/호위/선회)하는 모습을
한 장면에서 보여준다.

실행:
    python3 visualize_integrated.py            # integrated_mission.gif
    python3 visualize_integrated.py out.gif
"""

import sys

import numpy as np
import matplotlib

matplotlib.use("Agg")  # 헤드리스 렌더링
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter

from firefighting_drone import DroneRole
from integrated_mission import run_mission


# 역할별 색/마커.
ROLE_STYLE = {
    DroneRole.SCOUT: ("mediumpurple", "o", "SCOUT"),
    DroneRole.SUPPRESSOR: ("darkorange", "^", "SUPPRESSOR"),
    DroneRole.GUIDE: ("royalblue", "D", "GUIDE"),
    "PATROL": ("seagreen", "o", "PATROL"),
}


def render_gif(out_path="integrated_mission.gif", fps=7, trail=12):
    res = run_mission()
    positions = res["positions"]          # id -> (T+1, 3)
    roles = res["roles"]                  # id -> list[role]
    survivor_track = res["survivor_track"]
    lm = res["landmarks"]
    approach = res["approach_steps"]
    ids = list(positions.keys())
    T = len(next(iter(positions.values())))

    # 축 범위(모든 궤적 + 랜드마크 포함).
    all_pts = np.vstack([positions[i] for i in ids]
                        + [lm["fire"][None, :], lm["exit"][None, :]])
    lo = all_pts.min(axis=0) - 2
    hi = all_pts.max(axis=0) + 2

    fig = plt.figure(figsize=(8.5, 8.5))
    ax = fig.add_subplot(111, projection="3d")

    # 지상 화염 벽 셀(연한 빨강)로 위험 지역 표시.
    hazard = res["hazard"]
    fire_cells = np.argwhere(hazard > 0)  # (row, col)

    def draw(frame):
        ax.clear()
        ax.set_xlim(lo[0], hi[0])
        ax.set_ylim(lo[1], hi[1])
        ax.set_zlim(0, hi[2])
        ax.set_xlabel("X (m)")
        ax.set_ylabel("Y (m)")
        ax.set_zlabel("Z (m)")

        # 위험 지역(지상).
        if len(fire_cells):
            ax.scatter(fire_cells[:, 1], fire_cells[:, 0],
                       np.zeros(len(fire_cells)), color="red", marker="s",
                       s=12, alpha=0.25)

        # 랜드마크.
        ax.scatter(*lm["fire"], marker="*", s=340, color="orangered",
                   edgecolors="k", linewidths=0.5, label="Fire")
        ax.scatter(*lm["exit"], marker="s", s=130, color="limegreen",
                   edgecolors="k", linewidths=0.5, label="Exit")

        # 드론(역할별 색). 범례 중복을 막기 위해 역할당 한 번만 라벨.
        labeled = set()
        start = max(0, frame - trail)
        for i in ids:
            role = roles[i][frame]
            color, marker, name = ROLE_STYLE.get(role, ("gray", "o", role))
            seg = positions[i][start:frame + 1]
            ax.plot(seg[:, 0], seg[:, 1], seg[:, 2], color=color,
                    alpha=0.3, linewidth=1)
            cur = positions[i][frame]
            lbl = name if name not in labeled else None
            labeled.add(name)
            ax.scatter(*cur, color=color, marker=marker, s=70,
                       edgecolors="k", linewidths=0.4, label=lbl)

        # 요구조자(지상, GUIDE 호위 중일 때만 표시).
        sv = survivor_track[frame]
        if sv is not None:
            ax.scatter(sv[0], sv[1], 0.0, marker="P", s=160,
                       color="deepskyblue", edgecolors="k", linewidths=0.5,
                       label="Survivor")

        phase = "Approach (Boids formation)" if frame <= approach \
            else "On-scene (suppress / escort / loiter)"
        ax.set_title(
            f"Integrated mission: Swarm + Firefighting (3D)\n"
            f"step {frame}/{T - 1}  |  {phase}",
            fontsize=11,
        )
        ax.legend(loc="upper left", fontsize=8, framealpha=0.85, ncol=2)
        ax.view_init(elev=24, azim=-70 + frame * 0.9)  # 천천히 회전
        return ax,

    anim = FuncAnimation(fig, draw, frames=T, interval=1000 / fps)
    anim.save(out_path, writer=PillowWriter(fps=fps))
    plt.close(fig)

    print(f"[OK] {out_path} 생성 완료 ({T} frames)")
    print(f"     편대 {len(ids)}기, 전 구간 최소 간격 "
          f"{res['min_dist_series'].min():.2f} m")
    final = {}
    for i in ids:
        final[roles[i][-1]] = final.get(roles[i][-1], 0) + 1
    print(f"     최종 역할: {final}")


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "integrated_mission.gif"
    render_gif(out_path=out)
