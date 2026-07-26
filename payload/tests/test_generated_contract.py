from xuexi_agent.generated.equation_extensions import EQUATION_LABELS, evaluate
from xuexi_agent.generated.strategy import mutate_parameters, research_hypotheses


def test_generated_contracts() -> None:
    params = {"delta": 0.05, "rho": 0.2}
    assert isinstance(mutate_parameters(params, {}), dict)
    assert isinstance(research_hypotheses({}), list)
    assert isinstance(EQUATION_LABELS, list)
    assert isinstance(evaluate({}, params), list)
