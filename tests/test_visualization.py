"""Test functions of the visualization package."""

import matplotlib.pyplot as plt
import pandas as pd
import pytest

# pylint: disable=W0611
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 unused import

import weldx.transformations as tf
import weldx.visualization as vs

# pylint: enable=W0611


def test_plot_coordinate_system():
    """Test executing all possible code paths."""
    lcs_constant = tf.LocalCoordinateSystem()

    time = pd.TimedeltaIndex([10, 11, 12], "s")
    orientation_tdp = [
        [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
        [[0, 1, 0], [-1, 0, 0], [0, 0, 1]],
        [[-1, 0, 0], [0, -1, 0], [0, 0, 1]],
    ]
    coordinates_tdp = [[0, 0, 1], [0, 0, 2], [0, -1, 0]]
    lcs_tdp = tf.LocalCoordinateSystem(
        orientation=orientation_tdp, coordinates=coordinates_tdp, time=time
    )

    fig = plt.figure()
    ax = fig.gca(projection="3d")

    vs.plot_coordinate_system(lcs_constant, ax, "g")
    vs.plot_coordinate_system(lcs_tdp, ax, "r", "2016-01-10")
    vs.plot_coordinate_system(lcs_tdp, ax, "b", "2016-01-11", time_idx=1)
    vs.plot_coordinate_system(lcs_tdp, ax, "y", "2016-01-12", pd.TimedeltaIndex([12]))

    # exceptions ------------------------------------------

    # label without color
    with pytest.raises(Exception):
        vs.plot_coordinate_system(lcs_constant, ax, label="label")


def test_set_axes_equal():
    """Test executing all possible code paths."""
    fig = plt.figure()
    ax = fig.gca(projection="3d")
    vs.set_axes_equal(ax)
