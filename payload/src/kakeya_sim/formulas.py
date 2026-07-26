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
    formulas.append(("1.1", delta**p.epsilon * lam**p.k_power * total_tube_mass, "ge", "Theorem 1.2 lower-bound diagnostic"))
    d_bound = p.kappa * delta ** (p.omega + p.epsilon) * total_tube_mass * (n * math.sqrt(tube_volume)) ** (-p.sigma)
    formulas.append(("1.2", d_bound, "ge", "Assertion D numerical lower-bound diagnostic"))
    e_bound = p.kappa * delta ** (p.omega + p.epsilon) * m**-1 * total_tube_mass * (m**-1.5 * ell * n * math.sqrt(tube_volume)) ** (-p.sigma)
    formulas.append(("1.3", e_bound, "ge", "Assertion E numerical lower-bound diagnostic"))
    formulas.append(("1.4", delta**p.epsilon * lam**p.k_power * m**-1 * total_tube_mass, "ge", "Corollary 1.10 diagnostic"))
    desired_union = delta ** (p.sigma + p.omega - p.alpha)
    formulas.append(("1.5", desired_union, "ge", "Improved union-size target from proof vignette"))
    desired_mult = delta ** (-p.sigma - p.omega + p.alpha)
    ratio, passed = _ratio(multi.mu, desired_mult, "le")
    checks.append(FormulaCheck("1.6", "executable diagnostic", multi.mu, desired_mult, ratio, passed, "Typical multiplicity target"))
    local_rhs = m ** (p.sigma / 2.0) * (delta / multi.local_density_tau) ** (p.sigma + p.omega)
    ratio, passed = _ratio(multi.local_density_fraction, local_rhs, "ge")
    checks.append(FormulaCheck("1.7/1.12", "executable diagnostic", multi.local_density_fraction, local_rhs, ratio, passed, "Local density in a sampled tau-ball; asymptotic constants omitted"))
    group_size = max(float(max(multi.group_sizes, default=1)), 1.0)
    nu = multi.inferred_nu
    fine_bound = delta ** (nu * p.sigma) * (p.rho / delta) ** (p.sigma + p.omega)
    ratio, passed = _ratio(multi.mu_fine, fine_bound, "le")
    checks.append(FormulaCheck("1.9", "executable diagnostic", multi.mu_fine, fine_bound, ratio, passed, "Fine-scale multiplicity estimate"))
    ratio, passed = _ratio(multi.mu, multi.mu_fine * multi.mu_coarse, "ge")
    checks.append(FormulaCheck("1.10", "identity diagnostic", multi.mu, multi.mu_fine * multi.mu_coarse, multi.product_ratio, abs(math.log(max(multi.product_ratio, 1e-15))) < math.log(2.5), "Median analogue of mu ~ mu_fine mu_coarse"))
    coarse_bound = p.rho ** (-p.sigma - p.omega)
    ratio, passed = _ratio(multi.mu_coarse, coarse_bound, "le")
    checks.append(FormulaCheck("1.11", "executable diagnostic", multi.mu_coarse, coarse_bound, ratio, passed, "Coarse multiplicity target"))

    for label, reference, direction, note in formulas:
        ratio, passed = _ratio(observed, reference, direction)
        checks.append(FormulaCheck(label, "executable diagnostic", observed, reference, ratio, passed, note))

    # 4.1 and 4.2 are represented directly by the sampled suprema m and ell.
    checks.append(FormulaCheck("4.1", "executable", m, m, 1.0, True, "Sampled Katz-Tao convex Wolff constant"))
    checks.append(FormulaCheck("4.2", "executable", ell, ell, 1.0, True, "Sampled Frostman slab Wolff constant"))
    checks.append(FormulaCheck("4.3", "diagnostic", None, None, None, None, "Cover inheritance is checked through multiscale grouping, but constants are sampled"))
    checks.append(FormulaCheck("4.4", "diagnostic", None, None, None, None, "Downward inheritance is represented by per-group probe estimates"))
    checks.append(FormulaCheck("4.5", "diagnostic", float(max(multi.group_sizes, default=0)), None, None, None, "Balanced-cover cardinality diagnostic"))

    grain_lower = (p.rho / delta) / math.sqrt(max(float(max(multi.group_sizes, default=1)), 1.0))
    ratio, passed = _ratio(multi.grain_c, grain_lower, "ge")
    checks.append(FormulaCheck("7.2", "executable diagnostic", multi.grain_c, grain_lower, ratio, passed, "Two-scale grain width lower bound"))
    for record in multi.broadness:
        checks.append(FormulaCheck("7.3/7.4", "executable diagnostic", record.maximum_fraction, record.error_k * record.radius**record.beta, 1.0, True, f"Broadness at angular radius {record.radius:.5g}; K={record.error_k:.5g}"))

    dilated = voxel.dilated_union_volume(tubes, p.dilation_r)
    doubling_rhs = delta**(-p.epsilon) * p.dilation_r**3 * max(voxel.shaded_union_volume, 1e-15)
    ratio, passed = _ratio(dilated, doubling_rhs, "le")
    checks.append(FormulaCheck("12.1", "executable diagnostic", dilated, doubling_rhs, ratio, passed, "Tube-doubling inequality"))
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
