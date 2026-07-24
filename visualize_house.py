"""가정집 화재 SOP-D 미션 3D 시각화 — 정돈된 화면 + 실시간 편대 담당.

  - 좌(대형): 3D 가정집(2층·박공지붕, 장애물) + 드론(역할 아이콘)·요구조자·화점
  - 우상: 단계 + 현재 상황(간결)
  - 우중: 실시간 편대 상태표 — 담당 임무 · 배터리
  - 하단: 진행 타임라인

실행:
    python3 visualize_house.py            # house_mission.gif
"""

import sys

import numpy as np
import matplotlib

matplotlib.use("Agg")
from matplotlib import font_manager as fm
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.animation import FuncAnimation, PillowWriter
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

from drone_icons import role_icon, VICTIM_ICON
import sop_doctrine as sop
from house_mission import run_house_mission

_FONT = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"
fm.fontManager.addfont(_FONT)
plt.rcParams["font.family"] = "WenQuanYi Zen Hei"
plt.rcParams["axes.unicode_minus"] = False

PHASE_COLOR = {
    "deploy": "#6366f1", "assess": "#0891b2", "operate": "#f97316",
    "relay": "#dc2626", "clear": "#22c55e",
}
LM_STYLE = {"fire": ("#ef4444", "*", 300), "exit": ("#22c55e", "s", 120),
            "safe": ("#475569", "s", 90), "victim": ("#0891b2", "P", 130)}


def _spans(phases):
    spans, s = [], 0
    for i in range(1, len(phases) + 1):
        if i == len(phases) or phases[i] != phases[s]:
            spans.append((phases[s], s, i - 1)); s = i
    return spans


def _batt_color(pct):
    if pct <= sop.BATTERY_EMERGENCY_PCT:
        return "#dc2626"
    if pct <= sop.BATTERY_RELAY_PCT:
        return "#f59e0b"
    return "#16a34a"


def _clean_3d(ax):
    """3D 축을 정돈: 그리드 제거, 패널 투명화."""
    ax.grid(False)
    for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
        axis.pane.set_facecolor((1, 1, 1, 0))
        axis.pane.set_edgecolor((1, 1, 1, 0))
        axis.line.set_color((0.7, 0.7, 0.7, 0.4))
    ax.set_xticks([]); ax.set_yticks([]); ax.set_zticks([])


def render(res, out_path="house_mission.gif", fps=6):
    positions = res["positions"]
    roles = res["roles"]
    labels = res["labels"]
    status = res["frame_status"]
    ustatus = res["unit_status"]
    lm = res["landmarks"]
    extras = res["extras"]
    house = res["house"]
    ids = list(positions.keys())
    T = len(next(iter(positions.values())))
    lo, hi = house.bounds()
    spans = _spans([s["phase"] for s in status])

    # 지면 평면(연한 회색).
    gx = [(lo[0], lo[1], 0), (hi[0], lo[1], 0), (hi[0], hi[1], 0), (lo[0], hi[1], 0)]

    fig = plt.figure(figsize=(15, 8.6))
    gs = fig.add_gridspec(3, 2, width_ratios=[1.55, 1],
                          height_ratios=[0.9, 1.7, 0.12],
                          hspace=0.22, wspace=0.06)
    ax = fig.add_subplot(gs[0:2, 0], projection="3d")
    axn = fig.add_subplot(gs[0, 1])
    axu = fig.add_subplot(gs[1, 1])
    axb = fig.add_subplot(gs[2, :])

    def draw(frame):
        ax.clear(); axn.clear(); axu.clear(); axb.clear()
        st = status[frame]

        # ==================== 3D 현장 ====================
        ax.add_collection3d(Poly3DCollection([gx], facecolor="#f1f5f9",
                                             edgecolor="none", alpha=0.5, zorder=0))
        house.draw3d(ax)
        ax.set_xlim(lo[0], hi[0]); ax.set_ylim(lo[1], hi[1]); ax.set_zlim(0, hi[2])
        ax.set_box_aspect((hi[0] - lo[0], hi[1] - lo[1], (hi[2]) * 1.6))
        _clean_3d(ax)

        for name, (text, pos, kind) in lm.items():
            c, mk, sz = LM_STYLE.get(kind, ("#6b7280", "o", 100))
            ax.scatter(pos[0], pos[1], pos[2], marker=mk, s=sz, color=c,
                       edgecolors="k", linewidths=0.5, zorder=5)

        vic = extras["survivor"][frame - 1] if frame >= 1 else None
        if vic is not None:
            ax.scatter(vic[0], vic[1], vic[2], marker=VICTIM_ICON[0], s=150,
                       color=VICTIM_ICON[1], edgecolors="k", linewidths=0.5,
                       zorder=8)

        for i in ids:
            role = roles[i][frame]
            path, color, name, tag = role_icon(role)
            x, y, z = positions[i][frame]
            ax.plot([x, x], [y, y], [0, z], color="#cbd5e1", lw=0.5, alpha=0.5,
                    ls=":")
            ax.scatter(x, y, z, marker=path, s=135, color=color,
                       edgecolors="k", linewidths=0.5, zorder=9)
            ax.text(x, y, z + 1.4, labels[i], fontsize=6.5, color=color,
                    ha="center", va="bottom", weight="bold")
        ax.view_init(elev=20, azim=-58 + frame * 0.5)
        ax.set_title(f"{res['title']}   (실제 규모: 약 {house.W:.0f}×{house.D:.0f} m, 2층)",
                     fontsize=11.5, weight="bold", pad=0)

        # ==================== 내레이션(간결) ====================
        axn.axis("off"); axn.set_xlim(0, 1); axn.set_ylim(0, 1)
        pcolor = PHASE_COLOR.get(st["phase"], "#334155")
        axn.text(0, 0.98, f"STEP {frame}/{T-1}", fontsize=9, color="#94a3b8",
                 va="top", family="monospace")
        axn.text(0, 0.72, st["phase"].upper(), fontsize=19, color=pcolor,
                 va="top", weight="bold")
        axn.text(0, 0.30, st["headline"], fontsize=11, color="#0f172a", va="top")

        # ============ 실시간 편대 상태표 ============
        axu.axis("off"); axu.set_xlim(0, 1); axu.set_ylim(0, 1)
        axu.text(0, 1.0, "실시간 편대 담당 임무", fontsize=11.5, color="#b91c1c",
                 va="top", weight="bold")
        us = ustatus[frame]
        rows = len(ids)
        y = 0.90
        dy = 0.90 / rows
        for i in ids:
            role = roles[i][frame]
            path, color, name, tag = role_icon(role)
            info = us[i]
            yc = y - dy / 2
            axu.scatter(0.035, yc + dy * 0.12, marker=path, s=150, color=color,
                        edgecolors="k", linewidths=0.5)
            # 라벨 + (활성 아닐 때만) 상태 배지.
            lbl = labels[i]
            axu.text(0.09, yc + dy * 0.16, lbl, fontsize=9, color=color,
                     va="center", weight="bold")
            if info["state"] != "active":
                axu.text(0.30, yc + dy * 0.16, info["state"].upper(), fontsize=6.5,
                         color="#64748b", va="center",
                         bbox=dict(boxstyle="round,pad=0.15", fc="#f1f5f9",
                                   ec="#cbd5e1", lw=0.4))
            axu.text(0.09, yc - dy * 0.12, f"{info['task']}  · SOP {info['code']}",
                     fontsize=7.4, color="#334155", va="center")
            # 배터리 바.
            bx, bw = 0.70, 0.24
            axu.add_patch(Rectangle((bx, yc + dy * 0.05), bw, dy * 0.22,
                                    fill=False, ec="#cbd5e1", lw=0.7,
                                    transform=axu.transAxes))
            axu.add_patch(Rectangle((bx, yc + dy * 0.05), bw * info["battery"] / 100,
                                    dy * 0.22, color=_batt_color(info["battery"]),
                                    transform=axu.transAxes))
            axu.text(bx + bw + 0.015, yc + dy * 0.16, f"{info['battery']:.0f}%",
                     fontsize=7.5, color=_batt_color(info["battery"]),
                     va="center", weight="bold")
            y -= dy

        # ==================== 타임라인 ====================
        axb.set_xlim(0, T - 1); axb.set_ylim(0, 1); axb.set_yticks([])
        axb.set_xlabel("mission timeline", fontsize=8)
        for phase, s0, s1 in spans:
            axb.axvspan(s0, s1, color=PHASE_COLOR.get(phase, "#ccc"), alpha=0.3)
            if s1 - s0 >= 3:
                axb.text((s0 + s1) / 2, 0.5, phase, ha="center", va="center",
                         fontsize=7.5, weight="bold",
                         color=PHASE_COLOR.get(phase, "#333"))
        axb.axvline(frame, color="black", lw=1.6)
        for sp in axb.spines.values():
            sp.set_visible(False)

        fig.suptitle("드론 군집 SOP-D · 가정집 화재 대응", fontsize=13,
                     weight="bold", y=0.98)
        return (ax,)

    anim = FuncAnimation(fig, draw, frames=T, interval=1000 / fps)
    anim.save(out_path, writer=PillowWriter(fps=fps))
    plt.close(fig)
    print(f"[OK] {out_path}  ({T} frames, min_dist "
          f"{res['min_dist_series'].min():.2f} m)")


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "house_mission.gif"
    render(run_house_mission(), out)
