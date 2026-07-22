"""핀홀 카메라 모델: 열화상/RGB 픽셀 좌표를 월드 좌표로 변환.

드론에 장착된 하향(nadir) 카메라를 가정하고, 픽셀에서 나온 광선(ray)을
지면(또는 목표 높이 평면)과 교차시켜 월드 좌표를 복원한다.

좌표계
------
- 월드: x=동(East), y=북(North), z=상(Up).
- 카메라(CV 관례): x=오른쪽, y=아래, z=전방(광축).
- 드론 요(yaw)는 월드 z축 기준 회전. 카메라는 정하방(-z)을 향한다.
"""

import numpy as np


class CameraModel:
    """핀홀 카메라 내부 파라미터.

    Parameters
    ----------
    fx, fy : float
        초점 거리(픽셀 단위).
    cx, cy : float
        주점(principal point). 보통 이미지 중심.
    """

    def __init__(self, fx, fy, cx, cy):
        self.fx = float(fx)
        self.fy = float(fy)
        self.cx = float(cx)
        self.cy = float(cy)

    @classmethod
    def from_fov(cls, image_shape, hfov_deg):
        """이미지 크기와 수평 화각(HFOV)으로 카메라를 만든다.

        Parameters
        ----------
        image_shape : tuple
            (H, W) 픽셀.
        hfov_deg : float
            수평 화각(도).
        """
        h, w = image_shape[:2]
        fx = (w / 2.0) / np.tan(np.radians(hfov_deg) / 2.0)
        fy = fx  # 정사각 픽셀 가정
        return cls(fx=fx, fy=fy, cx=w / 2.0, cy=h / 2.0)

    @staticmethod
    def _downward_rotation(yaw_rad):
        """요(yaw)만큼 회전한 하향 카메라의 회전행렬 R_world_cam.

        열: [x_cam, y_cam, z_cam] (모두 월드 좌표계 기준 단위벡터).
        z_cam = 월드 -z(정하방)이므로 광선은 항상 아래를 향한다.
        """
        c, s = np.cos(yaw_rad), np.sin(yaw_rad)
        return np.array([
            [c,  s,  0.0],
            [s, -c,  0.0],
            [0.0, 0.0, -1.0],
        ])

    def pixel_to_ground(self, pixel_uv, drone_pos, yaw_rad=0.0, target_z=0.0):
        """픽셀 (u, v)를 목표 높이 평면(z=target_z)의 월드 좌표로 변환한다.

        Parameters
        ----------
        pixel_uv : array-like, shape (2,)
            이미지 좌표 (u=col, v=row).
        drone_pos : array-like, shape (3,)
            카메라(=드론) 월드 위치. z는 target_z보다 높아야 한다.
        yaw_rad : float
            드론 요(rad).
        target_z : float
            교차시킬 평면의 높이(요구조자/지면 높이).

        Returns
        -------
        np.ndarray, shape (3,) or None
            월드 좌표. 광선이 평면과 만나지 않으면(드론이 평면 아래 등) None.
        """
        u, v = float(pixel_uv[0]), float(pixel_uv[1])
        pos = np.asarray(drone_pos, dtype=float)

        # 카메라 프레임에서의 정규화 광선 방향.
        d_cam = np.array([(u - self.cx) / self.fx,
                          (v - self.cy) / self.fy,
                          1.0])
        d_world = self._downward_rotation(yaw_rad) @ d_cam

        if abs(d_world[2]) < 1e-12:
            return None  # 광선이 평면과 평행
        t = (target_z - pos[2]) / d_world[2]
        if t <= 0:
            return None  # 평면이 카메라 뒤쪽(드론이 평면 아래)
        return pos + t * d_world
