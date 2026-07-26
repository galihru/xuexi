from __future__ import annotations

from dataclasses import asdict
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
        writer.writerow(["编号", "分组", "中心_x", "中心_y", "中心_z", "方向_x", "方向_y", "方向_z", "delta", "着色起点", "着色终点"])
        for i, tube in enumerate(tubes):
            writer.writerow([i, tube.group, *tube.center.tolist(), *tube.direction.tolist(), tube.radius, tube.shade_start, tube.shade_end])


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
    histogram = {str(int(key)): int(value) for key, value in zip(*np.unique(voxel.multiplicity[occupied], return_counts=True))}
    data = {
        "metadata": metadata,
        "parameters": asdict(parameters),
        "geometry": {
            "tube_count": len(tubes),
            "paper_single_tube_volume": tubes[0].paper_volume,
            "capsule_single_tube_volume": tubes[0].capsule_volume,
            "sum_paper_tube_volume": len(tubes) * tubes[0].paper_volume,
            "mean_shading_fraction": float(np.mean([tube.shading_fraction for tube in tubes])),
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
        "# 随机数值实验记录",
        "",
        f"- UTC 生成时间：`{meta['generated_at']}`",
        f"- 随机种子：`{meta['seed']}`",
        f"- 排列模式：`{meta['mode']}`",
        f"- 管数量：`{len(tubes)}`",
        f"- 体素分辨率：`{meta['resolution']}^3`",
        "",
        "## 主要数值观察",
        "",
        f"- 并集体积估计：`{voxel['union_volume']:.10f}`",
        f"- 着色并集体积估计：`{voxel['shaded_union_volume']:.10f}`",
        f"- 中位重数：`{voxel['median_multiplicity']:.6f}`",
        f"- 最大重数：`{voxel['maximum_multiplicity']}`",
        f"- Katz–Tao 凸 Wolff 常数采样估计：`{wolff['katz_tao_convex']:.8f}`",
        f"- Frostman 板 Wolff 常数采样估计：`{wolff['frostman_slab']:.8f}`",
        f"- 长方体非聚集最坏比值：`{wolff['prism_nonclustering_ratio']:.8f}`",
        f"- 粗尺度分组数：`{multi['group_count']}`",
        f"- grain 宽度 c：`{multi['grain_c']:.8f}`",
        "",
        "## 前十二个随机管",
        "",
        "| 管 | 分组 | 中心 | 方向 | 着色区间 |",
        "|---:|---:|---|---|---|",
    ]
    for i, tube in enumerate(tubes[:12]):
        center = ", ".join(f"{value:.5f}" for value in tube.center)
        direction = ", ".join(f"{value:.5f}" for value in tube.direction)
        lines.append(f"| {i} | {tube.group} | ({center}) | ({direction}) | [{tube.shade_start:.5f}, {tube.shade_end:.5f}] |")
    lines.extend([
        "",
        "## 公式诊断",
        "",
        "> 下列结果是有限分辨率数值诊断，不构成对渐近定理的证明。",
        "",
        "| 公式 | 类型 | 观测值 | 参考值 | 比值 | 结果 |",
        "|---|---|---:|---:|---:|---|",
    ])
    for check in checks:
        if check.observed is None:
            continue
        observed = f"{check.observed:.8g}"
        reference = "" if check.reference is None else f"{check.reference:.8g}"
        ratio = "" if check.ratio is None else f"{check.ratio:.8g}"
        result = "不适用" if check.passed is None else ("通过" if check.passed else "未通过")
        lines.append(f"| {check.label} | {check.status} | {observed} | {reference} | {ratio} | {result} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
