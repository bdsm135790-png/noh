"""역할을 한눈에 보여주는 드론 아이콘(마커) 정의.

「소방청훈령 제119호」제7조제4항(역할이 구분되도록 착용)의 취지를 반영해,
각 드론의 임무가 형태만 봐도 드러나도록 matplotlib용 벡터 아이콘(Path)을 만든다.

  진압(SUPPRESSOR)   물방울   — 소화(물) 투하
  정찰(SCOUT)        눈       — 수색·관측
  안내(GUIDE)        화살표   — 방향 유도
  경계(OVERWATCH)    방패     — 편대 보호·감시
  안전(SAFETY)       경고삼각 — 위험요인 감시·전파
  구조(RIT)          십자     — 조난 대원 구조
  구급(MEDIC)        십자     — 응급 처치(색으로 구분)
  지휘(COMMANDER)    별       — 지휘·통제
  유해물(HAZMAT)     육각형   — 유해가스·위험물
"""

import numpy as np
from matplotlib.path import Path

from firefighting_doctrine import Role


def _poly(points, close=True):
    """정점 리스트로 채워진 다각형 Path를 만든다(원점 중심 대략 [-1,1])."""
    pts = list(points)
    if close:
        pts = pts + [pts[0]]
    codes = [Path.MOVETO] + [Path.LINETO] * (len(pts) - 2) + [Path.CLOSEPOLY]
    return Path(np.array(pts, dtype=float), codes)


def _circle(cx, cy, r, n=24):
    a = np.linspace(0, 2 * np.pi, n, endpoint=False)
    return [(cx + r * np.cos(t), cy + r * np.sin(t)) for t in a]


def _drop():
    """물방울 — 진압(소화탄/방수)."""
    pts = [(0.0, 1.0)]
    # 아래쪽 둥근 몸통.
    a = np.linspace(np.deg2rad(60), np.deg2rad(480), 22)
    pts += [(0.62 * np.cos(t), -0.25 + 0.62 * np.sin(t)) for t in a]
    return _poly(pts)


def _eye():
    """눈 — 정찰·관측(수색)."""
    top = [(-0.95, 0.0), (-0.5, 0.42), (0.0, 0.52), (0.5, 0.42), (0.95, 0.0)]
    bot = [(0.5, -0.42), (0.0, -0.52), (-0.5, -0.42)]
    return _poly(top + bot)


def _arrow():
    """오른쪽 화살표 — 안내·유도(방향 지시)."""
    return _poly([(-0.85, 0.30), (0.15, 0.30), (0.15, 0.62),
                  (0.9, 0.0), (0.15, -0.62), (0.15, -0.30), (-0.85, -0.30)])


def _shield():
    """방패 — 경계·보호."""
    return _poly([(0.0, 0.95), (0.72, 0.55), (0.72, -0.2),
                  (0.0, -0.95), (-0.72, -0.2), (-0.72, 0.55)])


def _warning():
    """경고 삼각형 — 안전(위험요인 감시)."""
    return _poly([(0.0, 0.9), (0.86, -0.62), (-0.86, -0.62)])


def _cross():
    """굵은 십자 — 구조/구급."""
    a, b = 0.32, 0.9
    return _poly([(-a, b), (a, b), (a, a), (b, a), (b, -a), (a, -a),
                  (a, -b), (-a, -b), (-a, -a), (-b, -a), (-b, a), (-a, a)])


def _star(n=5, r_out=1.0, r_in=0.42):
    """별 — 지휘."""
    pts = []
    for k in range(2 * n):
        ang = np.pi / 2 + k * np.pi / n
        r = r_out if k % 2 == 0 else r_in
        pts.append((r * np.cos(ang), r * np.sin(ang)))
    return _poly(pts)


def _hexagon():
    """육각형 — 유해가스·위험물."""
    return _poly(_circle(0, 0, 0.95, n=6))


def _person():
    """사람 — 요구조자(머리 원 + 사다리꼴 몸통, 두 서브패스)."""
    head = _circle(0.0, 0.58, 0.34, n=20)
    body = [(-0.40, 0.18), (0.40, 0.18), (0.26, -0.92), (-0.26, -0.92)]
    verts, codes = [], []
    for sub in (head, body):
        loop = sub + [sub[0]]
        codes += [Path.MOVETO] + [Path.LINETO] * (len(loop) - 2) + [Path.CLOSEPOLY]
        verts += loop
    return Path(np.array(verts, dtype=float), codes)


# 역할 -> (아이콘 Path, 색, 한글 이름, 짧은 태그)
ICONS = {
    Role.COMMANDER: (_star(), "#111827", "지휘 COMMANDER", "CMD"),
    Role.SAFETY: (_warning(), "#f59e0b", "안전 SAFETY", "SAF"),
    Role.SCOUT: (_eye(), "#7c3aed", "정찰 SCOUT", "SCT"),
    Role.SUPPRESSOR: (_drop(), "#2563eb", "진압 SUPPRESSOR", "SUP"),
    Role.GUIDE: (_arrow(), "#0ea5e9", "안내 GUIDE", "GDE"),
    Role.RIT: (_cross(), "#dc2626", "신속구조 RIT", "RIT"),
    Role.HAZMAT: (_hexagon(), "#16a34a", "유해물 HAZMAT", "HZM"),
    Role.OVERWATCH: (_shield(), "#0d9488", "경계 OVERWATCH", "OWatch"),
    Role.MEDIC: (_cross(), "#db2777", "구급 MEDIC", "MED"),
}

# 요구조자/조난자 등 비-드론 개체.
VICTIM_ICON = (_person(), "#0891b2")
DOWNED_ICON = (_cross(), "#b91c1c")


def role_icon(role):
    """역할의 (Path, 색, 이름, 태그). 미정의 역할은 회색 원으로 대체."""
    return ICONS.get(role, (_circle_path(), "#6b7280", role, role[:3]))


def _circle_path():
    return _poly(_circle(0, 0, 0.9, n=20))


def color_of(role):
    return role_icon(role)[1]
