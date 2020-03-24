"""Contains package internal utility functions."""

import math
import numpy as np
import xarray as xr


def is_column_in_matrix(column, matrix):
    """
    Check if a column (1d array) can be found inside of a matrix.

    :param column: Column that should be checked
    :param matrix: Matrix
    :return: True or False
    """
    return is_row_in_matrix(column, np.transpose(matrix))


def is_row_in_matrix(row, matrix):
    """
    Check if a row (1d array) can be found inside of a matrix.

    source: https://codereview.stackexchange.com/questions/193835

    :param row: Row that should be checked
    :param matrix: Matrix
    :return: True or False
    """
    if not matrix.shape[1] == np.array(row).size:
        return False
    # noinspection PyUnresolvedReferences
    return (matrix == row).all(axis=1).any()


def to_float_array(container):
    """
    Cast the passed container to a numpy array of floats.

    :param container: Container which can be cast to a numpy array
    :return:
    """
    return np.array(container, dtype=float)


def to_list(var):
    """
    Store the passed variable into a list and return it.

    If the variable is already a list, it is returned without modification.
    If 'None' is passed, the function returns an empty list.

    :param var: Arbitrary variable
    :return: List
    """
    if isinstance(var, list):
        return var
    if var is None:
        return []
    return [var]


def matrix_is_close(mat_a, mat_b, abs_tol=1e-9):
    """
    Check if a matrix is close or equal to another matrix.

    :param mat_a: First matrix
    :param mat_b: Second matrix
    :param abs_tol: Absolute tolerance
    :return: True or False
    """
    mat_a = to_float_array(mat_a)
    mat_b = to_float_array(mat_b)

    if not mat_a.shape == mat_b.shape:
        return False
    for i in range(mat_a.shape[0]):
        for j in range(mat_a.shape[1]):
            if not math.isclose(mat_a[i, j], mat_b[i, j], abs_tol=abs_tol):
                return False
    return True


def vector_is_close(vec_a, vec_b, abs_tol=1e-9):
    """
    Check if a vector is close or equal to another vector.

    :param vec_a: First vector
    :param vec_b: Second vector
    :param abs_tol: Absolute tolerance
    :return: True or False
    """
    vec_a = to_float_array(vec_a)
    vec_b = to_float_array(vec_b)

    if not vec_a.size == vec_b.size:
        return False
    for i in range(vec_a.size):
        if not math.isclose(vec_a[i], vec_b[i], abs_tol=abs_tol):
            return False

    return True


def mat_vec_mul(a, b):
    """
    Matrix x Vector multiplication using matmul with newaxis for correct broadcasting.

    :param a: Input Matrix [m, n]
    :param b: Input Vector to be multiplied [n, ]
    :return: Resulting vector [n, ]
    """
    return np.matmul(a, b[..., np.newaxis]).squeeze()


def transpose_xarray_axis_data(da, dim1, dim2):
    """
    Transpose data along two dimensions in an xarray.DataArray.

    :param da: xarray.DataArray to transpose
    :param dim1: name of the first dimension
    :param dim2: name of the second dimension
    :return: xarray.DataArray with transposed data at specified dimensions
    """
    dims = list(da.dims)
    i = dims.copy()
    a, b = i.index(dim1), i.index(dim2)
    i[b], i[a] = i[a], i[b]

    da.data = da.transpose(*i).data
    return da


def xr_matvecmul(a, vec, dims_a, dims_v=None, **apply_kwargs):
    """
    Broadcast Matrix * Vector operations on xarray objects.

    :param a: xarray object containing the matrix
    :param vec: xarray object containing the vector
    :param dims_a: dimension names spanning the matrix in a
    :param dims_v: vector dimension of vec (if None, use dims_a[0])
    :param: **apply_kwargs: parameters to pass on to xr.apply_ufunc
    :return: broadcasted result of np.matmul(a,vec)
    """
    return xr.apply_ufunc(
        mat_vec_mul, a, vec, input_core_dims=[dims_a, dims_v], output_core_dims=[dims_v]
    )


def xr_matmul(a, b, dims_a, dims_b=None, dims_out=None, **apply_kwargs):
    """
    Calculate broadcasted np.matmul(a,b) for xarray objects.

    Should work for any size and shape of quadratic matrixes contained in a DataArray.
    Ordering, broadcasting of dimensions should be taken care of by xarray internally.
    :param a: xarray object containing the first matrix
    :param b: xarray object containing the second matrix
    :param dims_a: name and order of dimensions in the first object
    :param dims_b: name and order of dimensions in the second object
                    (if None, use dims_a)
    :param dims_out: name and order of dimensions in the resulting object
                    (if None, use dims_a)
    :param: **apply_kwargs: parameters to pass on to xr.apply_ufunc
    :return:
    """
    if dims_b is None:
        dims_b = dims_a
    if dims_out is None:
        dims_out = dims_a

    return xr.apply_ufunc(
        np.matmul,
        a,
        b,
        input_core_dims=[dims_a, dims_b],
        output_core_dims=[dims_out],
        **apply_kwargs
    )


def xr_matmul_transpose(a, b, dims):
    """
    Calculate a * b.T for xarray.DataArray objects by applying np.matmul.

    Should work for any size and shape of quadratic matrixes contained in a DataArray.
    Ordering, broadcasting of dimensions should be taken care of by xarray internally.
    :param a: xarray object containing the first matrix
    :param b: xarray object containing the second matrix that will be transposed
    :param dims: dimensions in the non-transposed order. Must exist in both objects
    :return:
    """
    return xr_matmul(a, b, dims_a=dims, dims_b=reversed(dims))


def xr_is_orthogonal_matrix(da, dims):
    """
    Check if  matrix along specific dimensions in a DataArray is orthogonal.

    TODO: make more general

    :param da: xarray.DataArray to test
    :param dims: list of dimensions along which to test
    :return: True if all matrixes are orthogonal.
    """
    eye = np.eye(len(da.coords[dims[0]]), len(da.coords[dims[1]]))
    return np.allclose(xr_matmul_transpose(da, da, dims), eye)
