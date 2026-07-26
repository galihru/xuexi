from pathlib import Path

from xuexi_agent.paper import extract_equations


def test_paper_contains_all_numbered_equations() -> None:
    records = extract_equations(Path("paper/2502.17655v1.pdf"))
    labels = {record.label for record in records}
    assert len(records) == 254
    assert {"1.1", "4.1", "7.15", "10.20", "12.7"} <= labels
