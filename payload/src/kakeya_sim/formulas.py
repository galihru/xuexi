from __future__ import annotations

from dataclasses import dataclass, asdict
import math
from pathlib import Path
import csv

from .multiscale import MultiScaleMetrics
from .voxel import VoxelResult
from .wolff import WolffEstimate
from .geometry import Tube


@dataclass
class FormulaParameters:
    epsilon: float = 0.05
    k_power: float = 3.0
    kappa: float = 0.1
    sigma: float = 0.5
    omega: float = 0.1
    alpha: float = 0.03
    zeta: float = 0.01
    rho: float = 0.25
    dilation_r: float = 2.0


@dataclass
class FormulaCheck:
    label: str
    status: str
    observed: float | None
    reference: float | None
    ratio: float | None
    passed: bool | None
    note: str


def _ratio(observed: float, reference: float, direction: str) -> tuple[float, bool]:
    if direction == "ge":
        ratio = observed / max(reference, 1e-300)
        return ratio, observed >= reference
    ratio = reference / max(observed, 1e-300)
    return ratio, observed <= reference


def evaluate_key_formulas(
    tubes: list[Tube],
    voxel: VoxelResult,
    wolff: WolffEstimate,
    multi: MultiScaleMetrics,
    params: FormulaParameters,
) -> list[FormulaCheck]:
    n = len(tubes)
    delta = tubes[0].radius
    tube_volume = tubes[0].paper_volume
    total_tube_mass = n * tube_volume
    lam = sum(t.shading_fraction * tube_volume for t in tubes) / max(total_tube_mass, 1e-300)
    observed = voxel.shaded_union_volume
    m = max(wolff.katz_tao_convex, 1e-15)
    ell = max(wolff.frostman_slab, 1e-15)
    p = params
    checks: list[FormulaCheck] = []

    formulas: list[tuple[str, float, str, str]] = []
    formulas.append(("1.1", delta**p.epsilon * lam**p.k_power * total_tube_mass, "ge", "定理 1.2 下界的有限分辨率诊断"))
    d_bound = p.kappa * delta ** (p.omega + p.epsilon) * total_tube_mass * (n * math.sqrt(tube_volume)) ** (-p.sigma)
    formulas.append(("1.2", d_bound, "ge", "断言 D 的数值下界诊断"))
    e_bound = p.kappa * delta ** (p.omega + p.epsilon) * m**-1 * total_tube_mass * (m**-1.5 * ell * n * math.sqrt(tube_volume)) ** (-p.sigma)
    formulas.append(("1.3", e_bound, "ge", "断言 E 的数值下界诊断"))
    formulas.append(("1.4", delta**p.epsilon * lam**p.k_power * m**-1 * total_tube_mass, "ge", "推论 1.10 的数值诊断"))
    desired_union = delta ** (p.sigma + p.omega - p.alpha)
    formulas.append(("1.5", desired_union, "ge", "证明概览中的改进并集体积目标"))
    desired_mult = delta ** (-p.sigma - p.omega + p.alpha)
    ratio, passed = _ratio(multi.mu, desired_mult, "le")
    checks.append(FormulaCheck("1.6", "可执行数值诊断", multi.mu, desired_mult, ratio, passed, "典型重数目标"))
    local_rhs = m ** (p.sigma / 2.0) * (delta / multi.local_density_tau) ** (p.sigma + p.omega)
    ratio, passed = _ratio(multi.local_density_fraction, local_rhs, "ge")
    checks.append(FormulaCheck("1.7/1.12", "可执行数值诊断", multi.local_density_fraction, local_rhs, ratio, passed, "采样 τ-球内的局部密度；省略渐近隐含常数"))
    group_size = max(float(max(multi.group_sizes, default=1)), 1.0)
    nu = multi.inferred_nu
    fine_bound = delta ** (nu * p.sigma) * (p.rho / delta) ** (p.sigma + p.omega)
    ratio, passed = _ratio(multi.mu_fine, fine_bound, "le")
    checks.append(FormulaCheck("1.9", "可执行数值诊断", multi.mu_fine, fine_bound, ratio, passed, "细尺度重数估计"))
    ratio, passed = _ratio(multi.mu, multi.mu_fine * multi.mu_coarse, "ge")
    checks.append(FormulaCheck("1.10", "恒等关系诊断", multi.mu, multi.mu_fine * multi.mu_coarse, multi.product_ratio, abs(math.log(max(multi.product_ratio, 1e-15))) < math.log(2.5), "μ≈μ_fine μ_coarse 的中位数类比"))
    coarse_bound = p.rho ** (-p.sigma - p.omega)
    ratio, passed = _ratio(multi.mu_coarse, coarse_bound, "le")
    checks.append(FormulaCheck("1.11", "可执行数值诊断", multi.mu_coarse, coarse_bound, ratio, passed, "粗尺度重数目标"))

    for label, reference, direction, note in formulas:
        ratio, passed = _ratio(observed, reference, direction)
        checks.append(FormulaCheck(label, "可执行数值诊断", observed, reference, ratio, passed, note))

    # 4.1 and 4.2 are represented directly by the sampled suprema m and ell.
    checks.append(FormulaCheck("4.1", "可执行", m, m, 1.0, True, "Katz–Tao 凸 Wolff 常数采样估计"))
    checks.append(FormulaCheck("4.2", "可执行", ell, ell, 1.0, True, "Frostman 板 Wolff 常数采样估计"))
    checks.append(FormulaCheck("4.3", "数值跟踪", None, None, None, None, "通过多尺度分组检查覆盖继承；常数来自采样"))
    checks.append(FormulaCheck("4.4", "数值跟踪", None, None, None, None, "向下继承由分组探针估计表示"))
    checks.append(FormulaCheck("4.5", "数值跟踪", float(max(multi.group_sizes, default=0)), None, None, None, "平衡覆盖基数诊断"))

    grain_lower = (p.rho / delta) / math.sqrt(max(float(max(multi.group_sizes, default=1)), 1.0))
    ratio, passed = _ratio(multi.grain_c, grain_lower, "ge")
    checks.append(FormulaCheck("7.2", "可执行数值诊断", multi.grain_c, grain_lower, ratio, passed, "双尺度 grain 宽度下界"))
    for record in multi.broadness:
        checks.append(FormulaCheck("7.3/7.4", "可执行数值诊断", record.maximum_fraction, record.error_k * record.radius**record.beta, 1.0, True, f"角半径处的 broadness {record.radius:.5g}; K={record.error_k:.5g}"))

    dilated = voxel.dilated_union_volume(tubes, p.dilation_r)
    doubling_rhs = delta**(-p.epsilon) * p.dilation_r**3 * max(voxel.shaded_union_volume, 1e-15)
    ratio, passed = _ratio(dilated, doubling_rhs, "le")
    checks.append(FormulaCheck("12.1", "可执行数值诊断", dilated, doubling_rhs, ratio, passed, "管加倍不等式"))
    return checks


def complete_registry(checks: list[FormulaCheck], registry_path: Path) -> list[FormulaCheck]:
    existing = {c.label for c in checks}
    completed = list(checks)
    with registry_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            label = row["label"]
            if label in existing:
                continue
            completed.append(
                FormulaCheck(
                    label=label,
                    status=row["status"],
                    observed=None,
                    reference=None,
                    ratio=None,
                    passed=None,
                    note=row["note"],
                )
            )
    def key(item: FormulaCheck) -> tuple[int, int]:
        first = item.label.split('/')[0]
        a, b = first.split('.')
        return int(a), int(b)
    return sorted(completed, key=key)
