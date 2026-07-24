"""가정집 화재 SOP-D 미션 3D 시각화 + 실시간 편대 담당 임무 패널.

  - 좌(대형): 3D 가정집(장애물: 벽/방/지붕/가구) + 드론(역할 아이콘)·요구조자·화점
  - 우상: 내레이션(단계 + 상황) + 적용 SOP
  - 우중: **실시간 편대 상태표** — 편대별 현재 담당 임무·배터리·상태
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
LM_STYLE = {"fire": ("#ef4444", "*", 260), "exit": ("#22c55e", "s", 120),
            "safe": ("#334155", "s", 110), "victim": ("#0891b2", "P", 130)}


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
    order = ids  # 표시 순서

    fig = plt.figure(figsize=(15.5, 8.8))
    gs = fig.add_gridspec(3, 2, width_ratios=[1.5, 1],
                          height_ratios=[1.1, 1.5, 0.13],
                          hspace=0.28, wspace=0.12)
    ax = fig.add_subplot(gs[0:2, 0], projection="3d")
    axn = fig.add_subplot(gs[0, 1])
    axu = fig.add_subplot(gs[1, 1])
    axb = fig.add_subplot(gs[2, :])

    def draw(frame):
        ax.clear(); axn.clear(); axu.clear(); axb.clear()
        st = status[frame]

        # ==================== 3D 현장 ====================
        house.draw3d(ax)
        ax.set_xlim(lo[0], hi[0]); ax.set_ylim(lo[1], hi[1]); ax.set_zlim(0, hi[2])
        ax.set_box_aspect((hi[0] - lo[0], hi[1] - lo[1], (hi[2]) * 2.2))
        ax.set_xlabel("X (m)"); ax.set_ylabel("Y (m)"); ax.set_zlabel("고도 (m)")

        # 랜드마크.
        for name, (text, pos, kind) in lm.items():
            c, mk, sz = LM_STYLE.get(kind, ("#6b7280", "o", 100))
            ax.scatter(pos[0], pos[1], pos[2], marker=mk, s=sz, color=c,
                       edgecolors="k", linewidths=0.5, zorder=5)

        # 요구조자.
        vic = extras["survivor"][frame - 1] if frame >= 1 else None
        if vic is not None:
            ax.scatter(vic[0], vic[1], vic[2], marker=VICTIM_ICON[0], s=170,
                       color=VICTIM_ICON[1], edgecolors="k", linewidths=0.5,
                       zorder=8)

        # 드론(역할 아이콘 + 지면 투영선).
        for i in ids:
            role = roles[i][frame]
            path, color, name, tag = role_icon(role)
            x, y, z = positions[i][frame]
            ax.plot([x, x], [y, y], [0, z], color="gray", lw=0.6, alpha=0.4,
                    ls=":")
            ax.scatter(x, y, z, marker=path, s=150, color=color,
                       edgecolors="k", linewidths=0.6, zorder=9)
            ax.text(x, y, z + 1.2, labels[i], fontsize=6.5, color=color,
                    ha="center", weight="bold")
        ax.view_init(elev=30, azim=-60 + frame * 0.7)
        ax.set_title(res["title"], fontsize=12, weight="bold")

        # ==================== 내레이션 ====================
        axn.axis("off"); axn.set_xlim(0, 1); axn.set_ylim(0, 1)
        pcolor = PHASE_COLOR.get(st["phase"], "#334155")
        axn.text(0, 1.0, f"STEP {frame}/{T-1}", fontsize=9, color="#64748b",
                 va="top", family="monospace")
        axn.text(0, 0.80, st["phase"].upper(), fontsize=16, color=pcolor,
                 va="top", weight="bold")
        axn.text(0, 0.52, st["headline"], fontsize=10.5, color="#0f172a",
                 va="top", wrap=True)
        axn.text(0, 0.12, res["subtitle"], fontsize=8, color="#475569",
                 va="top", style="italic")

        # ============ 실시간 편대 상태표 ============
        axu.axis("off"); axu.set_xlim(0, 1); axu.set_ylim(0, 1)
        axu.text(0, 1.0, "실시간 편대 담당 임무 (SOP-D)", fontsize=10.5,
                 color="#b91c1c", va="top", weight="bold")
        us = ustatus[frame]
        y0 = 0.90
        for i in order:
            role = roles[i][frame]
            path, color, name, tag = role_icon(role)
            info = us[i]
            # 아이콘 + 편대명.
            axu.scatter(0.03, y0, marker=path, s=130, color=color,
                        edgecolors="k", linewidths=0.5)
            axu.text(0.075, y0 + 0.006, f"{labels[i]}", fontsize=8.5,
                     color=color, va="center", weight="bold")
            # 담당 임무 + 근거 SOP.
            axu.text(0.075, y0 - 0.035, f"{info['task']}", fontsize=7.6,
                     color="#1f2937", va="center")
            axu.text(0.075, y0 - 0.066, f"SOP {info['code']}", fontsize=6.5,
                     color="#dc2626", va="center")
            # 배터리 바.
            bx, bw = 0.74, 0.22
            axu.add_patch(Rectangle((bx, y0 - 0.012), bw, 0.024, fill=False,
                                    ec="#94a3b8", lw=0.8, transform=axu.transAxes))
            axu.add_patch(Rectangle((bx, y0 - 0.012), bw * info["battery"] / 100,
                                    0.024, color=_batt_color(info["battery"]),
                                    transform=axu.transAxes))
            axu.text(bx + bw + 0.01, y0, f"{info['battery']:.0f}%", fontsize=7,
                     color=_batt_color(info["battery"]), va="center",
                     weight="bold")
            axu.text(bx, y0 - 0.052, f"[{info['state']}]", fontsize=6.3,
                     color="#64748b", va="center")
            y0 -= 0.135

        # ==================== 타임라인 ====================
        axb.set_xlim(0, T - 1); axb.set_ylim(0, 1); axb.set_yticks([])
        axb.set_xlabel("mission timeline (step)", fontsize=8)
        for phase, s0, s1 in spans:
            axb.axvspan(s0, s1, color=PHASE_COLOR.get(phase, "#ccc"), alpha=0.35)
            if s1 - s0 >= 2:
                axb.text((s0 + s1) / 2, 0.5, phase, ha="center", va="center",
                         fontsize=7.5, weight="bold",
                         color=PHASE_COLOR.get(phase, "#333"))
        axb.axvline(frame, color="black", lw=1.8)

        fig.suptitle(f"드론 군집 SOP-D · 가정집 화재 대응   "
                     f"[편성: {res['roster_note']}]", fontsize=12.5, weight="bold")
        return (ax,)

    anim = FuncAnimation(fig, draw, frames=T, interval=1000 / fps)
    anim.save(out_path, writer=PillowWriter(fps=fps))
    plt.close(fig)
    print(f"[OK] {out_path}  ({T} frames, min_dist "
          f"{res['min_dist_series'].min():.2f} m)")


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "house_mission.gif"
    render(run_house_mission(), out)
