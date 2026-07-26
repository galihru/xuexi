# Kakeya Set Conjecture 3D Numerical Companion

本项目是 Wang 与 Zahl 论文 **“Volume estimates for unions of convex sets, and the Kakeya set conjecture in three dimensions”** 的三维数值实验伴随项目。

程序在 `R^3` 中随机生成 `δ`-管族，利用体素离散方法估计管族并集体积、遮影并集体积、交叠重数、Katz–Tao Convex Wolff 常数、Frostman Slab Wolff 常数、多尺度分组、广性以及管倍增比，并生成可交互的三维 HTML 可视化结果。

> 本项目是有限分辨率的数值模型，不是论文证明的替代品。论文中的许多结论属于渐近估计、存在性定理或归纳论证，不能被有限数值实验直接证明。

## 主要功能

- 生成均匀、黏性、非黏性、hairbrush、grains 和混合型 `δ`-管排列；
- 把单位线段的 `δ`-邻域建模为三维胶囊体；
- 使用体素网格近似并集体积与典型交叠重数；
- 数值评估论文中的主要公式 `(1.1)`–`(1.14)`、Wolff 常数 `(4.1)`–`(4.2)`、grains 尺度关系和 tube doubling `(12.1)`；
- 为论文中全部编号公式建立追踪表，区分“可执行”“数值诊断”和“证明内部步骤”；
- 生成 `viewer.html`、`metrics.json`、`formula_checks.csv`、`wolff_probes.csv`、`tubes.csv` 和随机运行记录；
- 可通过 GitHub Actions 运行，并由 Xuexi GitHub App 提交生成结果。

## 快速运行

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
python -m kakeya_sim \
  --mode mixed \
  --seed 250217655 \
  --tubes 64 \
  --delta 0.055 \
  --rho 0.24 \
  --resolution 52 \
  --output artifacts/latest
```

打开：

```text
artifacts/latest/viewer.html
```

## 输出文件

```text
artifacts/latest/
├── viewer.html
├── metrics.json
├── tubes.csv
├── wolff_probes.csv
├── formula_checks.csv
└── random_log.md
```

## 数学说明

详细推导见 [`docs/MATHEMATICAL_DERIVATION.md`](docs/MATHEMATICAL_DERIVATION.md)。公式覆盖范围见 [`docs/FORMULA_COVERAGE.md`](docs/FORMULA_COVERAGE.md)。

## 参考文献

Hong Wang and Joshua Zahl, *Volume estimates for unions of convex sets, and the Kakeya set conjecture in three dimensions*, arXiv:2502.17655v1, 2025.

## 许可

本仓库中的源代码采用 MIT License。论文内容与证明归原作者所有。
