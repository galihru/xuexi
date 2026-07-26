from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
import csv
import json

import numpy as np

from .formulas import FormulaCheck, FormulaParameters
from .geometry import Tube
from .multiscale import MultiScaleMetrics
from .voxel import VoxelResult
from .wolff import WolffEstimate


def write_tubes_csv(path: Path, tubes: list[Tube]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["id", "group", "cx", "cy", "cz", "dx", "dy", "dz", "delta", "shade_start", "shade_end"])
        for i, t in enumerate(tubes):
            writer.writerow([i, t.group, *t.center.tolist(), *t.direction.tolist(), t.radius, t.shade_start, t.shade_end])


def write_formula_csv(path: Path, checks: list[FormulaCheck]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["label", "status", "observed", "reference", "ratio", "passed", "note"])
        writer.writeheader()
        for check in checks:
            writer.writerow(asdict(check))


def write_probe_csv(path: Path, wolff: WolffEstimate) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = ["kind", "volume", "contained", "katz_tao_ratio", "frostman_ratio", "a", "b", "thickness"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for record in [*wolff.box_probes, *wolff.slab_probes]:
            writer.writerow(asdict(record))


def write_metrics_json(
    path: Path,
    tubes: list[Tube],
    voxel: VoxelResult,
    wolff: WolffEstimate,
    multi: MultiScaleMetrics,
    parameters: FormulaParameters,
    metadata: dict,
) -> dict:
    occupied = voxel.multiplicity > 0
    histogram = {str(int(k)): int(v) for k, v in zip(*np.unique(voxel.multiplicity[occupied], return_counts=True))}
    data = {
        "metadata": metadata,
        "parameters": asdict(parameters),
        "geometry": {
            "tube_count": len(tubes),
            "paper_single_tube_volume": tubes[0].paper_volume,
            "capsule_single_tube_volume": tubes[0].capsule_volume,
            "sum_paper_tube_volume": len(tubes) * tubes[0].paper_volume,
            "mean_shading_fraction": float(np.mean([t.shading_fraction for t in tubes])),
        },
        "voxel": {
            "spacing": voxel.spacing,
            "union_volume": voxel.union_volume,
            "shaded_union_volume": voxel.shaded_union_volume,
            "average_multiplicity": voxel.average_multiplicity,
            "median_multiplicity": voxel.median_multiplicity,
            "maximum_multiplicity": voxel.max_multiplicity,
            "multiplicity_histogram": histogram,
        },
        "wolff": {
            "katz_tao_convex": wolff.katz_tao_convex,
            "frostman_slab": wolff.frostman_slab,
            "prism_nonclustering_ratio": wolff.prism_nonclustering_ratio,
        },
        "multiscale": asdict(multi),
    }
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return data


def write_random_log(path: Path, data: dict, checks: list[FormulaCheck], tubes: list[Tube]) -> None:
    meta = data["metadata"]
    voxel = data["voxel"]
    wolff = data["wolff"]
    multi = data["multiscale"]
    lines = [
        "# Random Numerical Run Log",
        "",
        f"- UTC generation time: `{meta['generated_at']}`",
        f"- Seed: `{meta['seed']}`",
        f"- Mode: `{meta['mode']}`",
        f"- Tubes: `{len(tubes)}`",
        f"- Voxel resolution: `{meta['resolution']}^3`",
        "",
        "## Main numerical observations",
        "",
        f"- Voxelized union volume: `{voxel['union_volume']:.10f}`",
        f"- Voxelized shaded union volume: `{voxel['shaded_union_volume']:.10f}`",
        f"- Median multiplicity: `{voxel['median_multiplicity']:.6f}`",
        f"- Maximum multiplicity: `{voxel['maximum_multiplicity']}`",
        f"- Sampled Katz-Tao convex Wolff constant: `{wolff['katz_tao_convex']:.8f}`",
        f"- Sampled Frostman slab Wolff constant: `{wolff['frostman_slab']:.8f}`",
        f"- Worst rectangular-prism hypothesis ratio: `{wolff['prism_nonclustering_ratio']:.8f}`",
        f"- Coarse group count: `{multi['group_count']}`",
        f"- Grain width c: `{multi['grain_c']:.8f}`",
        "",
        "## First random tubes",
        "",
        "| Tube | Group | Center | Direction | Shading interval |",
        "|---:|---:|---|---|---|",
    ]
    for i, t in enumerate(tubes[:12]):
        center = ", ".join(f"{x:.5f}" for x in t.center)
        direction = ", ".join(f"{x:.5f}" for x in t.direction)
        lines.append(f"| {i} | {t.group} | ({center}) | ({direction}) | [{t.shade_start:.5f}, {t.shade_end:.5f}] |")
    lines.extend(["", "## Formula diagnostics", "", "These checks are finite-resolution numerical diagnostics, not proofs of asymptotic theorems.", "", "| Equation | Status | Observed | Reference | Ratio | Result |", "|---|---|---:|---:|---:|---|"])
    for c in checks:
        if c.observed is None:
            continue
        observed = f"{c.observed:.8g}"
        reference = "" if c.reference is None else f"{c.reference:.8g}"
        ratio = "" if c.ratio is None else f"{c.ratio:.8g}"
        result = "N/A" if c.passed is None else ("PASS" if c.passed else "FAIL")
        lines.append(f"| {c.label} | {c.status} | {observed} | {reference} | {ratio} | {result} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
