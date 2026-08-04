"""가정집(2층 단독주택) 3D 현장 — 실제 규모, 정돈된 표현.

실제 단독주택 크기(약 12 x 9 m, 2층, 층고 2.8 m, 박공지붕)를 3D로 모델링한다.
화면이 번잡하지 않도록 외벽/최소한의 내벽/2층 바닥/박공지붕만 얇고 연하게 그린다.

  - obstacle_boxes(): 충돌 회피용 벽/바닥 박스.
  - repel(pos): 벽 안/근처면 바깥으로 미는 벡터(장애물 회피).
  - draw3d(ax): 집을 깔끔하게 렌더링(박공지붕 포함).
"""

import numpy as np


class Box:
    def __init__(self, x0, x1, y0, y1, z0, z1, kind, name=""):
        self.x0, self.x1 = x0, x1
        self.y0, self.y1 = y0, y1
        self.z0, self.z1 = z0, z1
        self.kind = kind      # 'exterior' | 'interior' | 'floor'
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


# 정돈된 표현을 위한 연한 스타일(facecolor, edgecolor, alpha).
BOX_STYLE = {
    "exterior": ("#dbe4ee", "#94a3b8", 0.16),
    "interior": ("#e6ecf3", "#a9b6c6", 0.20),
    "floor": ("#cfd8e3", "#94a3b8", 0.14),
}


class HouseScene:
    """실제 규모 2층 단독주택."""

    def __init__(self):
        W, D = 12.0, 9.0          # 폭(x), 깊이(y) [m]
        story = 2.8               # 층고
        stories = 2
        t = 0.25                  # 벽 두께
        self.W, self.D = W, D
        self.story = story
        self.wall_h = story * stories          # 처마 높이 5.6 m
        self.ridge_h = self.wall_h + 2.4       # 지붕 용마루 8.0 m
        boxes = []

        # 외벽 4면(2층 전체 높이).
        H = self.wall_h
        boxes += [Box(0, W, 0, t, 0, H, "exterior", "front"),
                  Box(0, W, D - t, D, 0, H, "exterior", "back"),
                  Box(0, t, 0, D, 0, H, "exterior", "left"),
                  Box(W - t, W, 0, D, 0, H, "exterior", "right")]
        # 2층 바닥 슬래브(층 구분 느낌, 얇게).
        boxes += [Box(t, W - t, t, D - t, story, story + 0.15, "floor", "slab")]
        # 내벽: 층마다 방 구획 하나씩만(번잡 방지).
        boxes += [Box(W / 2, W / 2 + t, 0, D, 0, story, "interior", "1f-div"),
                  Box(W / 2, W / 2 + t, 0, D, story, H, "interior", "2f-div")]
        self.boxes = boxes

        # 주요 지점(2층에서 화재·요구조자 발생).
        z2 = story                     # 2층 바닥 높이
        self.fire = np.array([9.0, 4.5, z2 + 0.9])       # 2층 우측 방 화점
        self.survivor = np.array([3.0, 4.5, z2 + 0.2])   # 2층 좌측 방 요구조자
        self.door = np.array([W / 2, 0.0, 0.0])          # 현관(전면 중앙, 1층)
        self.exit = np.array([W / 2, -7.0, 0.0])         # 집 밖 대피 집결지
        self.pad = np.array([-8.5, -6.5, 0.0])           # GCS/드론 패드(Cold Zone)
        # 창문(외벽 진입점) — 2층, 집 밖 공중에서 접근.
        self.windows = {
            "kitchen": np.array([9.0, -1.0, z2 + 1.0]),   # 화재실 전면 창(진압)
            "bed1": np.array([-1.0, 4.5, z2 + 1.0]),      # 침실 좌측 창(구조)
        }
        self.transit_alt = self.ridge_h + 3.0            # 용마루 위 통과 고도

    # --------------------------------------------------------------
    def obstacle_boxes(self):
        return [b for b in self.boxes if b.kind != "floor"]

    def repel(self, pos, margin=0.6):
        """벽 내부(또는 근처)이고 그 높이 아래면 바깥으로 미는 벡터."""
        pos = np.asarray(pos, float)
        push = np.zeros(3)
        for b in self.obstacle_boxes():
            if pos[2] > b.z1 + 0.2:
                continue
            if not b.contains_xy(pos[0], pos[1], margin):
                continue
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
            push[2] += 0.4
        return push

    def roof_polys(self):
        """박공(gable) 지붕 면 목록(앞/뒤 경사면 + 좌/우 박공 삼각형)."""
        W, D, H, R = self.W, self.D, self.wall_h, self.ridge_h
        ym = D / 2
        front = [(0, 0, H), (W, 0, H), (W, ym, R), (0, ym, R)]
        back = [(0, D, H), (W, D, H), (W, ym, R), (0, ym, R)]
        gable_l = [(0, 0, H), (0, D, H), (0, ym, R)]
        gable_r = [(W, 0, H), (W, D, H), (W, ym, R)]
        return [front, back, gable_l, gable_r]

    def bounds(self):
        lo = np.array([self.pad[0] - 2, self.exit[1] - 2, 0.0])
        hi = np.array([self.W + 5, self.D + 5, self.transit_alt + 5])
        return lo, hi

    def draw3d(self, ax):
        from mpl_toolkits.mplot3d.art3d import Poly3DCollection
        # 벽/바닥.
        for b in self.boxes:
            fc, ec, alpha = BOX_STYLE[b.kind]
            ax.add_collection3d(Poly3DCollection(
                b.faces(), facecolor=fc, edgecolor=ec, linewidths=0.3,
                alpha=alpha))
        # 박공지붕(연한 벽돌색).
        ax.add_collection3d(Poly3DCollection(
            self.roof_polys(), facecolor="#e7c9a9", edgecolor="#b08968",
            linewidths=0.4, alpha=0.20))
        # 드론 패드(Cold Zone).
        ax.scatter(*self.pad, marker="s", s=90, color="#475569",
                   edgecolors="k", linewidths=0.4, zorder=3)
