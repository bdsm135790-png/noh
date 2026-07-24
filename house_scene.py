"""가정집(단독주택) 3D 현장 — 장애물 포함.

재난현장에는 벽·방·가구 등 장애물이 많다. 여기서는 방 5칸짜리 단독주택을
3D 박스로 모델링해, 드론이 벽을 피해(위로 넘거나 창문으로 접근) 비행하도록 한다.

  - 외벽/내벽/지붕/가구를 3D 박스로 표현(Poly3DCollection).
  - 화점(주방), 요구조자(침실1), 현관 출구, 창문(진입점), GCS 패드(Cold Zone).
  - obstacle_boxes(): 충돌 회피용 박스 목록.
  - repel(pos): 벽 안/근처에 있으면 밖으로 밀어내는 벡터(장애물 회피).
"""

import numpy as np


class Box:
    def __init__(self, x0, x1, y0, y1, z0, z1, kind, name=""):
        self.x0, self.x1 = x0, x1
        self.y0, self.y1 = y0, y1
        self.z0, self.z1 = z0, z1
        self.kind = kind      # 'exterior' | 'interior' | 'roof' | 'furniture'
        self.name = name

    def faces(self):
        v = [(self.x0, self.y0, self.z0), (self.x1, self.y0, self.z0),
             (self.x1, self.y1, self.z0), (self.x0, self.y1, self.z0),
             (self.x0, self.y0, self.z1), (self.x1, self.y0, self.z1),
             (self.x1, self.y1, self.z1), (self.x0, self.y1, self.z1)]
        idx = [[0, 1, 2, 3], [4, 5, 6, 7], [0, 1, 5, 4],
               [2, 3, 7, 6], [1, 2, 6, 5], [0, 3, 7, 4]]
        return [[v[i] for i in f] for f in idx]

    def contains_xy(self, x, y, margin=0.0):
        return (self.x0 - margin <= x <= self.x1 + margin and
                self.y0 - margin <= y <= self.y1 + margin)


# 박스 종류별 표시 스타일.
BOX_STYLE = {
    "exterior": ("#cbd5e1", "#475569", 0.22),
    "interior": ("#e2e8f0", "#64748b", 0.30),
    "roof": ("#b45309", "#7c2d12", 0.14),
    "furniture": ("#a8a29e", "#57534e", 0.45),
}


class HouseScene:
    """방 5칸짜리 단독주택. 좌표 단위 m."""

    def __init__(self):
        W, D, H = 16.0, 12.0, 3.0          # 폭, 깊이, 층고
        t = 0.4                            # 벽 두께
        self.W, self.D, self.H = W, D, H
        self.wall_h = H
        boxes = []

        # 외벽 4면(창문/현관은 별도 표시).
        boxes += [Box(0, W, 0, t, 0, H, "exterior", "front"),
                  Box(0, W, D - t, D, 0, H, "exterior", "back"),
                  Box(0, t, 0, D, 0, H, "exterior", "left"),
                  Box(W - t, W, 0, D, 0, H, "exterior", "right")]
        # 내벽(방 구획): 거실/주방/침실1/침실2/욕실.
        boxes += [Box(7, 7 + t, 0, 7, 0, H, "interior", "hall-v"),
                  Box(7, W, 6, 6 + t, 0, H, "interior", "kit-h"),
                  Box(0, 7, 7, 7 + t, 0, H, "interior", "bed-h"),
                  Box(3.5, 3.5 + t, 7, D, 0, H, "interior", "bed-split")]
        # 지붕(반투명, 내부가 보이도록 낮은 alpha) — 얇은 판.
        boxes += [Box(-0.5, W + 0.5, -0.5, D + 0.5, H, H + 0.4, "roof", "roof")]
        # 가구 몇 개(추가 장애물).
        boxes += [Box(9, 12, 1, 3, 0, 1.0, "furniture", "sofa"),
                  Box(2, 4, 2, 4, 0, 0.8, "furniture", "table"),
                  Box(1, 3, 8.5, 11, 0, 1.2, "furniture", "bed1")]
        self.boxes = boxes

        # 주요 지점.
        self.fire = np.array([12.0, 3.0, 1.0])       # 주방 화점
        self.survivor = np.array([2.0, 9.5, 0.0])    # 침실1 요구조자
        self.door = np.array([7.0, 0.0, 0.0])        # 현관(전면 중앙)
        self.exit = np.array([7.0, -4.0, 0.0])       # 집 밖 대피 집결지
        self.pad = np.array([-8.0, -6.0, 0.0])       # GCS/드론 패드(Cold Zone)
        # 창문(외벽 진입점): 화재실/침실 접근용(집 밖 공중에서 접근).
        self.windows = {
            "kitchen": np.array([12.0, -1.2, 1.6]),   # 주방 전면 창(진압 접근)
            "bed1": np.array([-1.2, 9.5, 1.6]),       # 침실1 좌측 창(구조 접근)
        }
        self.transit_alt = self.wall_h + 3.0          # 벽 위 통과 고도

    # --------------------------------------------------------------
    def obstacle_boxes(self):
        """충돌 회피 대상(지붕 제외: 상공 통과 가능)."""
        return [b for b in self.boxes if b.kind != "roof"]

    def repel(self, pos, margin=0.6):
        """벽/가구 박스 내부(또는 근처)이고 그 높이 아래면 바깥으로 미는 벡터."""
        pos = np.asarray(pos, float)
        push = np.zeros(3)
        for b in self.obstacle_boxes():
            if pos[2] > b.z1 + 0.2:      # 박스보다 높이 있으면 통과.
                continue
            if not b.contains_xy(pos[0], pos[1], margin):
                continue
            # 가장 가까운 면으로 밀어낸다(수평).
            dx0, dx1 = pos[0] - (b.x0 - margin), (b.x1 + margin) - pos[0]
            dy0, dy1 = pos[1] - (b.y0 - margin), (b.y1 + margin) - pos[1]
            m = min(dx0, dx1, dy0, dy1)
            if m == dx0:
                push[0] -= (margin - min(dx0, margin))
            elif m == dx1:
                push[0] += (margin - min(dx1, margin))
            elif m == dy0:
                push[1] -= (margin - min(dy0, margin))
            else:
                push[1] += (margin - min(dy1, margin))
            push[2] += 0.4    # 살짝 띄워 벽 위로 유도.
        return push

    def bounds(self):
        lo = np.array([self.pad[0] - 2, self.exit[1] - 2, 0.0])
        hi = np.array([self.W + 4, self.D + 4, self.transit_alt + 6])
        return lo, hi

    def draw3d(self, ax):
        """장애물 박스를 3D로 그린다."""
        from mpl_toolkits.mplot3d.art3d import Poly3DCollection
        for b in self.boxes:
            fc, ec, alpha = BOX_STYLE[b.kind]
            col = Poly3DCollection(b.faces(), facecolor=fc, edgecolor=ec,
                                   linewidths=0.4, alpha=alpha)
            ax.add_collection3d(col)
        # 드론 패드(Cold Zone) 바닥 표시.
        ax.scatter(*self.pad, marker="s", s=120, color="#334155",
                   edgecolors="k", zorder=3)
