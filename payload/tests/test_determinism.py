import numpy as np

from kakeya_sim.generator import generate_tubes


def test_generation_is_deterministic() -> None:
    a = generate_tubes("sticky", 12345, 12, 0.04, 0.2, 0.7)
    b = generate_tubes("sticky", 12345, 12, 0.04, 0.2, 0.7)
    assert all(np.allclose(x.center, y.center) and np.allclose(x.direction, y.direction) for x, y in zip(a, b))
