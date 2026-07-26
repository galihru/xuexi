import math
import numpy as np

from kakeya_sim.geometry import Tube


def test_capsule_volume_exceeds_paper_scale() -> None:
    tube = Tube(np.zeros(3), np.array([1.0, 0.0, 0.0]), 0.05)
    assert tube.capsule_volume > tube.paper_volume
    assert math.isclose(tube.paper_volume, 0.0025)
