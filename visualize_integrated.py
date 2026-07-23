"""스웜 + 소방 통합 임무 3D/탑다운 시각화.

integrated_mission.run_mission() 의 궤적을 애니메이션(GIF)으로 렌더링한다.
구분이 잘 되도록 좌측 3D 원근 뷰와 우측 탑다운(XY) 평면도를 함께 보여주고,
각 드론에 지면 투영선·역할 태그·고도 라벨을 붙인다.

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


# 역할별 (색, 마커, 이름, 짧은 태그). 색·모양을 모두 달리해 구분을 강화한다.
ROLE_STYLE = {
    DroneRole.SCOUT: ("#7c3aed", "*", "SCOUT", "Sc"),          # 보라 별
    DroneRole.SUPPRESSOR: ("#f97316", "^", "SUPPRESSOR", "Su"),  # 주황 삼각
    DroneRole.GUIDE: ("#2563eb", "D", "GUIDE", "G"),           # 파랑 다이아
    "PATROL": ("#16a34a", "o", "PATROL", "P"),                # 초록 원
}


def render_gif(out_path="integrated_mission.gif", fps=7, trail=10):
    res = run_mission()
    positions = res["positions"]          # id -> (T+1, 3)
    roles = res["roles"]                  # id -> list[role]
    survivor_track = res["survivor_track"]
    lm = res["landmarks"]
    approach = res["approach_steps"]
    ids = list(positions.keys())
    T = len(next(iter(positions.values())))

    # GUIDE가 계획한 탈출 경로(호위선 표시용).
    planned = next((d.escape_path for d in res["fleet"]
                    if d.escape_path is not None), None)

    # 축 범위(모든 궤적 + 랜드마크 포함).
    all_pts = np.vstack([positions[i] for i in ids]
                        + [lm["fire"][None, :], lm["exit"][None, :]])
    lo = all_pts.min(axis=0) - 2
    hi = all_pts.max(axis=0) + 2

    hazard = res["hazard"]
    fire_cells = np.argwhere(hazard > 0)  # (row, col)

    # 좌: 3D 원근 / 우: 탑다운(XY) 평면도.
    fig = plt.figure(figsize=(14, 7))
    ax3d = fig.add_subplot(121, projection="3d")
    ax2d = fig.add_subplot(122)

    # 지면 평면(z=0) 메쉬(한 번만 계산).
    gx, gy = np.meshgrid(np.linspace(lo[0], hi[0], 2),
                         np.linspace(lo[1], hi[1], 2))
    gz = np.zeros_like(gx)

    def _style(role):
        return ROLE_STYLE.get(role, ("gray", "o", role, "?"))

    def draw(frame):
        ax3d.clear()
        ax2d.clear()
        start = max(0, frame - trail)

        phase = "APPROACH — Boids formation" if frame <= approach \
            else "ON-SCENE — suppress / escort / loiter"

        # ============================ 좌: 3D ============================
        ax3d.set_xlim(lo[0], hi[0])
        ax3d.set_ylim(lo[1], hi[1])
        ax3d.set_zlim(0, hi[2])
        ax3d.set_xlabel("X (m)")
        ax3d.set_ylabel("Y (m)")
        ax3d.set_zlabel("Z / altitude (m)")
        ax3d.plot_surface(gx, gy, gz, alpha=0.06, color="slategray", zorder=0)

        if len(fire_cells):
            ax3d.scatter(fire_cells[:, 1], fire_cells[:, 0],
                         np.zeros(len(fire_cells)), color="red", marker="s",
                         s=14, alpha=0.3)
        ax3d.scatter(*lm["fire"], marker="*", s=420, color="#ef4444",
                     edgecolors="k", linewidths=0.6, label="Fire")
        ax3d.scatter(*lm["exit"], marker="s", s=150, color="#22c55e",
                     edgecolors="k", linewidths=0.6, label="Exit")

        labeled = set()
        for i in ids:
            role = roles[i][frame]
            color, marker, name, _ = _style(role)
            seg = positions[i][start:frame + 1]
            ax3d.plot(seg[:, 0], seg[:, 1], seg[:, 2], color=color,
                      alpha=0.45, linewidth=1.6)
            x, y, z = positions[i][frame]
            # 지면 투영선(stem) + 그림자로 실제 XY 위치·고도를 읽게 한다.
            ax3d.plot([x, x], [y, y], [0, z], color="gray",
                      linewidth=0.6, alpha=0.4, linestyle=":")
            ax3d.scatter(x, y, 0, color=color, marker=marker, s=22, alpha=0.25)
            lbl = name if name not in labeled else None
            labeled.add(name)
            ax3d.scatter(x, y, z, color=color, marker=marker, s=130,
                         edgecolors="k", linewidths=0.6, label=lbl, zorder=5)

        sv = survivor_track[frame]
        if sv is not None:
            ax3d.scatter(sv[0], sv[1], 0.0, marker="P", s=200,
                         color="#0ea5e9", edgecolors="k", linewidths=0.6,
                         label="Survivor", zorder=6)
        ax3d.legend(loc="upper left", fontsize=8, framealpha=0.9, ncol=2)
        ax3d.view_init(elev=26, azim=-70 + frame * 0.8)
        ax3d.set_title("3D perspective (rotating)", fontsize=10)

        # ======================= 우: 탑다운(XY) =======================
        ax2d.set_xlim(lo[0], hi[0])
        ax2d.set_ylim(lo[1], hi[1])
        ax2d.set_aspect("equal")
        ax2d.set_xlabel("X (m)")
        ax2d.set_ylabel("Y (m)")
        ax2d.grid(True, alpha=0.15)

        if len(fire_cells):
            ax2d.scatter(fire_cells[:, 1], fire_cells[:, 0], color="red",
                         marker="s", s=30, alpha=0.25)
        if planned is not None and len(planned):
            ax2d.plot(planned[:, 0], planned[:, 1], "--", color="#0ea5e9",
                      lw=1.4, alpha=0.6, label="Escape path")
        ax2d.scatter(*lm["fire"][:2], marker="*", s=420, color="#ef4444",
                     edgecolors="k", linewidths=0.6)
        ax2d.annotate("FIRE", lm["fire"][:2], textcoords="offset points",
                      xytext=(6, 6), fontsize=8, color="#b91c1c", weight="bold")
        ax2d.scatter(*lm["exit"][:2], marker="s", s=150, color="#22c55e",
                     edgecolors="k", linewidths=0.6)
        ax2d.annotate("EXIT", lm["exit"][:2], textcoords="offset points",
                      xytext=(6, 6), fontsize=8, color="#15803d", weight="bold")

        for i in ids:
            role = roles[i][frame]
            color, marker, name, tag = _style(role)
            seg = positions[i][start:frame + 1]
            ax2d.plot(seg[:, 0], seg[:, 1], color=color, alpha=0.35, lw=1.2)
            x, y, z = positions[i][frame]
            ax2d.scatter(x, y, color=color, marker=marker, s=150,
                         edgecolors="k", linewidths=0.6, zorder=5)
            # 역할 태그 + 고도 라벨로 개별 식별을 쉽게 한다.
            ax2d.annotate(f"{tag}·{z:.0f}m", (x, y), textcoords="offset points",
                          xytext=(7, -3), fontsize=7, color=color, weight="bold")

        if sv is not None:
            ax2d.scatter(sv[0], sv[1], marker="P", s=200, color="#0ea5e9",
                         edgecolors="k", linewidths=0.6, zorder=6)
            ax2d.annotate("survivor", (sv[0], sv[1]),
                          textcoords="offset points", xytext=(7, 5),
                          fontsize=7, color="#0369a1", weight="bold")
        ax2d.legend(loc="upper left", fontsize=8, framealpha=0.9)
        ax2d.set_title("Top-down map (X-Y)", fontsize=10)

        # 현재 역할 분포 배너.
        counts = {}
        for i in ids:
            counts[roles[i][frame]] = counts.get(roles[i][frame], 0) + 1
        cnt_txt = "  ".join(f"{_style(r)[3]}={n}" for r, n in sorted(counts.items()))
        fig.suptitle(
            f"Integrated mission - Swarm + Firefighting   |   "
            f"step {frame}/{T - 1}   |   {phase}   |   [{cnt_txt}]",
            fontsize=12, weight="bold",
        )
        return ax3d, ax2d

    anim = FuncAnimation(fig, draw, frames=T, interval=1000 / fps)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
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
