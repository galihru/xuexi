from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import secrets

from .formulas import FormulaCheck, FormulaParameters, complete_registry, evaluate_key_formulas
from .generator import generate_tubes
from .multiscale import analyze_multiscale
from .report import write_formula_csv, write_metrics_json, write_probe_csv, write_random_log, write_tubes_csv
from .viewer import create_viewer
from .media import create_preview, create_rotation_video
from .site import build_site
from .voxel import voxelize
from .wolff import estimate_wolff_constants
from xuexi_agent.generated.strategy import mutate_parameters
from xuexi_agent.generated.equation_extensions import evaluate as evaluate_extensions


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="三维 Kakeya δ-管数值实验")
    p.add_argument("--mode", choices=["uniform", "sticky", "nonsticky", "hairbrush", "grains", "mixed"], default="mixed")
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--tubes", type=int, default=64)
    p.add_argument("--delta", type=float, default=0.055)
    p.add_argument("--rho", type=float, default=0.24)
    p.add_argument("--lambda-density", type=float, default=0.72)
    p.add_argument("--resolution", type=int, default=52)
    p.add_argument("--epsilon", type=float, default=0.05)
    p.add_argument("--k-power", type=float, default=3.0)
    p.add_argument("--kappa", type=float, default=0.1)
    p.add_argument("--sigma", type=float, default=0.5)
    p.add_argument("--omega", type=float, default=0.1)
    p.add_argument("--alpha", type=float, default=0.03)
    p.add_argument("--zeta", type=float, default=0.01)
    p.add_argument("--dilation-r", type=float, default=2.0)
    p.add_argument("--frames", type=int, default=60)
    p.add_argument("--fps", type=int, default=15)
    p.add_argument("--site-output", type=Path, default=Path("site"))
    p.add_argument("--output", type=Path, default=Path("artifacts/latest"))
    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if not (0.0 < args.delta < args.rho <= 1.0):
        raise SystemExit("必须满足 0 < δ < ρ ≤ 1。")
    if not (0.0 < args.lambda_density <= 1.0):
        raise SystemExit("着色密度必须位于 (0,1]。")
    seed = args.seed if args.seed is not None else secrets.randbits(63)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)

    base_parameters = {
        "mode": args.mode,
        "tubes": args.tubes,
        "delta": args.delta,
        "rho": args.rho,
        "lambda_density": args.lambda_density,
        "resolution": args.resolution,
        "epsilon": args.epsilon,
        "k_power": args.k_power,
        "kappa": args.kappa,
        "sigma": args.sigma,
        "omega": args.omega,
        "alpha": args.alpha,
        "zeta": args.zeta,
        "dilation_r": args.dilation_r,
    }
    learned = mutate_parameters(base_parameters, {"seed": seed, "source": "kakeya_sim.cli"})
    if not isinstance(learned, dict):
        raise SystemExit("学习策略必须返回参数字典。")
    parameters_used = {**base_parameters, **learned}
    delta = float(parameters_used["delta"])
    rho = float(parameters_used["rho"])
    lam = float(parameters_used["lambda_density"])
    tube_count = int(parameters_used["tubes"])
    resolution = int(parameters_used["resolution"])
    mode = str(parameters_used["mode"])
    if not (0.0 < delta < rho <= 1.0):
        raise SystemExit("学习策略生成了非法尺度，必须满足 0 < δ < ρ ≤ 1。")
    if not (0.0 < lam <= 1.0):
        raise SystemExit("学习策略生成了非法着色密度。")

    tubes = generate_tubes(mode, seed, tube_count, delta, rho, lam)
    voxel = voxelize(tubes, resolution)
    wolff = estimate_wolff_constants(tubes, seed + 101)
    multi = analyze_multiscale(tubes, voxel, delta, rho, float(parameters_used["omega"]), float(parameters_used["zeta"]), seed + 202)
    parameters = FormulaParameters(
        epsilon=float(parameters_used["epsilon"]),
        k_power=float(parameters_used["k_power"]),
        kappa=float(parameters_used["kappa"]),
        sigma=float(parameters_used["sigma"]),
        omega=float(parameters_used["omega"]),
        alpha=float(parameters_used["alpha"]),
        zeta=float(parameters_used["zeta"]),
        rho=rho,
        dilation_r=float(parameters_used["dilation_r"]),
    )
    checks = evaluate_key_formulas(tubes, voxel, wolff, multi, parameters)
    extension_metrics = {
        "tube_count": len(tubes),
        "delta": delta,
        "rho": rho,
        "union_volume": voxel.union_volume,
        "shaded_union_volume": voxel.shaded_union_volume,
        "average_multiplicity": voxel.average_multiplicity,
        "median_multiplicity": voxel.median_multiplicity,
        "maximum_multiplicity": voxel.max_multiplicity,
        "katz_tao_convex": wolff.katz_tao_convex,
        "frostman_slab": wolff.frostman_slab,
        "grain_c": multi.grain_c,
        "mu": multi.mu,
        "mu_fine": multi.mu_fine,
        "mu_coarse": multi.mu_coarse,
    }
    for item in evaluate_extensions(extension_metrics, parameters_used):
        if not isinstance(item, dict):
            continue
        checks.append(FormulaCheck(
            label=str(item.get("label", "generated")),
            status=str(item.get("status", "学习代理数值诊断")),
            observed=None if item.get("observed") is None else float(item["observed"]),
            reference=None if item.get("reference") is None else float(item["reference"]),
            ratio=None if item.get("ratio") is None else float(item["ratio"]),
            passed=None if item.get("passed") is None else bool(item["passed"]),
            note=str(item.get("note", "由学习代理生成。")),
        ))
    registry = Path(__file__).resolve().parents[2] / "data" / "equation_registry.csv"
    checks = complete_registry(checks, registry)

    metadata = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "seed": seed,
        "mode": mode,
        "resolution": resolution,
        "learned_parameters": parameters_used,
        "paper": "Volume estimates for unions of convex sets, and the Kakeya set conjecture in three dimensions",
        "authors": "Hong Wang and Joshua Zahl",
        "arxiv": "2502.17655v1",
    }
    data = write_metrics_json(output / "metrics.json", tubes, voxel, wolff, multi, parameters, metadata)
    write_tubes_csv(output / "tubes.csv", tubes)
    write_probe_csv(output / "wolff_probes.csv", wolff)
    write_formula_csv(output / "formula_checks.csv", checks)
    write_random_log(output / "random_log.md", data, checks, tubes)
    create_viewer(tubes, voxel, output / "viewer.html", seed + 303)
    create_preview(tubes, voxel, output / "preview.png", seed + 404)
    create_rotation_video(
        tubes, voxel, output / "rotation.mp4", output / "rotation.gif",
        seed + 505, frames=args.frames, fps=args.fps,
    )
    build_site(output, args.site_output)

    print(f"模拟完成，随机种子：{seed}")
    print(f"三维查看器：{output / 'viewer.html'}")
    print(f"数值指标：{output / 'metrics.json'}")
    print(f"旋转视频：{output / 'rotation.mp4'}")
    print(f"网站：{args.site_output / 'index.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
