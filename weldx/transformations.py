"""Contains methods and classes for coordinate transformations."""

import weldx.utility as ut
import numpy as np
import xarray as xr
import math
import networkx as nx
from scipy.spatial.transform import Rotation as Rot


# functions -------------------------------------------------------------------


def rotation_matrix_x(angle):
    """
    Create a rotation matrix that rotates around the x-axis.

    :param angle: Rotation angle
    :return: Rotation matrix
    """
    return Rot.from_euler("x", angle).as_matrix()


def rotation_matrix_y(angle):
    """
    Create a rotation matrix that rotates around the y-axis.

    :param angle: Rotation angle
    :return: Rotation matrix
    """
    return Rot.from_euler("y", angle).as_matrix()


def rotation_matrix_z(angle):
    """
    Create a rotation matrix that rotates around the z-axis.

    :param angle: Rotation angle
    :return: Rotation matrix
    """
    return Rot.from_euler("z", angle).as_matrix()


def scale_matrix(scale_x, scale_y, scale_z):
    """
    Return a scaling matrix.

    :param scale_x: Scaling factor in x direction
    :param scale_y: Scaling factor in y direction
    :param scale_z: Scaling factor in z direction
    :return: Scaling matrix
    """
    return np.array([[scale_x, 0, 0], [0, scale_y, 0], [0, 0, scale_z]], dtype=float)


def normalize(vec):
    """
    Normalize a vector.

    :param vec: Vector
    :return: Normalized vector
    """
    norm = np.linalg.norm(vec, axis=(-1))
    if not np.all(norm):
        raise ValueError("Vector length is 0.")
    if vec.ndim > 1:
        return vec / norm[..., np.newaxis]
    return vec / norm


def orientation_point_plane_containing_origin(point, p_a, p_b):
    """
    Determine a points orientation relative to a plane containing the origin.

    The side is defined by the winding order of the triangle 'origin - A -
    B'. When looking at it from the left-hand side, the ordering is clockwise
    and counter-clockwise when looking from the right-hand side.

    The function returns 1 if the point lies left of the plane, -1 if it is
    on the right and 0 if it lies on the plane.

    Note, that this function is not appropriate to check if a point lies on
    a plane since it has no tolerance to compensate for numerical errors.

    Additional note: The points A and B can also been considered as two
    vectors spanning the plane.

    :param point: Point
    :param p_a: Second point of the triangle 'origin - A - B'.
    :param p_b: Third point of the triangle 'origin - A - B'.
    :return: 1, -1 or 0 (see description)
    """
    if (
        math.isclose(np.linalg.norm(p_a), 0)
        or math.isclose(np.linalg.norm(p_b), 0)
        or math.isclose(np.linalg.norm(p_b - p_a), 0)
    ):
        raise Exception("One or more points describing the plane are identical.")

    return np.sign(np.linalg.det([p_a, p_b, point]))


def orientation_point_plane(point, p_a, p_b, p_c):
    """
    Determine a points orientation relative to an arbitrary plane.

    The side is defined by the winding order of the triangle 'A - B - C'.
    When looking at it from the left-hand side, the ordering is clockwise
    and counter-clockwise when looking from the right-hand side.

    The function returns 1 if the point lies left of the plane, -1 if it is
    on the right and 0 if it lies on the plane.

    Note, that this function is not appropriate to check if a point lies on
    a plane since it has no tolerance to compensate for numerical errors.

    :param point: Point
    :param p_a: First point of the triangle 'A - B - C'.
    :param p_b: Second point of the triangle 'A - B - C'.
    :param p_c: Third point of the triangle 'A - B - C'.
    :return: 1, -1 or 0 (see description)
    """
    vec_a_b = p_b - p_a
    vec_a_c = p_c - p_a
    vec_a_point = point - p_a
    return orientation_point_plane_containing_origin(vec_a_point, vec_a_b, vec_a_c)


def is_orthogonal(vec_u, vec_v, tolerance=1e-9):
    """
    Check if vectors are orthogonal.

    :param vec_u: First vector
    :param vec_v: Second vector
    :param tolerance: Numerical tolerance
    :return: True or False
    """
    if math.isclose(np.dot(vec_u, vec_u), 0) or math.isclose(np.dot(vec_v, vec_v), 0):
        raise Exception("One or both vectors have zero length.")

    return math.isclose(np.dot(vec_u, vec_v), 0, abs_tol=tolerance)


def point_left_of_line(point, line_start, line_end):
    """
    Determine if a point lies left of a line.

    Returns 1 if the point is left of the line and -1 if it is to the right.
    If the point is located on the line, this function returns 0.

    :param point: Point
    :param line_start: Starting point of the line
    :param line_end: End point of the line
    :return: 1,-1 or 0 (see description)
    """
    vec_line_start_end = line_end - line_start
    vec_line_start_point = point - line_start
    return vector_points_to_left_of_vector(vec_line_start_point, vec_line_start_end)


def reflection_sign(matrix):
    """
    Get a sign indicating if the transformation is a reflection.

    Returns -1 if the transformation contains a reflection and 1 if not.

    :param matrix: Transformation matrix
    :return: 1 or -1 (see description)
    """
    sign = int(np.sign(np.linalg.det(matrix)))

    if sign == 0:
        raise Exception("Invalid transformation")

    return sign


def vector_points_to_left_of_vector(vector, vector_reference):
    """
    Determine if a vector points to the left of another vector.

    Returns 1 if the vector points to the left of the reference vector and
    -1 if it points to the right. In case both vectors point into the same
    or the opposite directions, this function returns 0.

    :param vector: Vector
    :param vector_reference: Reference vector
    :return: 1,-1 or 0 (see description)
    """
    return int(np.sign(np.linalg.det([vector_reference, vector])))


# local coordinate system class --------------------------------------------------------


class LocalCoordinateSystem:
    """Defines a local cartesian coordinate system in 3d."""

    def __init__(
        self,
        basis=np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]]),
        origin=np.array([0, 0, 0]),
    ):
        """
        Construct a cartesian coordinate system.

        :param basis: Matrix of 3 orthogonal column vectors which represent
        the coordinate systems basis. Keep in mind, that the columns of the
        corresponding orientation matrix is equal to the normalized basis
        vectors. So each orthogonal transformation matrix can also be
        provided as basis.
        :param origin: Position of the origin
        :return: Cartesian coordinate system
        """
        if not isinstance(basis, xr.DataArray):
            basis = xr.DataArray(
                data=basis,
                dims=["c", "v"],
                coords={"c": ["x", "y", "z"], "v": [0, 1, 2]},
                name="basis",
            )
            basis = basis.astype(float)

        if not isinstance(origin, xr.DataArray):
            origin = xr.DataArray(
                data=origin, dims=["c"], coords={"c": ["x", "y", "z"]}, name=origin
            )
            origin = origin.astype(float)

        basis = xr.apply_ufunc(
            normalize,
            basis,
            input_core_dims=[["c", "v"]],
            output_core_dims=[["c", "v"]],
        )

        # vectorize test if orthogonal
        if not ut.xr_is_orthogonal_matrix(basis, dims=["c", "v"]):
            raise Exception("Basis vectors must be orthogonal")

        self._xarray = xr.Dataset({"basis": basis, "origin": origin})

    def __repr__(self):
        """Give __repr_ output in xarray format."""
        return self.xarray.__repr__().replace(
            "<xarray.Dataset>", "<LocalCoordinateSystem>"
        )

    def __add__(self, rhs_cs):
        """
        Add 2 coordinate systems.

        Generates a new coordinate system by treating the left-hand side
        coordinate system as being defined in the right hand-side coordinate
        system.
        The transformations from the base coordinate system to the new
        coordinate system are equivalent to the combination of the
        transformations from both added coordinate systems:

        R_n = R_r * R_l
        T_n = R_r * T_l + T_r

        R_r and T_r are rotation matrix and translation vector of the
        right-hand side coordinate system, R_l and T_l of the left-hand side
        coordinate system and R_n and T_n of the resulting coordinate system.

        :param rhs_cs: Right-hand side coordinate system
        :return: Resulting coordinate system.
        """
        basis = ut.xr_matmul(rhs_cs.basis, self.basis, dims_a=["c", "v"])
        origin = (
            ut.xr_matvecmul(rhs_cs.basis, self.origin, ["c", "v"], ["c"])
            + rhs_cs.origin
        )
        return LocalCoordinateSystem(basis, origin)

    def __sub__(self, rhs_cs):
        """
        Subtract 2 coordinate systems.

        Generates a new coordinate system from two local coordinate systems
        with the same reference coordinate system. The resulting system is
        equivalent to the left-hand side system but with the right-hand side
        as reference coordinate system.
        This is achieved by the following transformations:

        R_n = R_r^(-1) * R_l
        T_n = R_r^(-1) * (T_l - T_r)

        R_r and T_r are rotation matrix and translation vector of the
        right-hand side coordinate system, R_l and T_l of the left-hand side
        coordinate system and R_n and T_n of the resulting coordinate system.

        :param rhs_cs: Right-hand side coordinate system
        :return: Resulting coordinate system.
        """
        basis = ut.xr_matmul(
            rhs_cs.basis,
            self.basis,
            dims_a=["v", "c"],  # transposed !
            dims_b=["c", "v"],
            dims_out=["c", "v"],
        )

        origin = xr.apply_ufunc(
            ut.mat_vec_mul,
            rhs_cs.basis,
            self.origin - rhs_cs.origin,
            input_core_dims=[["v", "c"], ["c"]],  # transposed !
            output_core_dims=[["c"]],
        )
        return LocalCoordinateSystem(basis, origin)

    @classmethod
    def construct_from_euler(cls, sequence, angles, degrees=False, origin=None):
        """
        Construct a cartesian coordinate system from an euler sequence.

        This function uses scipy.spatial.transform.Rotation.from_euler method to define
        the coordinate systems orientation. Take a look at it's documentation, if some
        information is missing here. The related parameter docs are a copy of the scipy
        documentation.
        :param sequence: Specifies sequence of axes for rotations. Up to 3 characters
        belonging to the set {‘X’, ‘Y’, ‘Z’} for intrinsic rotations, or {‘x’, ‘y’, ‘z’}
        for extrinsic rotations. Extrinsic and intrinsic rotations cannot be mixed in
        one function call.
        :param angles: Euler angles specified in radians (degrees is False) or degrees
        (degrees is True). For a single character seq, angles can be:
        - a single value
        - array_like with shape (N,), where each angle[i] corresponds to a single
          rotation
        - array_like with shape (N, 1), where each angle[i, 0] corresponds to a single
          rotation
        For 2- and 3-character wide seq, angles can be:
        - array_like with shape (W,) where W is the width of seq, which corresponds to a
          single rotation with W axes
        - array_like with shape (N, W) where each angle[i] corresponds to a sequence of
          Euler angles describing a single rotation
        :param degrees: If True, then the given angles are assumed to be in degrees.
        Default is False.
        :param origin: Position of the origin
        :return: Local coordinate system
        :return:
        """
        if origin is None:
            origin = np.array([0, 0, 0])
        orientation = Rot.from_euler(sequence, angles, degrees).as_matrix()
        return cls(orientation, origin=origin)

    @classmethod
    def construct_from_orientation(cls, orientation, origin=np.array([0, 0, 0])):
        """
        Construct a cartesian coordinate system from orientation matrix.

        :param orientation: Orthogonal transformation matrix
        :param origin: Position of the origin
        :return: Local coordinate system
        """
        return cls(orientation, origin=origin)

    @classmethod
    def construct_from_xyz(cls, vec_x, vec_y, vec_z, origin=np.array([0, 0, 0])):
        """
        Construct a cartesian coordinate system from 3 basis vectors.

        :param vec_x: Vector defining the x-axis
        :param vec_y: Vector defining the y-axis
        :param vec_z: Vector defining the z-axis
        :param origin: Position of the origin
        :return: Cartesian coordinate system
        """
        basis = np.transpose([vec_x, vec_y, vec_z])
        return cls(basis, origin=origin)

    @classmethod
    def construct_from_xy_and_orientation(
        cls, vec_x, vec_y, positive_orientation=True, origin=np.array([0, 0, 0])
    ):
        """
        Construct a coordinate system from 2 vectors and an orientation.

        :param vec_x: Vector defining the x-axis
        :param vec_y: Vector defining the y-axis
        :param positive_orientation: Set to True if the orientation should
        be positive and to False if not
        :param origin: Position of the origin
        :return: Cartesian coordinate system
        """
        vec_z = cls._calculate_orthogonal_axis(vec_x, vec_y) * cls._sign_orientation(
            positive_orientation
        )

        basis = np.transpose([vec_x, vec_y, vec_z])
        return cls(basis, origin=origin)

    @classmethod
    def construct_from_yz_and_orientation(
        cls, vec_y, vec_z, positive_orientation=True, origin=np.array([0, 0, 0])
    ):
        """
        Construct a coordinate system from 2 vectors and an orientation.

        :param vec_y: Vector defining the y-axis
        :param vec_z: Vector defining the z-axis
        :param positive_orientation: Set to True if the orientation should
        be positive and to False if not
        :param origin: Position of the origin
        :return: Cartesian coordinate system
        """
        vec_x = cls._calculate_orthogonal_axis(vec_y, vec_z) * cls._sign_orientation(
            positive_orientation
        )

        basis = np.transpose(np.array([vec_x, vec_y, vec_z]))
        return cls(basis, origin=origin)

    @classmethod
    def construct_from_xz_and_orientation(
        cls, vec_x, vec_z, positive_orientation=True, origin=np.array([0, 0, 0])
    ):
        """
        Construct a coordinate system from 2 vectors and an orientation.

        :param vec_x: Vector defining the x-axis
        :param vec_z: Vector defining the z-axis
        :param positive_orientation: Set to True if the orientation should
        be positive and to False if not
        :param origin: Position of the origin
        :return: Cartesian coordinate system
        """
        vec_y = cls._calculate_orthogonal_axis(vec_z, vec_x) * cls._sign_orientation(
            positive_orientation
        )

        basis = np.transpose([vec_x, vec_y, vec_z])
        return cls(basis, origin=origin)

    @staticmethod
    def _sign_orientation(positive_orientation):
        """
        Get -1 or 1 depending on the coordinate systems orientation.

        :param positive_orientation: Set to True if the orientation should
        be positive and to False if not
        :return: 1 if the coordinate system has positive orientation,
        -1 otherwise
        """
        if positive_orientation:
            return 1
        return -1

    @staticmethod
    def _calculate_orthogonal_axis(a_0, a_1):
        """
        Calculate an axis which is orthogonal to two other axes.

        The calculated axis has a positive orientation towards the other 2
        axes.

        :param a_0: First axis
        :param a_1: Second axis
        :return: Orthogonal axis
        """
        return np.cross(a_0, a_1)

    @property
    def basis(self):
        """
        Get the normalizes basis as matrix of 3 column vectors.

        This function is identical to the 'orientation' function.

        :return: Basis of the coordinate system
        """
        return self._xarray.basis.transpose(..., "c", "v")

    @property
    def orientation(self):
        """
        Get the coordinate systems orientation matrix.

        This function is identical to the 'basis' function.

        :return: Orientation matrix
        """
        return self._xarray.basis.transpose(..., "c", "v")

    @property
    def origin(self):
        """
        Get the coordinate systems origin.

        This function is identical to the 'location' function.

        :return: Origin of the coordinate system
        """
        return self._xarray.origin.transpose(..., "c")

    @property
    def location(self):
        """
        Get the coordinate systems location.

        This function is identical to the 'origin' function.

        :return: Location of the coordinate system.
        """
        return self._xarray.origin.transpose(..., "c")

    @property
    def xarray(self):
        """
        Get the xarray.Dataset of the LocalCoordinateSystem.

        :return: xarray.Dataset of the coordinate system
        """
        return self._xarray

    def invert(self):
        """
        Get a local coordinate system defining the parent in the child system.

        Inverse is defined as basis_new=basis.T, origin_new=basis.T*(-origin)
        :return: Inverted coordinate system.
        """
        ds = self._xarray.copy(deep=False)

        # transpose rotation matrix (TODO: find the correct "xarray-way" to do this..)
        ds["basis"] = ut.transpose_xarray_axis_data(ds.basis, dim1="c", dim2="v")

        ds["origin"] = xr.apply_ufunc(
            ut.mat_vec_mul,
            ds.basis,
            -ds.origin,
            input_core_dims=[["c", "v"], ["c"]],
            output_core_dims=[["c"]],
        )

        return LocalCoordinateSystem(ds.basis, ds.origin)

    def interp_like(self, rhs):
        """

        :param rhs: für lcs -> pd.DatetimeIndex? -> xarray?
        :return:
        """


# coordinate system manager class ------------------------------------------------------


class CoordinateSystemManager:
    """Manages multiple coordinate systems and the transformations between them."""

    def __init__(self, base_coordinate_system_name="base"):
        self._graph = nx.DiGraph()
        self._graph.add_node(base_coordinate_system_name)

    def _add_edges(self, node_from, node_to, lcs, calculated):
        self._graph.add_edge(node_from, node_to, lcs=lcs, calculated=calculated)
        self._graph.add_edge(
            node_to, node_from, lcs=lcs.invert(), calculated=calculated
        )

    def add_coordinate_system(self, name, parent_system_name, local_coordinate_system):
        if not isinstance(local_coordinate_system, LocalCoordinateSystem):
            raise Exception(
                "'local_coordinate_system' must be an instance of "
                + "weldx.transformations.LocalCoordinateSystem"
            )
        if parent_system_name not in self._graph.nodes:
            raise Exception("Invalid parent system")
        self._graph.add_node(name)
        self._add_edges(name, parent_system_name, local_coordinate_system, False)

    def get_local_coordinate_system(self, cs_child, cs_parent):
        if cs_child not in self.graph.nodes:
            raise Exception("Invalid child system")
        if cs_parent not in self.graph.nodes:
            raise Exception("Invalid parent system")

        path = nx.shortest_path(self.graph, cs_child, cs_parent)
        lcs = self.graph.edges[path[0], path[1]]["lcs"]
        length_path = len(path) - 1
        if length_path > 1:
            for i in np.arange(1, length_path):
                lcs = lcs + self.graph.edges[path[i], path[i + 1]]["lcs"]
            self._add_edges(path[0], path[-1], lcs, True)
        return lcs

    def transform_data(self, data, cs_from, cs_to):
        lcs = self.get_local_coordinate_system(cs_from, cs_to)
        rotation = lcs.orientation.data
        translation = lcs.location.data[:, np.newaxis]
        return np.matmul(rotation, data) + translation

    @property
    def graph(self):
        return self._graph
