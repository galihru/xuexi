from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import secrets

from .formulas import FormulaParameters, complete_registry, evaluate_key_formulas
from .generator import generate_tubes
from .multiscale import analyze_multiscale
from .report import write_formula_csv, write_metrics_json, write_probe_csv, write_random_log, write_tubes_csv
from .viewer import create_viewer
from .voxel import voxelize
from .wolff import estimate_wolff_constants


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="3D numerical Kakeya tube experiment")
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
    p.add_argument("--output", type=Path, default=Path("artifacts/latest"))
    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if not (0.0 < args.delta < args.rho <= 1.0):
        raise SystemExit("Require 0 < delta < rho <= 1")
    if not (0.0 < args.lambda_density <= 1.0):
        raise SystemExit("lambda-density must lie in (0,1]")
    seed = args.seed if args.seed is not None else secrets.randbits(63)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)

    tubes = generate_tubes(args.mode, seed, args.tubes, args.delta, args.rho, args.lambda_density)
    voxel = voxelize(tubes, args.resolution)
    wolff = estimate_wolff_constants(tubes, seed + 101)
    multi = analyze_multiscale(tubes, voxel, args.delta, args.rho, args.omega, args.zeta, seed + 202)
    parameters = FormulaParameters(
        epsilon=args.epsilon,
        k_power=args.k_power,
        kappa=args.kappa,
        sigma=args.sigma,
        omega=args.omega,
        alpha=args.alpha,
        zeta=args.zeta,
        rho=args.rho,
        dilation_r=args.dilation_r,
    )
    checks = evaluate_key_formulas(tubes, voxel, wolff, multi, parameters)
    registry = Path(__file__).resolve().parents[2] / "data" / "equation_registry.csv"
    checks = complete_registry(checks, registry)

    metadata = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "seed": seed,
        "mode": args.mode,
        "resolution": args.resolution,
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

    print(f"Simulation completed with seed {seed}")
    print(f"3D viewer: {output / 'viewer.html'}")
    print(f"Metrics: {output / 'metrics.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
