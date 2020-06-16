"""Tests asdf implementations of core module."""

import asdf
import numpy as np
import pandas as pd
import xarray as xr
from io import BytesIO

import weldx.transformations as tf
from weldx.asdf.extension import WeldxExtension, WeldxAsdfExtension


# xarray.DataArray ---------------------------------------------------------------------

buffer_data_array = BytesIO()


def get_xarray_example_data_array():
    """Get an xarray.DataArray for test purposes."""
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
    """Get an xarray.Dataset for test purposes."""

    temp = [
        [[15.0, 16.0, 17.0], [18.0, 19.0, 20.0]],
        [[21.0, 22.0, 23.0], [24.0, 25.0, 26.0]],
    ]
    precip = [[[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]], [[7.0, 8.0, 9.0], [10.0, 11.0, 12.0]]]
    lon = [[-99.83, -99.32], [-99.79, -99.23]]
    lat = [[42.25, 42.21], [42.63, 42.59]]

    dsx = xr.Dataset(
        {
            "temperature": (["x", "y", "time"], temp),
            "precipitation": (["x", "y", "time"], precip),
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


# TODO: remove
# test_xarray_dataset_save()


def test_xarray_dataset_load():
    """Test if an xarray.Dataset can be restored from an asdf file."""
    f = asdf.open(buffer_dataset, extensions=[WeldxExtension(), WeldxAsdfExtension()])
    dsx_file = f.tree["dsx"]
    dsx_exp = get_xarray_example_dataset()
    assert dsx_exp.identical(dsx_file)


# TODO: remove
# test_xarray_dataset_load()

# weldx.transformations.LocalCoordinateSystem ------------------------------------------

buffer_lcs = BytesIO()


def get_local_coordinate_system(time_dep_orientation, time_dep_coordinates):
    coords = [2, 5, 1]
    orientation = tf.rotation_matrix_z(np.pi / 3)

    if not time_dep_orientation and not time_dep_coordinates:
        return tf.LocalCoordinateSystem(orientation=orientation, coordinates=coords)
    raise Exception("not implemented")


def are_local_coordinate_systems_equal(
    lcs_0: tf.LocalCoordinateSystem, lcs_1: tf.LocalCoordinateSystem
):
    return lcs_0.orientation.identical(
        lcs_1.orientation
    ) and lcs_0.coordinates.identical(lcs_1.coordinates)


def test_local_coordinate_system_save():
    """Test if a LocalCoordinateSystem can be writen to an asdf file."""
    lcs_static = get_local_coordinate_system(False, False)
    tree = {"lcs_static": lcs_static}
    with asdf.AsdfFile(
        tree, extensions=[WeldxExtension(), WeldxAsdfExtension()], copy_arrays=True
    ) as f:
        f.write_to(buffer_lcs)
        buffer_lcs.seek(0)


# TODO: remove
# test_local_coordinate_system_save()


def test_local_coordinate_system_load():
    """Test if an xarray.DataArray can be restored from an asdf file."""
    f = asdf.open(buffer_lcs, extensions=[WeldxExtension(), WeldxAsdfExtension()],)
    lcs_static_file = f.tree["lcs_static"]
    lcs_static_exp = get_local_coordinate_system(False, False)

    assert are_local_coordinate_systems_equal(lcs_static_file, lcs_static_exp)


# TODO: remove
# test_local_coordinate_system_load()
