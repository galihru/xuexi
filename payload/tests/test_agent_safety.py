import pytest

from xuexi_agent.safety import validate_proposal


WRITABLE = {"src/xuexi_agent/generated/strategy.py"}
ALLOWED = {"math", "dataclasses", "typing", "numpy"}


def test_safe_generated_module_is_accepted() -> None:
    proposal = {
        "files": [
            {
                "path": "src/xuexi_agent/generated/strategy.py",
                "content": "from __future__ import annotations\nimport math\ndef mutate_parameters(p, c):\n    return dict(p)\n",
            }
        ]
    }
    files = validate_proposal(proposal, WRITABLE, ALLOWED, 10000)
    assert files[0][0].endswith("strategy.py")


def test_dangerous_import_is_rejected() -> None:
    proposal = {
        "files": [
            {
                "path": "src/xuexi_agent/generated/strategy.py",
                "content": "import os\ndef mutate_parameters(p, c):\n    os.system('x')\n    return p\n",
            }
        ]
    }
    with pytest.raises(ValueError):
        validate_proposal(proposal, WRITABLE, ALLOWED, 10000)


def test_path_traversal_is_rejected() -> None:
    proposal = {"files": [{"path": "../workflow.yml", "content": "x"}]}
    with pytest.raises(ValueError):
        validate_proposal(proposal, WRITABLE, ALLOWED, 10000)
