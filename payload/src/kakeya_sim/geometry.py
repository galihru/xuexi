from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable

import numpy as np

Array = np.ndarray


def normalize(v: Array) -> Array:
    v = np.asarray(v, dtype=float)
    n = float(np.linalg.norm(v))
    if n <= 1e-15:
        raise ValueError("无法归一化接近零的向量。")
    return v / n


def orthonormal_frame(direction: Array, roll: float = 0.0) -> tuple[Array, Array, Array]:
    """返回正交归一标架 (u, v, w)，其中 w 为给定方向。"""
    w = normalize(direction)
    helper = np.array([1.0, 0.0, 0.0]) if abs(w[0]) < 0.8 else np.array([0.0, 1.0, 0.0])
    u = normalize(np.cross(w, helper))
    v = normalize(np.cross(w, u))
    if roll:
        c, s = math.cos(roll), math.sin(roll)
        u, v = c * u + s * v, -s * u + c * v
    return u, v, w


def point_segment_distance_squared(points: Array, a: Array, b: Array) -> tuple[Array, Array]:
    """计算 N 个点到线段 [a,b] 的距离平方，并返回截断到 [0,1] 的线段参数 t。"""
    points = np.asarray(points, dtype=float)
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    ab = b - a
    denom = float(np.dot(ab, ab))
    if denom <= 1e-15:
        delta = points - a
        return np.einsum("ij,ij->i", delta, delta), np.zeros(points.shape[0])
    t = np.clip(((points - a) @ ab) / denom, 0.0, 1.0)
    nearest = a + t[:, None] * ab
    delta = points - nearest
    return np.einsum("ij,ij->i", delta, delta), t


@dataclass(frozen=True)
class Tube:
    """单位线段的 δ 邻域，使用三维胶囊体表示。"""

    center: Array
    direction: Array
    radius: float
    shade_start: float = 0.0
    shade_end: float = 1.0
    group: int = -1

    def __post_init__(self) -> None:
        object.__setattr__(self, "center", np.asarray(self.center, dtype=float))
        object.__setattr__(self, "direction", normalize(self.direction))
        if self.radius <= 0:
            raise ValueError("管半径必须为正数。")
        if not (0.0 <= self.shade_start <= self.shade_end <= 1.0):
            raise ValueError("着色区间必须位于 [0,1]。")

    @property
    def a(self) -> Array:
        return self.center - 0.5 * self.direction

    @property
    def b(self) -> Array:
        return self.center + 0.5 * self.direction

    @property
    def paper_volume(self) -> float:
        """论文对单位管采用 |T|≈δ² 的尺度记号。"""
        return self.radius**2

    @property
    def capsule_volume(self) -> float:
        """单位线段半径为 δ 的胶囊体精确体积。"""
        r = self.radius
        return math.pi * r * r + (4.0 / 3.0) * math.pi * r**3

    @property
    def shading_fraction(self) -> float:
        return self.shade_end - self.shade_start

    def contains(self, points: Array, shaded: bool = False, radius_scale: float = 1.0) -> Array:
        d2, t = point_segment_distance_squared(points, self.a, self.b)
        mask = d2 <= (self.radius * radius_scale) ** 2
        if shaded:
            mask &= (t >= self.shade_start) & (t <= self.shade_end)
        return mask


@dataclass(frozen=True)
class OrientedBox:
    center: Array
    axes: Array  # shape (3,3), rows are unit axes
    lengths: Array  # full side lengths

    def __post_init__(self) -> None:
        object.__setattr__(self, "center", np.asarray(self.center, dtype=float))
        object.__setattr__(self, "axes", np.asarray(self.axes, dtype=float))
        object.__setattr__(self, "lengths", np.asarray(self.lengths, dtype=float))

    @property
    def volume(self) -> float:
        return float(np.prod(self.lengths))

    def contains_tube(self, tube: Tube) -> bool:
        rel_a = tube.a - self.center
        rel_b = tube.b - self.center
        pa = self.axes @ rel_a
        pb = self.axes @ rel_b
        allowance = self.lengths / 2.0 - tube.radius
        return bool(np.all(allowance >= 0.0) and np.all(np.abs(pa) <= allowance) and np.all(np.abs(pb) <= allowance))


@dataclass(frozen=True)
class Slab:
    normal: Array
    offset: float
    half_thickness: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "normal", normalize(self.normal))
        if self.half_thickness <= 0:
            raise ValueError("板厚度必须为正数。")

    def contains_tube(self, tube: Tube) -> bool:
        da = abs(float(np.dot(self.normal, tube.a)) - self.offset)
        db = abs(float(np.dot(self.normal, tube.b)) - self.offset)
        return max(da, db) + tube.radius <= self.half_thickness

    @property
    def unit_ball_volume(self) -> float:
        """单位球 B(0,1) 与偏移板相交部分的精确体积。"""
        lo = max(-1.0, self.offset - self.half_thickness)
        hi = min(1.0, self.offset + self.half_thickness)
        if hi <= lo:
            return 0.0
        primitive = lambda z: math.pi * (z - z**3 / 3.0)
        return primitive(hi) - primitive(lo)


def angular_distance(u: Array, v: Array) -> float:
    dot = float(np.clip(np.dot(normalize(u), normalize(v)), -1.0, 1.0))
    return math.acos(abs(dot))


def random_point_in_ball(rng: np.random.Generator, radius: float) -> Array:
    direction = normalize(rng.normal(size=3))
    return direction * radius * float(rng.random()) ** (1.0 / 3.0)


def polyline_length(points: Iterable[Array]) -> float:
    pts = [np.asarray(p, dtype=float) for p in points]
    return sum(float(np.linalg.norm(b - a)) for a, b in zip(pts, pts[1:]))
