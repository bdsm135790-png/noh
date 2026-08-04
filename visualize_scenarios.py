"""5대 시나리오 공통 3-패널 시각화(한글 지침 표시).

scenarios.py의 표준 결과 dict를 받아 하나의 렌더러로 GIF를 만든다.
  - 좌(대형): 탑다운 지도 — 역할 아이콘, 랜드마크, 요구조자/조난자/가스 플룸
  - 우상: 내레이션(단계 + 상황)
  - 우중: 현재 적용 중인 행동 지침(근거 조항 포함) — 「소방청훈령 제119호」
  - 우하: 역할 아이콘 범례(임무 설명)
  - 하단: 임무 진행 타임라인

실행:
    python3 visualize_scenarios.py            # 5개 GIF 모두 생성
    python3 visualize_scenarios.py rescue     # 특정 시나리오만
"""

import sys

import numpy as np
import matplotlib

matplotlib.use("Agg")
from matplotlib import font_manager as fm
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.patches import Circle

from drone_icons import role_icon, VICTIM_ICON, DOWNED_ICON
import firefighting_doctrine as doc
from scenarios import ALL_SCENARIOS

# 한글 표시용 폰트(WenQuanYi Zen Hei — Hangul 지원).
_FONT = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"
fm.fontManager.addfont(_FONT)
plt.rcParams["font.family"] = "WenQuanYi Zen Hei"
plt.rcParams["axes.unicode_minus"] = False

# 랜드마크 종류별 스타일.
LM_STYLE = {
    "fire": ("#ef4444", "*", 520),
    "exit": ("#22c55e", "s", 200),
    "safe": ("#2563eb", "H", 240),
    "victim": ("#0891b2", "P", 200),
}
PHASE_COLOR = {
    "search": "#6366f1", "found": "#f59e0b", "escort": "#0ea5e9",
    "clear": "#22c55e", "size-up": "#6366f1", "suppress": "#f97316",
    "overhaul": "#0d9488", "working": "#6366f1", "WARNING": "#f59e0b",
    "EVACUATE": "#dc2626", "accounted": "#22c55e", "MAYDAY": "#dc2626",
    "reach": "#f59e0b", "extract": "#0ea5e9", "detect": "#6366f1",
    "zone": "#f59e0b", "rescue": "#0ea5e9",
}


def _spans(phases):
    spans, s = [], 0
    for i in range(1, len(phases) + 1):
        if i == len(phases) or phases[i] != phases[s]:
            spans.append((phases[s], s, i - 1))
            s = i
    return spans


def _extra(extras, key, frame):
    """extras[key]는 step1부터 기록 → frame(0..T)에 맞춰 정렬(-1)."""
    seq = extras.get(key)
    if not seq or frame < 1 or frame - 1 >= len(seq):
        return None
    return seq[frame - 1]


def render_scenario(res, out_path, fps=7, trail=8):
    positions = res["positions"]
    roles = res["roles"]
    labels = res["labels"]
    status = res["frame_status"]
    lm = res["landmarks"]
    extras = res["extras"]
    ids = list(positions.keys())
    T = len(next(iter(positions.values())))

    lm_pts = [v[1] for v in lm.values()]
    all_pts = np.vstack([positions[i][:, :3] for i in ids] +
                        [np.array(lm_pts)])
    lo = all_pts.min(axis=0) - 4
    hi = all_pts.max(axis=0) + 4

    # 이 시나리오에 등장하는 역할(범례용).
    present = []
    for i in ids:
        r0 = roles[i][0]
        if r0 not in present:
            present.append(r0)

    spans = _spans([s["phase"] for s in status])
    hazard = res.get("hazard")
    fire_cells = np.argwhere(hazard > 0) if hazard is not None else []

    fig = plt.figure(figsize=(15.5, 8.6))
    gs = fig.add_gridspec(4, 2, width_ratios=[1.45, 1],
                          height_ratios=[1, 1, 1, 0.14],
                          hspace=0.35, wspace=0.16)
    axm = fig.add_subplot(gs[0:3, 0])   # 지도(대형)
    axn = fig.add_subplot(gs[0, 1])     # 내레이션
    axd = fig.add_subplot(gs[1, 1])     # 지침
    axl = fig.add_subplot(gs[2, 1])     # 역할 범례
    axb = fig.add_subplot(gs[3, :])     # 타임라인

    def draw(frame):
        for a in (axm, axn, axd, axl, axb):
            a.clear()
        st = status[frame]
        start = max(0, frame - trail)

        # ==================== 지도 ====================
        axm.set_xlim(lo[0], hi[0]); axm.set_ylim(lo[1], hi[1])
        axm.set_aspect("equal"); axm.grid(True, alpha=0.15)
        axm.set_xlabel("X (m)"); axm.set_ylabel("Y (m)")

        if len(fire_cells):
            axm.scatter(fire_cells[:, 1], fire_cells[:, 0], color="red",
                        marker="s", s=26, alpha=0.18)

        # 가스 플룸(있으면): 반투명 원 + 경계구역 점선.
        plume = _extra(extras, "plume", frame)
        if plume is not None:
            c, r = plume
            axm.add_patch(Circle(c[:2], r, color="#84cc16", alpha=0.22, zorder=1))
            axm.add_patch(Circle(c[:2], r + 3, fill=False, ls="--",
                                 ec="#65a30d", lw=1.3, alpha=0.7, zorder=1))

        # 랜드마크.
        for name, (text, pos, kind) in lm.items():
            color, mk, sz = LM_STYLE.get(kind, ("#6b7280", "o", 120))
            axm.scatter(pos[0], pos[1], marker=mk, s=sz, color=color,
                        edgecolors="k", linewidths=0.6, zorder=4)
            axm.annotate(text, (pos[0], pos[1]), textcoords="offset points",
                         xytext=(8, 7), fontsize=8, color=color, weight="bold")

        # 드론(역할 아이콘). 조난(DOWNED)은 아이콘 대신 '조난 대원'으로만 표시.
        for i in ids:
            role = roles[i][frame]
            if role == "DOWNED":
                continue
            path, color, name, tag = role_icon(role)
            seg = positions[i][start:frame + 1]
            axm.plot(seg[:, 0], seg[:, 1], color=color, alpha=0.3, lw=1.1)
            x, y = positions[i][frame][:2]
            axm.scatter(x, y, marker=path, s=260, color=color,
                        edgecolors="k", linewidths=0.6, zorder=6)
            axm.annotate(labels[i], (x, y), textcoords="offset points",
                         xytext=(7, -10), fontsize=7, color=color, weight="bold",
                         bbox=dict(boxstyle="round,pad=0.1", fc="white",
                                   ec=color, lw=0.4, alpha=0.7))

        # 요구조자 / 조난자.
        vic = _extra(extras, "victim", frame)
        if vic is not None:
            axm.scatter(vic[0], vic[1], marker=VICTIM_ICON[0], s=300,
                        color=VICTIM_ICON[1], edgecolors="k", linewidths=0.6,
                        zorder=7)
            axm.annotate("요구조자", (vic[0], vic[1]), textcoords="offset points",
                         xytext=(8, 6), fontsize=8, color=VICTIM_ICON[1],
                         weight="bold")
        downed = _extra(extras, "downed", frame)
        if downed is not None:
            axm.scatter(downed[0], downed[1], marker=DOWNED_ICON[0], s=300,
                        color=DOWNED_ICON[1], edgecolors="k", linewidths=0.7,
                        zorder=7)
            axm.annotate("조난 대원", (downed[0], downed[1]),
                         textcoords="offset points", xytext=(8, 6), fontsize=8,
                         color=DOWNED_ICON[1], weight="bold")
        axm.set_title(res["title"], fontsize=12, weight="bold")

        # ==================== 내레이션 ====================
        axn.axis("off"); axn.set_xlim(0, 1); axn.set_ylim(0, 1)
        pcolor = PHASE_COLOR.get(st["phase"], "#334155")
        axn.text(0, 1.0, f"STEP {frame}/{T-1}", fontsize=9, color="#64748b",
                 va="top", family="monospace")
        axn.text(0, 0.82, st["phase"].upper(), fontsize=16, color=pcolor,
                 va="top", weight="bold")
        axn.text(0, 0.55, st["headline"], fontsize=10, color="#0f172a",
                 va="top", wrap=True)
        axn.text(0, 0.12, res["subtitle"], fontsize=8, color="#475569",
                 va="top", style="italic")

        # ==================== 지침(도크트린) ====================
        axd.axis("off"); axd.set_xlim(0, 1); axd.set_ylim(0, 1)
        key = st["directive"]
        title_ko, article, desc = doc.GUIDELINES.get(
            key, (key, "", ""))
        axd.text(0, 1.0, "▣ 적용 지침 (소방청훈령 제119호)", fontsize=9.5,
                 color="#b91c1c", va="top", weight="bold")
        axd.text(0, 0.72, f"{title_ko}", fontsize=13, color="#111827",
                 va="top", weight="bold")
        axd.text(0, 0.50, f"근거: {article}", fontsize=9, color="#dc2626",
                 va="top")
        axd.text(0, 0.30, desc, fontsize=8.5, color="#374151", va="top",
                 wrap=True)

        # ==================== 역할 범례 ====================
        axl.axis("off"); axl.set_xlim(0, 1); axl.set_ylim(0, 1)
        axl.text(0, 1.0, "역할 (아이콘)", fontsize=9.5, color="#475569",
                 va="top", weight="bold")
        y0 = 0.86
        for role in present:
            path, color, name, tag = role_icon(role)
            job, art = doc.directive_for(role)
            axl.scatter(0.03, y0, marker=path, s=140, color=color,
                        edgecolors="k", linewidths=0.5)
            axl.text(0.09, y0, name, fontsize=8.5, color=color, va="center",
                     weight="bold")
            axl.text(0.09, y0 - 0.05, job, fontsize=7, color="#374151",
                     va="center")
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

        fig.suptitle(f"드론 소방 대응 시나리오  ·  {res['title']}   "
                     f"[편성: {res['roster_note']}]",
                     fontsize=13, weight="bold")
        return (axm,)

    anim = FuncAnimation(fig, draw, frames=T, interval=1000 / fps)
    anim.save(out_path, writer=PillowWriter(fps=fps))
    plt.close(fig)
    print(f"[OK] {out_path}  ({T} frames, min_dist "
          f"{res['min_dist_series'].min():.2f} m)")


def main(argv):
    names = argv or list(ALL_SCENARIOS.keys())
    for name in names:
        if name not in ALL_SCENARIOS:
            print(f"unknown scenario: {name}"); continue
        res = ALL_SCENARIOS[name]()
        render_scenario(res, f"scenario_{name}.gif")


if __name__ == "__main__":
    main(sys.argv[1:])
