from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .geometry import Tube


@dataclass
class VoxelResult:
    points: np.ndarray
    spacing: float
    multiplicity: np.ndarray
    shaded_multiplicity: np.ndarray
    membership: np.ndarray  # shape (tube_count, point_count), bool
    shaded_membership: np.ndarray

    @property
    def voxel_volume(self) -> float:
        return self.spacing**3

    @property
    def union_volume(self) -> float:
        return float(np.count_nonzero(self.multiplicity) * self.voxel_volume)

    @property
    def shaded_union_volume(self) -> float:
        return float(np.count_nonzero(self.shaded_multiplicity) * self.voxel_volume)

    @property
    def average_multiplicity(self) -> float:
        occupied = self.multiplicity > 0
        return float(np.mean(self.multiplicity[occupied])) if np.any(occupied) else 0.0

    @property
    def median_multiplicity(self) -> float:
        occupied = self.multiplicity > 0
        return float(np.median(self.multiplicity[occupied])) if np.any(occupied) else 0.0

    @property
    def max_multiplicity(self) -> int:
        return int(np.max(self.multiplicity, initial=0))

    def dilated_union_volume(self, tubes: list[Tube], radius_scale: float) -> float:
        counts = np.zeros(self.points.shape[0], dtype=np.uint16)
        for tube in tubes:
            counts += tube.contains(self.points, radius_scale=radius_scale).astype(np.uint16)
        return float(np.count_nonzero(counts) * self.voxel_volume)


def voxelize(
    tubes: list[Tube],
    resolution: int,
    extent: float = 1.05,
) -> VoxelResult:
    if resolution < 12:
        raise ValueError("Resolution must be at least 12")
    axis = np.linspace(-extent, extent, resolution, endpoint=False) + extent / resolution
    x, y, z = np.meshgrid(axis, axis, axis, indexing="ij")
    points = np.column_stack([x.ravel(), y.ravel(), z.ravel()])
    membership = np.zeros((len(tubes), len(points)), dtype=bool)
    shaded_membership = np.zeros_like(membership)
    for i, tube in enumerate(tubes):
        membership[i] = tube.contains(points, shaded=False)
        shaded_membership[i] = tube.contains(points, shaded=True)
    multiplicity = membership.sum(axis=0, dtype=np.uint16)
    shaded_multiplicity = shaded_membership.sum(axis=0, dtype=np.uint16)
    return VoxelResult(
        points=points,
        spacing=2.0 * extent / resolution,
        multiplicity=multiplicity,
        shaded_multiplicity=shaded_multiplicity,
        membership=membership,
        shaded_membership=shaded_membership,
    )
