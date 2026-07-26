# Formula Coverage and Traceability

The source paper contains 254 numbered equation labels. This repository does not claim that a finite voxel experiment proves every asymptotic statement. Instead, every numbered label is registered and assigned one of these statuses:

- **executable**: the mathematical quantity is computed directly;
- **executable diagnostic**: a finite-resolution analogue is compared numerically;
- **diagnostic**: a sampled proxy is computed;
- **proof-only trace**: the equation is an internal proof step, existential choice, refinement, dyadic pigeonholing statement, or asymptotic relation without a standalone numerical update law.

## Directly implemented families

| Formula family | Implementation |
|---|---|
| `(1.1)`–`(1.4)` | Union-volume lower-bound diagnostics |
| `(1.5)`–`(1.12)` | Multiplicity, fine/coarse decomposition, and local-density diagnostics |
| `(4.1)`–`(4.2)` | Sampled Katz–Tao and Frostman Wolff constants |
| `(4.3)`–`(4.5)` | Cover-inheritance and balanced-cover diagnostics |
| `(5.1)`–`(5.6)` | Flat-prism bound terms and neighbourhood concentration proxy |
| `(7.2)`–`(7.4)` | Grain scale and broadness diagnostics |
| `(9.1)` and `(10.1)` | Improved-union target diagnostics |
| `(12.1)` | Tube-doubling diagnostic |

The full registry is stored in [`data/equation_registry.csv`](../data/equation_registry.csv). Every simulation output contains `formula_checks.csv`, which includes every registered label and its implementation status.
