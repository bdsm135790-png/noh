"""드론 군집(Swarm) 3D 시각화.

Gazebo 같은 물리 엔진 GUI 없이도, Boids 규칙으로 움직이는 드론 군집의
비행 궤적을 3D 애니메이션(GIF)으로 렌더링해 눈으로 확인할 수 있게 한다.

실행:
    python3 visualize_swarm.py            # swarm.gif 생성
    python3 visualize_swarm.py out.gif    # 파일명 지정
"""

import sys

import numpy as np
import matplotlib

matplotlib.use("Agg")  # 화면(디스플레이) 없이 파일로만 렌더링
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter

from swarm_drone import SwarmDrone
from simulate import build_swarm, swarm_spread, min_pairwise_distance


def simulate_trajectory(n=15, steps=200, dt=0.1, safe_dist=5.0, seed=0):
    """군집을 시뮬레이션하며 매 스텝의 위치 스냅샷을 기록한다.

    Returns
    -------
    positions : np.ndarray, shape (steps+1, n, 3)
    metrics   : list[tuple(spread, min_dist)]  스텝별 지표
    """
    drones = build_swarm(n=n, seed=seed)
    positions = [np.array([d.pos for d in drones])]
    metrics = [(swarm_spread(drones), min_pairwise_distance(drones))]

    for _ in range(steps):
        # 동시 업데이트를 위해 갱신 전 스냅샷을 이웃으로 사용한다.
        snapshot = [SwarmDrone(d.id, d.pos, d.vel) for d in drones]
        for d in drones:
            neighbors = [s for s in snapshot if s.id != d.id]
            d.update_swarm_behavior(neighbors, safe_dist=safe_dist, dt=dt)
        positions.append(np.array([d.pos for d in drones]))
        metrics.append((swarm_spread(drones), min_pairwise_distance(drones)))

    return np.array(positions), metrics


def render_gif(out_path="swarm.gif", n=15, steps=200, dt=0.1, safe_dist=5.0,
               seed=0, trail=15, fps=20):
    positions, metrics = simulate_trajectory(
        n=n, steps=steps, dt=dt, safe_dist=safe_dist, seed=seed
    )

    # 전체 궤적을 담을 수 있게 축 범위를 고정한다.
    lo = positions.reshape(-1, 3).min(axis=0) - 1
    hi = positions.reshape(-1, 3).max(axis=0) + 1

    fig = plt.figure(figsize=(7, 7))
    ax = fig.add_subplot(111, projection="3d")
    colors = plt.cm.turbo(np.linspace(0, 1, n))

    def draw(frame):
        ax.clear()
        ax.set_xlim(lo[0], hi[0])
        ax.set_ylim(lo[1], hi[1])
        ax.set_zlim(lo[2], hi[2])
        ax.set_xlabel("X (m)")
        ax.set_ylabel("Y (m)")
        ax.set_zlabel("Z (m)")

        # 꼬리(trail): 최근 몇 스텝의 궤적을 연하게 그린다.
        start = max(0, frame - trail)
        for i in range(n):
            seg = positions[start:frame + 1, i, :]
            ax.plot(seg[:, 0], seg[:, 1], seg[:, 2],
                    color=colors[i], alpha=0.35, linewidth=1)

        # 현재 위치를 드론 마커로 표시한다.
        cur = positions[frame]
        ax.scatter(cur[:, 0], cur[:, 1], cur[:, 2],
                   color=colors, s=40, depthshade=True, edgecolors="k",
                   linewidths=0.3)

        # 군집 무게중심.
        center = cur.mean(axis=0)
        ax.scatter(*center, color="red", marker="x", s=80)

        spread, mindist = metrics[frame]
        ax.set_title(
            f"Swarm Boids  |  step {frame:>3}/{steps}\n"
            f"spread={spread:5.2f} m   min_dist={mindist:5.2f} m",
            fontsize=11,
        )
        ax.view_init(elev=22, azim=frame * 0.8)  # 천천히 회전
        return ax,

    anim = FuncAnimation(fig, draw, frames=len(positions), interval=1000 / fps)
    writer = PillowWriter(fps=fps)
    anim.save(out_path, writer=writer)
    plt.close(fig)

    s0, _ = metrics[0]
    sN, dN = metrics[-1]
    print(f"[OK] {out_path} 생성 완료 ({len(positions)} frames)")
    print(f"     퍼짐: {s0:.2f} m -> {sN:.2f} m,  최종 최소간격: {dN:.2f} m")
    print(f"     충돌(간격<=0) 발생: {'없음' if min(m[1] for m in metrics) > 0 else '있음'}")


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "swarm.gif"
    render_gif(out_path=out)
