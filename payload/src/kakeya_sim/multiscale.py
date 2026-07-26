from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np

from .geometry import Tube, angular_distance
from .voxel import VoxelResult


@dataclass
class BroadnessRecord:
    radius: float
    maximum_fraction: float
    beta: float
    error_k: float


@dataclass
class MultiScaleMetrics:
    group_count: int
    group_sizes: list[int]
    inferred_nu: float
    mu: float
    mu_fine: float
    mu_coarse: float
    product_ratio: float
    grain_c: float
    grain_dimensions_rescaled: tuple[float, float, float]
    grain_dimensions_original: tuple[float, float, float]
    broadness: list[BroadnessRecord]
    local_density_tau: float
    local_density_fraction: float


def regroup_by_angular_scale(tubes: list[Tube], rho: float) -> list[int]:
    centers: list[np.ndarray] = []
    assignments: list[int] = []
    for tube in tubes:
        chosen = None
        for i, center in enumerate(centers):
            if angular_distance(tube.direction, center) <= rho:
                chosen = i
                break
        if chosen is None:
            centers.append(tube.direction.copy())
            chosen = len(centers) - 1
        assignments.append(chosen)
    return assignments


def estimate_broadness(
    tubes: list[Tube],
    voxel: VoxelResult,
    delta: float,
    rho: float,
    beta: float,
    sample_count: int,
    seed: int,
) -> list[BroadnessRecord]:
    rng = np.random.default_rng(seed)
    occupied_indices = np.flatnonzero(voxel.multiplicity >= 2)
    if occupied_indices.size == 0:
        return []
    selected = rng.choice(occupied_indices, size=min(sample_count, occupied_indices.size), replace=False)
    radii = sorted(set([delta, min(rho, 1.0), min(math.sqrt(max(delta, 1e-12)), 1.0), 1.0]))
    results: list[BroadnessRecord] = []
    directions = np.array([t.direction for t in tubes])
    for radius in radii:
        worst_fraction = 0.0
        for idx in selected:
            members = np.flatnonzero(voxel.membership[:, idx])
            if members.size == 0:
                continue
            local_dirs = directions[members]
            dots = np.abs(local_dirs @ local_dirs.T)
            angles = np.arccos(np.clip(dots, -1.0, 1.0))
            cap = int(np.max(np.sum(angles <= radius, axis=1)))
            worst_fraction = max(worst_fraction, cap / members.size)
        denominator = max(radius**beta, 1e-15)
        results.append(BroadnessRecord(radius, worst_fraction, beta, worst_fraction / denominator))
    return results


def local_density(
    voxel: VoxelResult,
    tau: float,
    seed: int,
    samples: int = 60,
) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    occupied = np.flatnonzero(voxel.shaded_multiplicity > 0)
    if occupied.size == 0:
        return tau, 0.0
    chosen = rng.choice(occupied, size=min(samples, occupied.size), replace=False)
    fractions: list[float] = []
    for idx in chosen:
        center = voxel.points[idx]
        d2 = np.sum((voxel.points - center) ** 2, axis=1)
        ball = d2 <= tau**2
        if np.any(ball):
            fractions.append(float(np.mean(voxel.shaded_multiplicity[ball] > 0)))
    return tau, float(np.median(fractions)) if fractions else 0.0


def analyze_multiscale(
    tubes: list[Tube],
    voxel: VoxelResult,
    delta: float,
    rho: float,
    omega: float,
    zeta: float,
    seed: int,
) -> MultiScaleMetrics:
    assignments = regroup_by_angular_scale(tubes, rho)
    group_count = max(assignments) + 1 if assignments else 0
    group_sizes = [assignments.count(g) for g in range(group_count)]

    occupied = voxel.multiplicity > 0
    full = voxel.multiplicity[occupied].astype(float)
    group_presence = np.zeros((group_count, int(np.count_nonzero(occupied))), dtype=np.uint8)
    for g in range(group_count):
        member_ids = [i for i, a in enumerate(assignments) if a == g]
        if member_ids:
            group_presence[g] = np.any(voxel.membership[member_ids][:, occupied], axis=0)
    coarse = group_presence.sum(axis=0).astype(float)
    valid = coarse > 0
    fine_pointwise = np.divide(full, coarse, out=np.zeros_like(full), where=valid)
    mu = float(np.median(full[valid])) if np.any(valid) else 0.0
    mu_coarse = float(np.median(coarse[valid])) if np.any(valid) else 0.0
    mu_fine = float(np.median(fine_pointwise[valid])) if np.any(valid) else 0.0
    product_ratio = mu / max(mu_fine * mu_coarse, 1e-15)

    typical_group = max(float(np.median(group_sizes)) if group_sizes else 1.0, 1.0)
    target = typical_group / max((rho / delta) ** 2, 1e-15)
    inferred_nu = math.log(max(target, 1e-15)) / math.log(delta) if delta not in {0.0, 1.0} else 0.0
    grain_c = max(delta / rho, (rho / delta) / math.sqrt(typical_group))
    grain_c = min(1.0, grain_c)

    beta = max(omega * zeta / 100.0, 1e-6)
    broadness = estimate_broadness(tubes, voxel, delta, rho, beta, sample_count=90, seed=seed + 17)
    tau = min(0.8, max(2.0 * delta, math.sqrt(delta * rho)))
    tau, density = local_density(voxel, tau, seed + 29)

    return MultiScaleMetrics(
        group_count=group_count,
        group_sizes=group_sizes,
        inferred_nu=float(inferred_nu),
        mu=mu,
        mu_fine=mu_fine,
        mu_coarse=mu_coarse,
        product_ratio=float(product_ratio),
        grain_c=float(grain_c),
        grain_dimensions_rescaled=(delta / rho, grain_c, grain_c),
        grain_dimensions_original=(delta, rho * grain_c, grain_c),
        broadness=broadness,
        local_density_tau=float(tau),
        local_density_fraction=float(density),
    )
