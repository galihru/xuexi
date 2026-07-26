from __future__ import annotations

from dataclasses import dataclass, asdict
import math

import numpy as np

from .geometry import OrientedBox, Slab, Tube, normalize, orthonormal_frame


@dataclass
class ProbeRecord:
    kind: str
    volume: float
    contained: int
    katz_tao_ratio: float
    frostman_ratio: float
    a: float | None = None
    b: float | None = None
    thickness: float | None = None


@dataclass
class WolffEstimate:
    katz_tao_convex: float
    frostman_slab: float
    prism_nonclustering_ratio: float
    box_probes: list[ProbeRecord]
    slab_probes: list[ProbeRecord]


def _sample_scales(delta: float, count: int) -> np.ndarray:
    return np.geomspace(max(delta * 1.05, 1e-4), 1.0, max(2, count))


def estimate_wolff_constants(
    tubes: list[Tube],
    seed: int,
    box_probe_count: int = 180,
    slab_probe_count: int = 180,
) -> WolffEstimate:
    rng = np.random.default_rng(seed)
    n = len(tubes)
    if n == 0:
        raise ValueError("At least one tube is required")
    delta = tubes[0].radius
    paper_volume = tubes[0].paper_volume
    scales = _sample_scales(delta, 12)

    m = 1.0
    ell = 0.0
    worst_prism = 0.0
    box_records: list[ProbeRecord] = []
    slab_records: list[ProbeRecord] = []

    for _ in range(box_probe_count):
        anchor = tubes[int(rng.integers(0, n))]
        a = float(rng.choice(scales))
        b = float(rng.choice(scales[scales >= a]))
        roll = float(rng.uniform(0.0, 2.0 * math.pi))
        u, v, w = orthonormal_frame(anchor.direction, roll)
        center = anchor.center + rng.normal(scale=0.15, size=3)
        box = OrientedBox(center=center, axes=np.vstack([u, v, w]), lengths=np.array([a, b, 2.0]))
        contained = sum(box.contains_tube(t) for t in tubes)
        kt = contained * paper_volume / max(box.volume, 1e-15)
        fr = contained / max(box.volume * n, 1e-15)
        prism_ratio = contained / max(100.0 * a * b * delta**-2, 1e-15)
        m = max(m, kt)
        worst_prism = max(worst_prism, prism_ratio)
        box_records.append(ProbeRecord("oriented_box", box.volume, contained, kt, fr, a=a, b=b))

    for _ in range(slab_probe_count):
        normal = normalize(rng.normal(size=3))
        h = float(rng.choice(scales)) / 2.0
        offset = float(rng.uniform(-0.8, 0.8))
        slab = Slab(normal=normal, offset=offset, half_thickness=h)
        contained = sum(slab.contains_tube(t) for t in tubes)
        volume = slab.unit_ball_volume
        fr = contained / max(volume * n, 1e-15)
        kt = contained * paper_volume / max(volume, 1e-15)
        ell = max(ell, fr)
        slab_records.append(ProbeRecord("slab", volume, contained, kt, fr, thickness=2.0 * h))

    return WolffEstimate(
        katz_tao_convex=float(m),
        frostman_slab=float(max(ell, 1e-15)),
        prism_nonclustering_ratio=float(worst_prism),
        box_probes=box_records,
        slab_probes=slab_records,
    )
