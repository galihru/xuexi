from __future__ import annotations

from dataclasses import replace
import math

import numpy as np

from .geometry import Tube, angular_distance, normalize, orthonormal_frame, random_point_in_ball


def separated_directions(
    rng: np.random.Generator,
    count: int,
    minimum_angle: float,
    max_attempts: int = 200_000,
) -> list[np.ndarray]:
    """贪心构造近似 δ-分离的无向方向。"""
    directions: list[np.ndarray] = []
    attempts = 0
    while len(directions) < count and attempts < max_attempts:
        candidate = normalize(rng.normal(size=3))
        if candidate[2] < 0:
            candidate = -candidate
        if all(angular_distance(candidate, old) >= minimum_angle for old in directions):
            directions.append(candidate)
        attempts += 1
    if len(directions) < count:
        raise RuntimeError(
            f"Could only generate {len(directions)} separated directions; "
            f"requested {count}. Reduce tube count or delta."
        )
    return directions


def cone_direction(
    rng: np.random.Generator,
    axis: np.ndarray,
    aperture: float,
) -> np.ndarray:
    u, v, w = orthonormal_frame(axis, roll=float(rng.uniform(0.0, 2.0 * math.pi)))
    theta = aperture * math.sqrt(float(rng.random()))
    phi = float(rng.uniform(0.0, 2.0 * math.pi))
    return normalize(math.cos(theta) * w + math.sin(theta) * (math.cos(phi) * u + math.sin(phi) * v))


def random_shading_interval(rng: np.random.Generator, lam: float) -> tuple[float, float]:
    lam = float(np.clip(lam, 0.01, 1.0))
    start = float(rng.uniform(0.0, 1.0 - lam)) if lam < 1.0 else 0.0
    return start, start + lam


def generate_uniform(
    rng: np.random.Generator,
    n: int,
    delta: float,
    lam: float,
) -> list[Tube]:
    dirs = separated_directions(rng, n, minimum_angle=0.8 * delta)
    tubes: list[Tube] = []
    for i, direction in enumerate(dirs):
        center = random_point_in_ball(rng, radius=0.42)
        s0, s1 = random_shading_interval(rng, lam)
        tubes.append(Tube(center, direction, delta, s0, s1, group=i))
    return tubes


def generate_sticky(
    rng: np.random.Generator,
    n: int,
    delta: float,
    rho: float,
    lam: float,
) -> list[Tube]:
    group_count = max(2, min(n, round(rho ** -2)))
    coarse_dirs = separated_directions(rng, group_count, minimum_angle=max(rho * 0.7, delta))
    tubes: list[Tube] = []
    for i in range(n):
        g = i % group_count
        coarse_dir = coarse_dirs[g]
        direction = cone_direction(rng, coarse_dir, aperture=max(delta, 0.45 * rho))
        u, v, _ = orthonormal_frame(coarse_dir, roll=float(rng.uniform(0.0, 2.0 * math.pi)))
        transverse = (float(rng.normal()) * u + float(rng.normal()) * v) * (0.22 * rho)
        longitudinal = coarse_dir * float(rng.uniform(-0.25, 0.25))
        center = transverse + longitudinal
        s0, s1 = random_shading_interval(rng, lam)
        tubes.append(Tube(center, direction, delta, s0, s1, group=g))
    return tubes


def generate_nonsticky(
    rng: np.random.Generator,
    n: int,
    delta: float,
    rho: float,
    lam: float,
) -> list[Tube]:
    """粗尺度管高度重叠，而每个粗管内部的细管保持稀疏。"""
    group_count = max(3, min(n, round(1.8 * rho ** -2)))
    coarse_dirs = separated_directions(rng, group_count, minimum_angle=max(0.45 * rho, delta * 0.8))
    common_focus = random_point_in_ball(rng, radius=0.08)
    tubes: list[Tube] = []
    for i in range(n):
        g = i % group_count
        coarse_dir = coarse_dirs[g]
        direction = cone_direction(rng, coarse_dir, aperture=max(delta, 0.18 * rho))
        u, v, _ = orthonormal_frame(coarse_dir, roll=float(rng.uniform(0.0, 2.0 * math.pi)))
        sparse_offset = (u * float(rng.uniform(-0.7, 0.7)) + v * float(rng.uniform(-0.7, 0.7))) * rho
        center = common_focus + sparse_offset + coarse_dir * float(rng.uniform(-0.2, 0.2))
        s0, s1 = random_shading_interval(rng, lam)
        tubes.append(Tube(center, direction, delta, s0, s1, group=g))
    return tubes


def generate_hairbrush(
    rng: np.random.Generator,
    n: int,
    delta: float,
    lam: float,
) -> list[Tube]:
    """围绕中心管构造类似 Wolff hairbrush 的排列。"""
    stem = normalize(np.array([0.0, 0.0, 1.0]))
    tubes = [Tube(np.zeros(3), stem, delta, 0.0, 1.0, group=0)]
    for i in range(1, n):
        theta = float(rng.uniform(max(2.0 * delta, 0.08), math.pi / 2.0))
        phi = float(rng.uniform(0.0, 2.0 * math.pi))
        direction = normalize(np.array([math.sin(theta) * math.cos(phi), math.sin(theta) * math.sin(phi), math.cos(theta)]))
        intersection = stem * float(rng.uniform(-0.45, 0.45))
        center = intersection + direction * float(rng.uniform(-0.2, 0.2))
        s0, s1 = random_shading_interval(rng, lam)
        tubes.append(Tube(center, direction, delta, s0, s1, group=i // max(2, n // 10)))
    return tubes


def generate_grains(
    rng: np.random.Generator,
    n: int,
    delta: float,
    rho: float,
    lam: float,
) -> list[Tube]:
    """Tubes organized into thin planar grains, inspired by Figures 2 and 3."""
    grain_count = max(2, min(8, round(rho ** -1)))
    tubes: list[Tube] = []
    for i in range(n):
        g = i % grain_count
        angle = 2.0 * math.pi * g / grain_count
        normal = normalize(np.array([math.cos(angle), math.sin(angle), 0.35]))
        u, v, _ = orthonormal_frame(normal)
        direction = normalize(u * math.cos(float(rng.uniform(-rho, rho))) + v * math.sin(float(rng.uniform(-rho, rho))))
        center = normal * float(rng.uniform(-0.25, 0.25)) + u * float(rng.uniform(-0.35, 0.35)) + v * float(rng.uniform(-0.35, 0.35))
        center += normal * float(rng.normal(scale=0.25 * delta))
        s0, s1 = random_shading_interval(rng, lam)
        tubes.append(Tube(center, direction, delta, s0, s1, group=g))
    return tubes


def generate_tubes(
    mode: str,
    seed: int,
    n: int,
    delta: float,
    rho: float,
    lam: float,
) -> list[Tube]:
    rng = np.random.default_rng(seed)
    factories = {
        "uniform": generate_uniform,
        "sticky": generate_sticky,
        "nonsticky": generate_nonsticky,
        "hairbrush": generate_hairbrush,
        "grains": generate_grains,
    }
    if mode == "mixed":
        modes = ["sticky", "nonsticky", "hairbrush", "grains"]
        pieces: list[Tube] = []
        counts = [n // len(modes)] * len(modes)
        for i in range(n % len(modes)):
            counts[i] += 1
        next_group = 0
        for local_mode, count in zip(modes, counts):
            if count == 0:
                continue
            local_seed = int(rng.integers(0, 2**63 - 1))
            local_rng = np.random.default_rng(local_seed)
            if local_mode in {"sticky", "nonsticky", "grains"}:
                chunk = factories[local_mode](local_rng, count, delta, rho, lam)
            else:
                chunk = factories[local_mode](local_rng, count, delta, lam)
            remapped = []
            for tube in chunk:
                remapped.append(replace(tube, group=tube.group + next_group))
            next_group = max(t.group for t in remapped) + 1
            pieces.extend(remapped)
        return pieces
    if mode not in factories:
        raise ValueError(f"Unknown mode: {mode}")
    if mode in {"sticky", "nonsticky", "grains"}:
        return factories[mode](rng, n, delta, rho, lam)
    return factories[mode](rng, n, delta, lam)
