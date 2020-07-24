"""Tests asdf implementations of core module."""

from io import BytesIO

import asdf
import numpy as np
import pandas as pd
import pytest
import xarray as xr
from jsonschema.exceptions import ValidationError

import weldx.transformations as tf
from weldx.asdf.extension import WeldxAsdfExtension, WeldxExtension
from weldx.asdf.utils import _write_read_buffer
from weldx.constants import WELDX_QUANTITY as Q_

# xarray.DataArray ---------------------------------------------------------------------

buffer_data_array = BytesIO()


def get_xarray_example_data_array():
    """
    Get an xarray.DataArray for test purposes.

    Returns
    -------
    xarray.DataArray
        DataArray for test purposes

    """
    data = np.array([[0, 1], [2, 3]])

    time_labels = ["2020-05-01", "2020-05-03"]
    d1 = np.array([-1, 1])
    d2 = pd.DatetimeIndex(time_labels)
    coords = {"d1": d1, "d2": d2, "time_labels": (["d2"], time_labels)}

    dax = xr.DataArray(data=data, dims=["d1", "d2"], coords=coords)

    dax.attrs = {"answer": 42}

    return dax


def test_xarray_data_array_save():
    """Test if an xarray.DataArray can be written to an asdf file."""
    dax = get_xarray_example_data_array()
    tree = {"dax": dax}
    with asdf.AsdfFile(tree, extensions=[WeldxExtension(), WeldxAsdfExtension()]) as f:
        f.write_to(buffer_data_array)
        buffer_data_array.seek(0)


def test_xarray_data_array_load():
    """Test if an xarray.DataArray can be restored from an asdf file."""
    f = asdf.open(
        buffer_data_array, extensions=[WeldxExtension(), WeldxAsdfExtension()]
    )
    dax_file = f.tree["dax"]
    dax_exp = get_xarray_example_data_array()
    assert dax_exp.identical(dax_file)


# xarray.DataArray ---------------------------------------------------------------------


buffer_dataset = BytesIO()


def get_xarray_example_dataset():
    """
    Get an xarray.Dataset for test purposes.

    Returns
    -------
        Dataset for test purposes
    """

    temp_data = [
        [[15.0, 16.0, 17.0], [18.0, 19.0, 20.0]],
        [[21.0, 22.0, 23.0], [24.0, 25.0, 26.0]],
    ]
    temp = Q_(temp_data, "°C")
    precipitation = [
        [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]],
        [[7.0, 8.0, 9.0], [10.0, 11.0, 12.0]],
    ]
    lon = [[-99.83, -99.32], [-99.79, -99.23]]
    lat = [[42.25, 42.21], [42.63, 42.59]]

    dsx = xr.Dataset(
        {
            "temperature": (["x", "y", "time"], temp),
            "precipitation": (["x", "y", "time"], precipitation),
        },
        coords={
            "lon": (["x", "y"], lon),
            "lat": (["x", "y"], lat),
            "time": pd.date_range("2014-09-06", periods=3),
            "time_labels": (["time"], ["2014-09-06", "2014-09-09", "2014-09-12"]),
            "reference_time": pd.Timestamp("2014-09-05"),
        },
    )
    dsx.attrs = {"temperature": "Celsius"}
    return dsx


def test_xarray_dataset_save():
    """Test if an xarray.DataSet can be written to an asdf file."""
    dsx = get_xarray_example_dataset()
    tree = {"dsx": dsx}
    with asdf.AsdfFile(tree, extensions=[WeldxExtension(), WeldxAsdfExtension()]) as f:
        f.write_to(buffer_dataset)
        buffer_dataset.seek(0)


def test_xarray_dataset_load():
    """Test if an xarray.Dataset can be restored from an asdf file."""
    f = asdf.open(buffer_dataset, extensions=[WeldxExtension(), WeldxAsdfExtension()])
    dsx_file = f.tree["dsx"]
    dsx_exp = get_xarray_example_dataset()
    assert dsx_exp.identical(dsx_file)


# weldx.transformations.LocalCoordinateSystem ------------------------------------------

buffer_lcs = BytesIO()


def get_local_coordinate_system(time_dep_orientation: bool, time_dep_coordinates: bool):
    """
    Get a local coordinate system.

    Parameters
    ----------
    time_dep_orientation :
        If True, the coordinate system has a time dependent orientation.
    time_dep_coordinates :
        If True, the coordinate system has a time dependent coordinates.

    Returns
    -------
    weldx.transformations.LocalCoordinateSystem:
        A local coordinate system

    """
    if not time_dep_coordinates:
        coords = Q_(np.asarray([2.0, 5.0, 1.0]), "mm")
    else:
        coords = Q_(
            np.asarray(
                [[2.0, 5.0, 1.0], [1.0, -4.0, 1.2], [0.3, 4.4, 4.2], [1.1, 2.3, 0.2]]
            ),
            "mm",
        )

    if not time_dep_orientation:
        orientation = tf.rotation_matrix_z(np.pi / 3)
    else:
        orientation = tf.rotation_matrix_z(np.pi / 2 * np.array([1, 2, 3, 4]))

    if not time_dep_orientation and not time_dep_coordinates:
        return tf.LocalCoordinateSystem(orientation=orientation, coordinates=coords)

    time = pd.DatetimeIndex(["2000-01-01", "2000-01-02", "2000-01-03", "2000-01-04"])
    return tf.LocalCoordinateSystem(
        orientation=orientation, coordinates=coords, time=time
    )


@pytest.mark.parametrize("time_dep_orientation", [False, True])
@pytest.mark.parametrize("time_dep_coordinates", [False, True])
def test_local_coordinate_system(time_dep_orientation, time_dep_coordinates):
    """Test (de)serialization of LocalCoordinateSystem in ASDF."""
    lcs = get_local_coordinate_system(time_dep_orientation, time_dep_coordinates)
    data = _write_read_buffer({"lcs": lcs})
    assert data["lcs"] == lcs


def test_local_coordinate_system_shape_violation():
    """Test if the shape validators work as expected."""
    # coordinates have wrong shape ------------------------
    orientation = xr.DataArray(
        data=[[1, 2, 3], [4, 5, 6], [7, 8, 9]],
        dims=["u", "v"],
        coords={"u": ["x", "y", "z"], "v": [0, 1, 2]},
    )
    coordinates = xr.DataArray(data=[1, 2], dims=["c"], coords={"c": ["x", "y"]},)
    lcs = tf.LocalCoordinateSystem(
        orientation=orientation, coordinates=coordinates, construction_checks=False
    )

    with pytest.raises(ValidationError):
        buff = BytesIO()
        with asdf.AsdfFile(
            {"lcs": lcs}, extensions=[WeldxExtension(), WeldxAsdfExtension()],
        ) as f:
            f.write_to(buff)

    # orientations have wrong shape -----------------------
    orientation = xr.DataArray(
        data=[[1, 2], [3, 4]], dims=["c", "v"], coords={"c": ["x", "y"], "v": [0, 1]},
    )
    coordinates = xr.DataArray(
        data=[1, 2, 3], dims=["u"], coords={"u": ["x", "y", "z"]},
    )
    lcs = tf.LocalCoordinateSystem(
        orientation=orientation, coordinates=coordinates, construction_checks=False
    )

    with pytest.raises(ValidationError):
        buff = BytesIO()
        with asdf.AsdfFile(
            {"lcs": lcs}, extensions=[WeldxExtension(), WeldxAsdfExtension()]
        ) as f:
            f.write_to(buff)


# weldx.transformations.CoordinateSystemManager ----------------------------------------

buffer_csm = BytesIO()


def are_coordinate_system_managers_equal(
    csm_0: tf.CoordinateSystemManager, csm_1: tf.CoordinateSystemManager
):
    """
    Test if two CoordinateSystemManager instances are equal.

    Parameters
    ----------
    csm_0:
        First CoordinateSystemManager instance.
    csm_1:
        Second CoordinateSystemManager instance.

    Returns
    -------
    bool:
        True if both coordinate system managers are identical, False otherwise
    """
    graph_0 = csm_0.graph
    graph_1 = csm_1.graph

    if len(graph_0.nodes) != len(graph_1.nodes):
        return False
    if len(graph_0.edges) != len(graph_1.edges):
        return False

    # check nodes
    for node in graph_0.nodes:
        if node not in graph_1.nodes:
            return False

    # check edges
    for edge in graph_0.edges:
        if edge not in graph_1.edges:
            return False

    # check coordinate systems
    for edge in graph_0.edges:
        lcs_0 = csm_0.get_local_coordinate_system(edge[0], edge[1])
        lcs_1 = csm_1.get_local_coordinate_system(edge[0], edge[1])
        if not (lcs_0 == lcs_1):
            return False

    return True


def get_example_coordinate_system_manager():
    """Get a consistent CoordinateSystemManager instance for test purposes."""
    csm = tf.CoordinateSystemManager("root")
    csm.create_cs("lcs_01", "root", coordinates=[1, 2, 3])
    csm.create_cs(
        "lcs_02",
        "root",
        orientation=tf.rotation_matrix_z(np.pi / 3),
        coordinates=[4, -7, 8],
    )
    csm.create_cs(
        "lcs_03",
        "lcs_02",
        orientation=tf.rotation_matrix_y(np.pi / 11),
        coordinates=[4, -7, 8],
    )
    return csm


def test_coordinate_system_manager_save():
    """Test if a CoordinateSystemManager can be written to an asdf file."""
    csm = get_example_coordinate_system_manager()
    tree = {"cs_hierarchy": csm}
    with asdf.AsdfFile(
        tree, extensions=[WeldxExtension(), WeldxAsdfExtension()], copy_arrays=True
    ) as f:
        f.write_to(buffer_csm)
        buffer_csm.seek(0)


def test_coordinate_system_manager_load():
    """Test if a CoordinateSystemManager can be read from an asdf file."""
    f = asdf.open(buffer_csm, extensions=[WeldxExtension(), WeldxAsdfExtension()])
    csm_exp = get_example_coordinate_system_manager()
    csm_file = f.tree["cs_hierarchy"]

    assert are_coordinate_system_managers_equal(csm_exp, csm_file)
