import numpy as np

from kakeya_sim.geometry import Tube, point_segment_distance_squared


def test_point_segment_distance() -> None:
    points = np.array([[0.0, 1.0, 0.0], [0.0, 0.0, 0.0]])
    d2, t = point_segment_distance_squared(points, np.array([-0.5, 0.0, 0.0]), np.array([0.5, 0.0, 0.0]))
    assert np.allclose(d2, [1.0, 0.0])
    assert np.allclose(t, [0.5, 0.5])


def test_tube_contains() -> None:
    tube = Tube(np.zeros(3), np.array([1.0, 0.0, 0.0]), 0.1)
    points = np.array([[0.0, 0.05, 0.0], [0.0, 0.2, 0.0]])
    assert tube.contains(points).tolist() == [True, False]
