"""Collection of common classes and functions."""

import socket
from hashlib import sha256
from pathlib import Path
from typing import Any, Dict, List, Tuple, Union

import numpy as np
import pandas as pd
import pint
import sympy
import xarray as xr
from fs.osfs import OSFS

import weldx.utility as ut
from weldx.constants import WELDX_QUANTITY as Q_
from weldx.constants import WELDX_UNIT_REGISTRY as UREG


class MathematicalExpression:
    """Mathematical expression using sympy syntax."""

    def __init__(
        self, expression: Union[sympy.Expr, str], parameters: Union[Dict, None] = None
    ):
        """Construct a MathematicalExpression.

        Parameters
        ----------
        expression
            A sympy expression or a string that can be evaluated as one.
        parameters :
            A dictionary containing constant values for variables of the
            expression.

        """
        if not isinstance(expression, sympy.Expr):
            expression = sympy.sympify(expression)
        self._expression = expression
        self.function = sympy.lambdify(
            tuple(self._expression.free_symbols), self._expression, "numpy"
        )
        self._parameters = {}
        if parameters is not None:
            if not isinstance(parameters, dict):
                raise ValueError(
                    f'"parameters" must be dictionary, got {type(parameters)}'
                )
            variable_names = self.get_variable_names()
            for key in parameters:
                if key not in variable_names:
                    raise ValueError(
                        f'The expression does not have a parameter "{key}"'
                    )
            self._parameters = parameters

    def __repr__(self):
        """Give __repr__ output."""
        representation = (
            f"<MathematicalExpression>\n"
            f"Expression:\n\t {self._expression.__repr__()}"
            f"\nParameters:\n"
        )
        if len(self._parameters) > 0:
            for parameter, value in self._parameters.items():
                representation += f"\t{parameter} = {value}\n"
        else:
            representation += "\tNone"
        return representation

    def __eq__(self, other):
        """Return the result of a structural equality comparison with another object.

        If the other object is not a 'MathematicalExpression' this function always
        returns 'False'.

        Parameters
        ----------
        other:
            Other object.

        Returns
        -------
        bool:
            'True' if the compared object is also a 'MathematicalExpression' and equal
            to this instance, 'False' otherwise

        """
        return self.equals(other, check_parameters=True, check_structural_equality=True)

    def equals(
        self,
        other: Any,
        check_parameters: bool = True,
        check_structural_equality: bool = False,
    ):
        """Compare the instance with another object for equality and return the result.

        If the other object is not a MathematicalExpression this function always returns
        'False'. The function offers the choice to compare for structural or
        mathematical equality by setting the 'structural_expression_equality' parameter
        accordingly. Additionally, the comparison can be limited to the expression only,
        if 'check_parameters' is set to 'False'.

        Parameters
        ----------
        other:
            Arbitrary other object.
        check_parameters
            Set to 'True' if the parameters should be included during the comparison. If
            'False', only the expression is checked for equality.
        check_structural_equality:
            Set to 'True' if the expression should be checked for structural equality.
            Set to 'False' if mathematical equality is sufficient.

        Returns
        -------
        bool:
            'True' if both objects are equal, 'False' otherwise

        """
        if isinstance(other, MathematicalExpression):
            if check_structural_equality:
                equality = self.expression == other.expression
            else:
                equality = sympy.simplify(self.expression - other.expression) == 0

            if check_parameters:
                equality = equality and self._parameters == other.parameters
            return equality
        return False

    def set_parameter(self, name, value):
        """Define an expression parameter as constant value.

        Parameters
        ----------
        name
            Name of the parameter used in the expression.
        value
            Parameter value. This can be number, array or pint.Quantity

        """
        if not isinstance(name, str):
            raise TypeError(f'Parameter "name" must be a string, got {type(name)}')
        if name not in str(self._expression.free_symbols):
            raise ValueError(
                f'The expression "{self._expression}" does not have a '
                f'parameter with name "{name}".'
            )
        self._parameters[name] = value

    @property
    def num_parameters(self):
        """Get the expressions number of parameters.

        Returns
        -------
        int:
            Number of parameters.

        """
        return len(self._parameters)

    @property
    def num_variables(self):
        """Get the expressions number of free variables.

        Returns
        -------
        int:
            Number of free variables.

        """
        return len(self.expression.free_symbols) - len(self._parameters)

    @property
    def expression(self):
        """Return the internal sympy expression.

        Returns
        -------
        sympy.core.expr.Expr:
            Internal sympy expression

        """
        return self._expression

    @property
    def parameters(self) -> Dict:
        """Return the internal parameters dictionary.

        Returns
        -------
        Dict
            Internal parameters dictionary

        """
        return self._parameters

    def get_variable_names(self) -> List:
        """Get a list of all expression variables.

        Returns
        -------
        List:
            List of all expression variables

        """
        return [
            str(var)
            for var in self._expression.free_symbols
            if str(var) not in self._parameters
        ]

    def evaluate(self, **kwargs) -> Any:
        """Evaluate the expression for specific variable values.

        Parameters
        ----------
        kwargs
            additional keyword arguments (variable assignment) to pass.

        Returns
        -------
        Any:
            Result of the evaluated function

        """
        intersection = set(kwargs).intersection(self._parameters)
        if len(intersection) > 0:
            raise ValueError(
                f"The variables {intersection} are already defined as parameters."
            )
        inputs = {**kwargs, **self._parameters}
        return self.function(**inputs)


# TimeSeries ---------------------------------------------------------------------------


class TimeSeries:
    """Describes the behaviour of a quantity in time."""

    _valid_interpolations = ["step", "linear"]

    def __init__(
        self,
        data: Union[pint.Quantity, MathematicalExpression],
        time: Union[None, pd.TimedeltaIndex, pint.Quantity] = None,
        interpolation: str = "linear",
    ):
        """Construct a TimSeries.

        Parameters
        ----------
        data:
            Either a pint.Quantity or a weldx.MathematicalExpression. If a mathematical
            expression is chosen, it is only allowed to have a single free variable,
            which represents time.
        time:
            An instance of pandas.TimedeltaIndex if a quantity is passed and 'None'
            otherwise.
        interpolation:
            A string defining the desired interpolation method. This is only relevant if
            a quantity is passed as data. Currently supported interpolation methods are:
            'step', 'linear'.

        """
        self._data = None
        self._time_var_name = None
        self._shape = None
        self._units = None

        if isinstance(data, pint.Quantity):
            if not np.iterable(data):  # expand dim for scalar input
                data = np.expand_dims(data, 0)
            if time is None:  # constant value case
                time = pd.TimedeltaIndex([0])
                interpolation = None
            elif interpolation not in self._valid_interpolations:
                raise ValueError(
                    "A valid interpolation method must be specified if discrete "
                    f'values are used. "{interpolation}" is not supported'
                )
            if isinstance(time, pint.Quantity):
                time = ut.to_pandas_time_index(time)
            if not isinstance(time, pd.TimedeltaIndex):
                raise ValueError(
                    '"time" must be a time quantity or a "pandas.TimedeltaIndex".'
                )

            dax = xr.DataArray(
                data=data,
                attrs={"interpolation": interpolation},
            )
            self._data = dax.rename({"dim_0": "time"}).assign_coords({"time": time})

        elif isinstance(data, MathematicalExpression):

            if data.num_variables != 1:
                raise Exception(
                    "The mathematical expression must have exactly 1 free "
                    "variable that represents time."
                )
            time_var_name = data.get_variable_names()[0]
            try:
                eval_data = data.evaluate(**{time_var_name: Q_(1, "second")})
                self._units = eval_data.units
                if np.iterable(eval_data):
                    self._shape = eval_data.shape
                else:
                    self._shape = (1,)
            except pint.errors.DimensionalityError:
                raise Exception(
                    "Expression can not be evaluated with "
                    '"weldx.Quantity(1, "seconds")"'
                    ". Ensure that every parameter posses the correct unit."
                )

            self._data = data
            self._time_var_name = time_var_name

            try:
                self.interp_time(Q_([1, 2], "second"))
                self.interp_time(Q_([1, 2, 3], "second"))
            except Exception as e:
                raise Exception(
                    "The expression can not be evaluated with arrays of time deltas. "
                    "Ensure that all parameters that are multiplied with the time "
                    "variable have an outer dimension of size 1. This dimension is "
                    "broadcasted during multiplication. The original error message was:"
                    f' "{str(e)}"'
                )

        else:
            raise TypeError(f'The data type "{type(data)}" is not supported.')

    def __eq__(self, other: Any) -> bool:
        """Return the result of a structural equality comparison with another object.

        If the other object is not a 'TimeSeries' this function always returns 'False'.

        Parameters
        ----------
        other:
            Other object.

        Returns
        -------
        bool:
           'True' if the compared object is also a 'TimeSeries' and equal to
            this instance, 'False' otherwise

        """
        if not isinstance(other, TimeSeries):
            return False
        if not isinstance(self.data, MathematicalExpression):
            if not isinstance(other.data, pint.Quantity):
                return False
            return self._data.identical(other.data_array)

        return self._data == other.data

    def __repr__(self):
        """Give __repr__ output."""
        representation = "<TimeSeries>"
        if isinstance(self._data, xr.DataArray):
            if self._data.shape[0] == 1:
                representation += f"\nConstant value:\n\t{self.data.magnitude[0]}\n"
            else:
                representation += (
                    f"\nTime:\n\t{self.time}\n"
                    + f"Values:\n\t{self.data.magnitude}\n"
                    + f'Interpolation:\n\t{self._data.attrs["interpolation"]}\n'
                )
        else:
            representation += self.data.__repr__().replace(
                "<MathematicalExpression>", ""
            )
        return representation + f"Units:\n\t{self.units}\n"

    @property
    def data(self) -> Union[pint.Quantity, MathematicalExpression]:
        """Return the data of the TimeSeries.

        This is either a set of discrete values/quantities or a mathematical expression.

        Returns
        -------
        pint.Quantity:
            Underlying data array.
        MathematicalExpression:
            A mathematical expression describing the time dependency

        """
        if isinstance(self._data, xr.DataArray):
            return self._data.data
        return self._data

    @property
    def data_array(self) -> Union[xr.DataArray, None]:
        """Return the internal data as 'xarray.DataArray'.

        If the TimeSeries contains an expression, 'None' is returned.

        Returns
        -------
        xarray.DataArray:
            The internal data as 'xarray.DataArray'

        """
        if isinstance(self._data, xr.DataArray):
            return self._data
        return None

    @property
    def interpolation(self) -> Union[str, None]:
        """Return the interpolation.

        Returns
        -------
        str:
            Interpolation of the TimeSeries

        """
        if isinstance(self._data, xr.DataArray):
            return self._data.attrs["interpolation"]
        return None

    @property
    def time(self) -> Union[None, pd.TimedeltaIndex]:
        """Return the data's timestamps.

        Returns
        -------
        pandas.TimedeltaIndex:
            Timestamps of the  data

        """
        if isinstance(self._data, xr.DataArray) and len(self._data.time) > 1:
            return ut.to_pandas_time_index(self._data.time.data)
        return None

    def interp_time(
        self, time: Union[pd.TimedeltaIndex, pint.Quantity], time_unit: str = "s"
    ) -> xr.DataArray:
        """Interpolate the TimeSeries in time.

        If the internal data consists of discrete values, an interpolation with the
        prescribed interpolation method is performed. In case of mathematical
        expression, the expression is evaluated for the given timestamps.

        Parameters
        ----------
        time:
            A set of timestamps.
        time_unit:
            Only important if the time series is described by an expression and a
            'pandas.TimedeltaIndex' is passed to this function. In this case, time is
            converted to a quantity with the provided unit. Even though pint handles
            unit prefixes automatically, the accuracy of the results can be heavily
            influenced if the provided unit results in extreme large or
            small values when compared to the parameters of the expression.

        Returns
        -------
        xarray.DataArray:
            A data array containing the interpolated data.

        """
        if isinstance(self._data, xr.DataArray):
            if isinstance(time, pint.Quantity):
                time = ut.to_pandas_time_index(time)
            if not isinstance(time, pd.TimedeltaIndex):
                raise ValueError(
                    '"time" must be a time quantity or a "pandas.TimedeltaIndex".'
                )
            # constant values are also treated by this branch
            if self._data.attrs["interpolation"] == "linear" or self.shape[0] == 1:
                return ut.xr_interp_like(
                    self._data,
                    {"time": time},
                    assume_sorted=False,
                    broadcast_missing=False,
                )

            dax = self._data.reindex({"time": time}, method="ffill")
            return dax.fillna(self._data[0])

        # Transform time to both formats
        if isinstance(time, pint.Quantity) and time.check(UREG.get_dimensionality("s")):
            time_q = time
            time_pd = ut.to_pandas_time_index(time)
        elif isinstance(time, pd.TimedeltaIndex):
            time_q = ut.pandas_time_delta_to_quantity(time, time_unit)
            time_pd = time
        else:
            raise ValueError(
                '"time" must be a time quantity or a "pandas.TimedeltaIndex".'
            )

        if len(self.shape) > 1 and np.iterable(time_q):
            while len(time_q.shape) < len(self.shape):
                time_q = time_q[:, np.newaxis]

        # evaluate expression
        data = self._data.evaluate(**{self._time_var_name: time_q})
        data = data.astype(float).to_reduced_units()  # float conversion before reduce!

        # create data array
        if not np.iterable(data):  # make sure quantity is not scalar value
            data = np.expand_dims(data, 0)

        dax = xr.DataArray(data=data)  # don't know exact dimensions so far
        return dax.rename({"dim_0": "time"}).assign_coords({"time": time_pd})

    @property
    def shape(self) -> Tuple:
        """Return the shape of the TimeSeries data.

        For mathematical expressions, the shape does not contain the time axis.

        Returns
        -------
        Tuple:
            Tuple describing the data's shape

        """
        if isinstance(self._data, xr.DataArray):
            return self._data.shape
        return self._shape

    @property
    def units(self) -> str:
        """Return the units of the TimeSeries Data.

        Returns
        -------
        str:
            Unit sting

        """
        if isinstance(self._data, xr.DataArray):
            return self._data.data.units
        return self._units


# ExternalFile -------------------------------------------------------------------------


class ExternalFile:
    """Handles external files."""

    def __init__(
        self,
        path,
        file_system=None,
        hashing_algorithm: str = "SHA-256",
        asdf_save_content: bool = False,
        hostname=None,
        _tree: Dict = None,
    ):
        """Create an `ExternalFile` instance.

        Parameters
        ----------
        path : Union[str, Path]
            The path of the file
        file_system :
            The file system of the file
        hashing_algorithm : str
            The name of the hashing algorithm that should be used.
        asdf_save_content : bool
            Set to `True` if the file should be stored inside of an asdf file during
            serialization.
        hostname : str
            The hostname of the file. If `None` is provided, it is determined
            automatically.
        _tree : Dict
            This is an internal parameter for deserialization. Do not use it!

        """
        if _tree is None:
            if isinstance(path, str):
                path = Path(path)

            # todo: check filesystems too
            if file_system is None and not path.is_file():
                raise ValueError(f"File not found: {path.as_posix()}")

            if hostname is None:
                hostname = socket.gethostname()

            self._hostname = hostname
            self._save_content = asdf_save_content
            self._path = path
            self._file_system = file_system
            self._buffer = None
            self._hashing_algorithm = hashing_algorithm

            if file_system is None:
                with OSFS(self._path.parent.absolute().as_posix()) as system:
                    self._info = system.getdetails(self._path.name)
            else:
                self._info = file_system.getdetails(self._path)
        else:
            directory = _tree.get("location", None)
            file_name = _tree["filename"]
            if directory is not None:
                self._path = Path(f"{directory}/{file_name}")
            else:
                self._path = Path(file_name)
            self._hostname = _tree.get("hostname", None)

            self._hash = None
            self._hashing_algorithm = None
            hash_data = _tree.get("content_hash")
            if hash_data is not None:
                self._hash = hash_data.get("value", None)
                self._hashing_algorithm = hash_data.get("algorithm", None)

            buffer = _tree.get("content", None)
            if buffer is not None:
                self._buffer = buffer.tobytes()
                hash_calc = self.calculate_hash(self._buffer, self._hashing_algorithm)
                if not hash_calc == self._hash:
                    raise Exception(
                        "The stored hash does not match the stored contents' hash."
                    )

    def _write_content(self, buffer, path, file_system):
        """Write the content of the passed buffer to a file.

        Parameters
        ----------
        buffer : bytes
            A buffer that should be written to a file
        path : str
            The destination where the file should be written to
        file_system :
            The target file system

        """
        file_system.writebytes(f"{path}/{self.filename}", buffer)

    def get_file_content(self):
        """Get the content of the file as bytes.

        Returns
        -------
        bytes :
            Content of the file

        """
        if self._buffer is None:
            if self._file_system is None:
                with OSFS(self._path.parent.absolute().as_posix()) as file_system:
                    return file_system.readbytes(self.filename)
            return self._file_system.readbytes(self.filename)
        return self._buffer

    @classmethod
    def calculate_hash(cls, buffer: bytes, algorithm: str):
        """Get the hash of the content of a buffer.

        Parameters
        ----------
        buffer : bytes
            A buffer
        algorithm : str
            Name of the desired hashing algorithm

        Returns
        -------
        str :
            The calculated hash

        """
        # https://www.freecodecamp.org/news/md5-vs-sha-1-vs-sha-2-which-is-the-most-secure-encryption-hash-and-how-to-check-them/
        # https://softwareengineering.stackexchange.com/questions/49550/which-hashing-algorithm-is-best-for-uniqueness-and-speed
        if algorithm == "SHA-256":
            hasher = sha256()
        else:
            raise ValueError(f"Unsupported hash algorithm: {algorithm}")
        hasher.update(buffer)
        return hasher.hexdigest()

    def write_to(self, path: Union[str, Path], file_system=None):
        """Write the file to the specified destination.

        Parameters
        ----------
        path : :Union[str, Path]
            Path where the file should be written.
        file_system :
            The target file system.

        """
        if isinstance(path, str):
            path = Path(path)

        buffer = self.get_file_content()
        if file_system is None:
            with OSFS(path.absolute().as_posix()) as system:
                self._write_content(buffer, "", system)
        else:
            self._write_content(buffer, path, file_system)

    @property
    def asdf_save_content(self):
        """Return `True` if the file content should be stored in an asdf file.

        Returns
        -------
        bool :
            `True` if the file content should be stored in an asdf file, `False`
            otherwise

        """
        return self._save_content

    @property
    def created(self):
        """Get the timestamp of the file's creation.

        Returns
        -------
        pandas.Timestamp :
            Time when the file was created.

        """
        return pd.Timestamp(self._info.created)

    @property
    def hash_algorithm(self) -> str:
        """Get the hash algorithm.

        Returns
        -------
        str :
            The hash algorithm

        """
        return self._hashing_algorithm

    @property
    def hostname(self):
        """Get the hostname of the file.

        Returns
        -------
        str :
            The file's hostname.

        """
        return self._hostname

    @property
    def filename(self):
        """Get the filename.

        Returns
        -------
        str:
            The filename

        """
        return self._path.name

    @property
    def modified(self):
        """Get the timestamp of the file's last modification.

        Returns
        -------
        pandas.Timestamp :
            Time when the file was last modified.

        """
        return pd.Timestamp(self._info.modified)

    @property
    def location(self):
        """Return the file's absolute path.

        Returns
        -------
        str:
            The file's absolute path.

        """
        return self._path.parent.absolute().as_posix()

    @property
    def size(self):
        """Return the size of the file in bytes.

        Returns
        -------
        int :
            Size of the file in bytes

        """
        return self._info.size
