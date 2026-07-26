from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_public_pages_use_simplified_chinese() -> None:
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    assert "学习" in readme
    assert "```mermaid" in readme
    assert "自主研究代理" in readme


def test_site_template_declares_chinese() -> None:
    source = (PROJECT_ROOT / "src/kakeya_sim/site.py").read_text(encoding="utf-8")
    assert '<html lang="zh-CN">' in source
