"""스웜 + 소방 통합 임무 시각화 (이해 중심 레이아웃).

한 화면에서 임무를 쉽게 따라갈 수 있도록 3개 패널로 구성한다.
  - 좌(대형): 탑다운(XY) 지도 — 호위선/진압 사거리 링/이동 방향 화살표/라벨
  - 우상: 3D 원근 뷰 — 고도 감각
  - 우하: 실시간 내레이션 + 역할 설명(글로서리)
  - 하단: 임무 진행 타임라인(단계 색 구분 + 현재 위치 커서)

integrated_mission.run_mission() 의 궤적/상태를 그대로 사용한다.

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
from matplotlib.patches import Circle

from firefighting_drone import DroneRole
from integrated_mission import run_mission


# 역할별 (색, 마커, 이름, 짧은 태그, 하는 일).
ROLE_STYLE = {
    DroneRole.SCOUT: ("#7c3aed", "*", "SCOUT", "Sc", "find fire & survivor"),
    DroneRole.SUPPRESSOR: ("#f97316", "^", "SUPPRESSOR", "Su",
                           "attack fire, drop extinguisher"),
    DroneRole.GUIDE: ("#2563eb", "D", "GUIDE", "G",
                      "escort survivor along A* path"),
    "PATROL": ("#16a34a", "o", "PATROL", "P", "hold formation overhead"),
}

# 단계별 색(타임라인/배너).
PHASE_COLOR = {
    "launch": "#94a3b8", "approach": "#6366f1", "suppress": "#f97316",
    "escort": "#0ea5e9", "clear": "#22c55e",
}


def _phase_spans(phases):
    """연속된 같은 단계 구간을 [(phase, start, end), ...] 로 묶는다."""
    spans, s = [], 0
    for i in range(1, len(phases) + 1):
        if i == len(phases) or phases[i] != phases[s]:
            spans.append((phases[s], s, i - 1))
            s = i
    return spans


def _style(role):
    return ROLE_STYLE.get(role, ("gray", "o", role, "?", ""))


def render_gif(out_path="integrated_mission.gif", fps=7, trail=10):
    res = run_mission()
    positions = res["positions"]
    roles = res["roles"]
    labels = res["labels"]              # id -> 개체 라벨(Su1, P2, ...)
    survivor_track = res["survivor_track"]
    status = res["frame_status"]
    lm = res["landmarks"]
    approach = res["approach_steps"]
    ids = list(positions.keys())
    T = len(next(iter(positions.values())))

    planned = next((d.escape_path for d in res["fleet"]
                    if d.escape_path is not None), None)
    guide_id = next((i for i in ids if roles[i][0] == DroneRole.GUIDE), None)

    all_pts = np.vstack([positions[i] for i in ids]
                        + [lm["fire"][None, :], lm["exit"][None, :]])
    lo = all_pts.min(axis=0) - 3
    hi = all_pts.max(axis=0) + 3

    hazard = res["hazard"]
    fire_cells = np.argwhere(hazard > 0)
    spans = _phase_spans([s["phase"] for s in status])

    # 레이아웃: 좌 대형 탑다운 / 우상 3D / 우하 내레이션 / 하단 타임라인.
    fig = plt.figure(figsize=(15, 8.5))
    gs = fig.add_gridspec(3, 2, width_ratios=[1.4, 1],
                          height_ratios=[1, 1, 0.14],
                          hspace=0.32, wspace=0.16)
    ax2d = fig.add_subplot(gs[0:2, 0])
    ax3d = fig.add_subplot(gs[0, 1], projection="3d")
    axinfo = fig.add_subplot(gs[1, 1])
    axbar = fig.add_subplot(gs[2, :])

    gx, gy = np.meshgrid(np.linspace(lo[0], hi[0], 2),
                         np.linspace(lo[1], hi[1], 2))
    gz = np.zeros_like(gx)

    def draw(frame):
        ax2d.clear(); ax3d.clear(); axinfo.clear(); axbar.clear()
        start = max(0, frame - trail)
        st = status[frame]

        # ==================== 좌: 탑다운 지도(주뷰) ====================
        ax2d.set_xlim(lo[0], hi[0]); ax2d.set_ylim(lo[1], hi[1])
        ax2d.set_aspect("equal"); ax2d.grid(True, alpha=0.15)
        ax2d.set_xlabel("X (m)"); ax2d.set_ylabel("Y (m)")

        if len(fire_cells):
            ax2d.scatter(fire_cells[:, 1], fire_cells[:, 0], color="red",
                         marker="s", s=32, alpha=0.22)
        # 진압 사거리 링(반경 3 m).
        ax2d.add_patch(Circle(lm["fire"][:2], 3.0, fill=False, ls="--",
                              ec="#ef4444", alpha=0.6, lw=1.2))
        if planned is not None and len(planned):
            ax2d.plot(planned[:, 0], planned[:, 1], "--", color="#0ea5e9",
                      lw=1.4, alpha=0.55, label="Escape path (A*)")
        ax2d.scatter(*lm["fire"][:2], marker="*", s=520, color="#ef4444",
                     edgecolors="k", linewidths=0.7, zorder=4)
        ax2d.annotate("FIRE", lm["fire"][:2], textcoords="offset points",
                      xytext=(8, 8), fontsize=9, color="#b91c1c", weight="bold")
        ax2d.scatter(*lm["exit"][:2], marker="s", s=180, color="#22c55e",
                     edgecolors="k", linewidths=0.7, zorder=4)
        ax2d.annotate("EXIT", lm["exit"][:2], textcoords="offset points",
                      xytext=(8, 8), fontsize=9, color="#15803d", weight="bold")

        # 이동 방향 화살표(최근 속도).
        qx, qy, qu, qv, qc = [], [], [], [], []
        for i in ids:
            role = roles[i][frame]
            color, marker, name, tag, _ = _style(role)
            seg = positions[i][start:frame + 1]
            ax2d.plot(seg[:, 0], seg[:, 1], color=color, alpha=0.3, lw=1.2)
            x, y, z = positions[i][frame]
            ax2d.scatter(x, y, color=color, marker=marker, s=170,
                         edgecolors="k", linewidths=0.7, zorder=5)
            # 개체 라벨 + 고도. 흰 배경 박스로 겹쳐도 읽히게 한다.
            ax2d.annotate(f"{labels[i]}·{z:.0f}m", (x, y),
                          textcoords="offset points", xytext=(8, -4),
                          fontsize=7.5, color=color, weight="bold", zorder=8,
                          bbox=dict(boxstyle="round,pad=0.12", fc="white",
                                    ec=color, lw=0.5, alpha=0.75))
            if frame > 0:
                dvec = (positions[i][frame] - positions[i][frame - 1])[:2]
                n = np.linalg.norm(dvec)
                if n > 1e-6:
                    qx.append(x); qy.append(y)
                    qu.append(dvec[0] / n); qv.append(dvec[1] / n); qc.append(color)
        if qx:
            ax2d.quiver(qx, qy, qu, qv, color=qc, angles="xy",
                        scale_units="xy", scale=0.32, width=0.005,
                        alpha=0.8, zorder=6)

        # 요구조자 + 호위선(GUIDE→요구조자).
        sv = survivor_track[frame]
        if sv is not None:
            ax2d.scatter(sv[0], sv[1], marker="P", s=230, color="#0ea5e9",
                         edgecolors="k", linewidths=0.7, zorder=7)
            ax2d.annotate("survivor", (sv[0], sv[1]),
                          textcoords="offset points", xytext=(8, 6),
                          fontsize=8, color="#0369a1", weight="bold")
            if guide_id is not None:
                gx0, gy0 = positions[guide_id][frame][:2]
                ax2d.plot([gx0, sv[0]], [gy0, sv[1]], "-", color="#0ea5e9",
                          lw=1.0, alpha=0.5, zorder=3)
        ax2d.legend(loc="upper left", fontsize=8, framealpha=0.9)
        ax2d.set_title("Top-down map (X-Y)  — main view", fontsize=11,
                       weight="bold")

        # ======================== 우상: 3D ========================
        ax3d.set_xlim(lo[0], hi[0]); ax3d.set_ylim(lo[1], hi[1])
        ax3d.set_zlim(0, hi[2])
        ax3d.set_xlabel("X"); ax3d.set_ylabel("Y"); ax3d.set_zlabel("alt (m)")
        ax3d.plot_surface(gx, gy, gz, alpha=0.05, color="slategray", zorder=0)
        ax3d.scatter(*lm["fire"], marker="*", s=260, color="#ef4444",
                     edgecolors="k", linewidths=0.5)
        ax3d.scatter(*lm["exit"], marker="s", s=90, color="#22c55e",
                     edgecolors="k", linewidths=0.5)
        for i in ids:
            role = roles[i][frame]
            color, marker, *_ = _style(role)
            x, y, z = positions[i][frame]
            ax3d.plot([x, x], [y, y], [0, z], color="gray", lw=0.6,
                      alpha=0.4, ls=":")
            ax3d.scatter(x, y, 0, color=color, marker=marker, s=18, alpha=0.25)
            ax3d.scatter(x, y, z, color=color, marker=marker, s=90,
                         edgecolors="k", linewidths=0.5, zorder=5)
        if sv is not None:
            ax3d.scatter(sv[0], sv[1], 0, marker="P", s=120, color="#0ea5e9",
                         edgecolors="k", linewidths=0.5)
        ax3d.view_init(elev=28, azim=-70 + frame * 0.7)
        ax3d.set_title("3D perspective (altitude)", fontsize=10)

        # ==================== 우하: 내레이션 + 글로서리 ====================
        axinfo.axis("off")
        axinfo.set_xlim(0, 1); axinfo.set_ylim(0, 1)  # 0~1 고정 좌표
        pcolor = PHASE_COLOR.get(st["phase"], "#334155")
        axinfo.text(0.0, 1.0, f"STEP {frame}/{T - 1}",
                    fontsize=10, color="#475569", va="top", family="monospace")
        axinfo.text(0.0, 0.88, st["phase"].upper(), fontsize=15, color=pcolor,
                    va="top", weight="bold")
        # 헤드라인(길면 줄바꿈).
        head = st["headline"]
        axinfo.text(0.0, 0.72, head, fontsize=10.5, color="#111827", va="top",
                    wrap=True)
        # 역할 글로서리(현재 인원수 포함).
        counts = {}
        for i in ids:
            counts[roles[i][frame]] = counts.get(roles[i][frame], 0) + 1
        axinfo.text(0.0, 0.50, "Roles", fontsize=9.5, color="#475569",
                    va="top", weight="bold")
        y0 = 0.40
        order = [DroneRole.SCOUT, DroneRole.SUPPRESSOR, DroneRole.GUIDE, "PATROL"]
        for role in order:
            color, marker, name, tag, job = _style(role)
            n = counts.get(role, 0)
            axinfo.scatter(0.03, y0 + 0.012, marker=marker, s=90, color=color,
                           edgecolors="k", linewidths=0.5, zorder=5)
            axinfo.text(0.08, y0, f"{name} x{n}", fontsize=9, color=color,
                        va="center", weight="bold")
            axinfo.text(0.40, y0, f"- {job}", fontsize=8.5, color="#374151",
                        va="center")
            y0 -= 0.115

        # ==================== 하단: 진행 타임라인 ====================
        axbar.set_xlim(0, T - 1); axbar.set_ylim(0, 1)
        axbar.set_yticks([]); axbar.set_xlabel("mission timeline (step)",
                                                fontsize=8)
        for phase, s0, s1 in spans:
            axbar.axvspan(s0, s1, color=PHASE_COLOR.get(phase, "#ccc"),
                          alpha=0.35)
            mid = (s0 + s1) / 2
            if s1 - s0 >= 3:
                axbar.text(mid, 0.5, phase, ha="center", va="center",
                           fontsize=8, weight="bold",
                           color=PHASE_COLOR.get(phase, "#333"))
        axbar.axvline(frame, color="black", lw=1.8)

        fig.suptitle("Integrated Mission — Swarm formation + Firefighting roles",
                     fontsize=14, weight="bold")
        return ax2d, ax3d, axinfo, axbar

    anim = FuncAnimation(fig, draw, frames=T, interval=1000 / fps)
    anim.save(out_path, writer=PillowWriter(fps=fps))
    plt.close(fig)

    print(f"[OK] {out_path} 생성 완료 ({T} frames)")
    print(f"     편대 {len(ids)}기, 전 구간 최소 간격 "
          f"{res['min_dist_series'].min():.2f} m")
    print(f"     단계: {[p for p, _, _ in spans]}")


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "integrated_mission.gif"
    render_gif(out_path=out)
