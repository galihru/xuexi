from __future__ import annotations

from html import escape
import json
from pathlib import Path
import shutil


def _format(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.7g}"
    return str(value)


def _load_json(path: Path, fallback: dict) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return fallback
    return value if isinstance(value, dict) else fallback


def build_site(artifact_dir: Path, site_dir: Path) -> None:
    site_dir.mkdir(parents=True, exist_ok=True)
    for path in artifact_dir.iterdir():
        if path.is_file():
            shutil.copy2(path, site_dir / path.name)

    metrics = _load_json(artifact_dir / "metrics.json", {})
    state = _load_json(Path("state/agent_state.json"), {})
    cycle = _load_json(Path("state/latest_cycle.json"), {})
    evaluation = _load_json(Path("state/latest_evaluation.json"), {})

    metadata = metrics.get("metadata", {})
    geometry = metrics.get("geometry", {})
    voxel = metrics.get("voxel", {})
    wolff = metrics.get("wolff", {})
    multiscale = metrics.get("multiscale", {})

    cards = [
        ("随机种子", metadata.get("seed", "—")),
        ("排列模式", metadata.get("mode", "—")),
        ("管数量", geometry.get("tube_count", "—")),
        ("并集体积", voxel.get("union_volume", "—")),
        ("着色并集体积", voxel.get("shaded_union_volume", "—")),
        ("平均重数", voxel.get("average_multiplicity", "—")),
        ("最大重数", voxel.get("maximum_multiplicity", "—")),
        ("Katz–Tao 估计", wolff.get("katz_tao_convex", "—")),
        ("Frostman 板估计", wolff.get("frostman_slab", "—")),
        ("粗尺度分组", multiscale.get("group_count", "—")),
        ("grain 宽度 c", multiscale.get("grain_c", "—")),
        ("代理周期", state.get("cycle", 0)),
        ("最近评估得分", evaluation.get("score", "—")),
        ("已审查公式", len(state.get("reviewed_equations", []))),
        ("已实现公式", len(state.get("implemented_equations", []))),
        ("本轮是否接受", "是" if cycle.get("accepted") else "否"),
    ]
    card_html = "\n".join(
        f'<article class="metric"><span>{escape(label)}</span><strong>{escape(_format(value))}</strong></article>'
        for label, value in cards
    )

    research_note = ""
    note_path = Path("docs/AI_RESEARCH_NOTE.md")
    if note_path.exists():
        shutil.copy2(note_path, site_dir / "AI_RESEARCH_NOTE.md")
        research_note = '<a href="AI_RESEARCH_NOTE.md">学习代理研究记录</a>'

    coverage_link = ""
    coverage_path = Path("docs/EQUATION_COVERAGE.md")
    if coverage_path.exists():
        shutil.copy2(coverage_path, site_dir / "EQUATION_COVERAGE.md")
        coverage_link = '<a href="EQUATION_COVERAGE.md">公式覆盖说明</a>'

    generated = escape(str(metadata.get("generated_at", "—")))
    model = escape(str(state.get("last_model", "尚未运行")))
    cycle_message = escape(str(cycle.get("message", "尚未完成代理周期。")))

    html = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>学习 · 三维 Kakeya 自主研究代理</title>
  <style>
    :root {{ color-scheme: dark; font-family: Inter, "Noto Sans SC", "Microsoft YaHei", system-ui, sans-serif; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; background: #07111f; color: #e8eef8; }}
    header {{ padding: 48px 6vw 32px; background: radial-gradient(circle at top right, #17335f, #07111f 62%); }}
    h1 {{ margin: 0; font-size: clamp(2rem, 5vw, 4.2rem); line-height: 1.05; }}
    .subtitle {{ max-width: 980px; color: #afbdd1; line-height: 1.8; }}
    .status {{ display: inline-flex; gap: 10px; align-items: center; padding: 9px 14px; border: 1px solid #31517c; border-radius: 999px; background: #0c1b30; color: #c9e1ff; }}
    .dot {{ width: 9px; height: 9px; border-radius: 50%; background: #55d68b; box-shadow: 0 0 16px #55d68b; }}
    main {{ width: min(1450px, 92vw); margin: 0 auto 70px; }}
    .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin: 24px 0; }}
    .metric {{ background: #0c1a2d; border: 1px solid #1f3555; border-radius: 15px; padding: 17px; }}
    .metric span {{ display: block; color: #91a6c2; font-size: .82rem; margin-bottom: 8px; }}
    .metric strong {{ font-size: 1.18rem; word-break: break-word; }}
    .panel {{ background: #0b1728; border: 1px solid #1f3555; border-radius: 18px; overflow: hidden; margin-top: 22px; box-shadow: 0 20px 70px rgba(0,0,0,.25); }}
    .panel h2 {{ margin: 0; padding: 18px 22px; border-bottom: 1px solid #1f3555; font-size: 1.05rem; }}
    .panel p {{ margin: 0; padding: 20px 22px; color: #b9c7da; line-height: 1.75; }}
    iframe {{ width: 100%; height: min(78vh, 850px); border: 0; background: white; }}
    video, .preview {{ display: block; width: 100%; max-height: 820px; object-fit: contain; background: #02060c; }}
    .links {{ display: flex; flex-wrap: wrap; gap: 10px; padding: 22px 0; }}
    .links a {{ color: #cfe4ff; border: 1px solid #31517c; background: #10233d; padding: 10px 13px; border-radius: 10px; text-decoration: none; }}
    footer {{ color: #8fa2bd; padding: 26px 0; line-height: 1.8; }}
    code {{ color: #b9d7ff; }}
  </style>
</head>
<body>
<header>
  <div class="status"><span class="dot"></span>本地模型驱动的有界自主研究循环</div>
  <h1>学习（Xuexi）<br>三维 Kakeya 研究代理</h1>
  <p class="subtitle">代理读取论文、建立 254 个编号公式的索引、检查现有代码、生成受限候选修改、运行测试与数值模拟、进行自我批评，并且只有在得分提高且全部验证通过时才接受修改。数值实验用于理解公式与几何结构，不替代论文中的严格证明。</p>
</header>
<main>
  <section class="metrics">{card_html}</section>

  <section class="panel">
    <h2>最近一次自主研究周期</h2>
    <p>{cycle_message}<br>本地模型：<code>{model}</code><br>最近渲染：<code>{generated}</code></p>
  </section>

  <section class="panel">
    <h2>交互式三维查看器</h2>
    <iframe src="viewer.html" title="三维 Kakeya 交互查看器"></iframe>
  </section>

  <section class="panel">
    <h2>旋转模拟视频</h2>
    <video controls autoplay muted loop playsinline poster="preview.png">
      <source src="rotation.mp4" type="video/mp4">
    </video>
  </section>

  <section class="panel">
    <h2>最新静态渲染</h2>
    <img class="preview" src="preview.png" alt="三维 Kakeya 数值模拟">
  </section>

  <nav class="links">
    <a href="metrics.json">数值指标 JSON</a>
    <a href="formula_checks.csv">公式检查 CSV</a>
    <a href="wolff_probes.csv">Wolff 探针 CSV</a>
    <a href="tubes.csv">管数据 CSV</a>
    <a href="random_log.md">随机实验记录</a>
    <a href="rotation.gif">GIF 动画</a>
    {research_note}
    {coverage_link}
  </nav>

  <footer>
    学习代理不会重新训练模型权重。它执行的是可审计的软件代理循环：读取、规划、生成候选、测试、批评、回退或接受、重新渲染和提交。所有自动生成内容都应由人类审阅。
  </footer>
</main>
</body>
</html>
"""
    (site_dir / "index.html").write_text(html, encoding="utf-8")
    (site_dir / "404.html").write_text(html, encoding="utf-8")
    (site_dir / ".nojekyll").write_text("", encoding="utf-8")
