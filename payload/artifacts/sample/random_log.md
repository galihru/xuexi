# Random Numerical Run Log

- UTC generation time: `2026-07-26T03:00:54.623243+00:00`
- Seed: `250217655`
- Mode: `mixed`
- Tubes: `48`
- Voxel resolution: `40^3`

## Main numerical observations

- Voxelized union volume: `0.3632048438`
- Voxelized shaded union volume: `0.2248686563`
- Median multiplicity: `1.000000`
- Maximum multiplicity: `14`
- Sampled Katz-Tao convex Wolff constant: `1.00000000`
- Sampled Frostman slab Wolff constant: `0.17492552`
- Worst rectangular-prism hypothesis ratio: `0.00100800`
- Coarse group count: `25`
- Grain width c: `1.00000000`

## First random tubes

| Tube | Group | Center | Direction | Shading interval |
|---:|---:|---|---|---|
| 0 | 0 | (0.00457, -0.10952, -0.08172) | (0.42277, 0.80734, 0.41167) | [0.22225, 0.94225] |
| 1 | 1 | (0.06313, 0.04641, -0.12227) | (-0.99966, -0.01851, 0.01831) | [0.12573, 0.84573] |
| 2 | 2 | (-0.03474, 0.04042, 0.10095) | (-0.66295, 0.73941, 0.11734) | [0.19050, 0.91050] |
| 3 | 3 | (-0.06619, -0.03321, 0.04345) | (-0.48057, 0.43353, 0.76230) | [0.03263, 0.75263] |
| 4 | 4 | (0.00906, -0.01028, -0.09414) | (0.64796, -0.27693, 0.70955) | [0.22880, 0.94880] |
| 5 | 5 | (0.05037, 0.05410, -0.18806) | (-0.30539, 0.08950, 0.94801) | [0.06736, 0.78736] |
| 6 | 6 | (-0.11169, 0.04879, -0.04529) | (-0.74896, -0.60551, 0.26909) | [0.20949, 0.92949] |
| 7 | 7 | (0.15563, -0.00268, -0.14193) | (-0.77003, 0.18078, 0.61187) | [0.24698, 0.96698] |
| 8 | 8 | (-0.03336, -0.00145, -0.00886) | (0.74423, -0.41471, 0.52358) | [0.24954, 0.96954] |
| 9 | 9 | (-0.00010, 0.08611, 0.15486) | (-0.43699, 0.78315, 0.44240) | [0.01416, 0.73416] |
| 10 | 10 | (0.07376, -0.10508, 0.09511) | (0.16178, -0.81326, 0.55896) | [0.20791, 0.92791] |
| 11 | 11 | (0.07176, -0.06873, -0.07409) | (-0.24771, 0.63087, 0.73528) | [0.17439, 0.89439] |

## Formula diagnostics

These checks are finite-resolution numerical diagnostics, not proofs of asymptotic theorems.

| Equation | Status | Observed | Reference | Ratio | Result |
|---|---|---:|---:|---:|---|
| 1.1 | executable diagnostic | 0.22486866 | 0.057406627 | 3.9171202 | PASS |
| 1.2 | executable diagnostic | 0.22486866 | 0.0066768279 | 33.678965 | PASS |
| 1.3 | executable diagnostic | 0.22486866 | 0.015964069 | 14.085924 | PASS |
| 1.4 | executable diagnostic | 0.22486866 | 0.057406627 | 3.9171202 | PASS |
| 1.5 | executable diagnostic | 0.22486866 | 0.20116212 | 1.1178479 | PASS |
| 1.6 | executable diagnostic | 1 | 4.9711147 | 4.9711147 | PASS |
| 1.7/1.12 | executable diagnostic | 0.59649123 | 0.65172349 | 0.915252 | FAIL |
| 1.9 | executable diagnostic | 1 | 0.79909699 | 0.79909699 | FAIL |
| 1.10 | identity diagnostic | 1 | 1 | 1 | PASS |
| 1.11 | executable diagnostic | 1 | 2.2973967 | 2.2973967 | PASS |
| 4.1 | executable | 1 | 1 | 1 | PASS |
| 4.2 | executable | 0.17492552 | 0.17492552 | 1 | PASS |
| 4.5 | diagnostic | 5 |  |  | N/A |
| 7.2 | executable diagnostic | 1 | 1.86339 | 0.53665631 | FAIL |
| 7.3/7.4 | executable diagnostic | 0.5 | 0.5 | 1 | PASS |
| 7.3/7.4 | executable diagnostic | 1 | 1 | 1 | PASS |
| 7.3/7.4 | executable diagnostic | 1 | 1 | 1 | PASS |
| 7.3/7.4 | executable diagnostic | 1 | 1 | 1 | PASS |
| 12.1 | executable diagnostic | 0.95026542 | 2.0706722 | 2.1790461 | PASS |
