"""Collection of common classes and functions."""

import socket
from dataclasses import dataclass
from hashlib import sha256, md5
from pathlib import Path
from typing import Any, Dict, List, Tuple, Union

import numpy as np
import pandas as pd
import pint
import sympy
import xarray as xr

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


@dataclass
class ExternalFile:
    """Handles the asdf serialization of external files."""

    path: Union[str, Path] = None

    filename: str = None
    suffix: str = None
    directory: str = None
    hostname: str = None

    created: pd.Timestamp = None
    modified: pd.Timestamp = None
    size: int = None

    hashing_algorithm: str = "SHA-256"
    asdf_save_content: bool = False
    buffer: bytes = None
    file_system = None

    def __post_init__(self):
        """Initialize the internal values."""
        if self.file_system is not None:
            raise Exception(
                "Using file systems to load a file is currently not supported."
            )

        if self.path is not None:
            if not isinstance(self.path, Path):
                self.path = Path(self.path)
            if not self.path.is_file():
                raise ValueError(f"File not found: {self.path.as_posix()}")

            self.filename = self.path.name
            self.suffix = self.path.suffix  # should we use suffixes (plural) here?
            self.directory = self.path.parent.absolute().as_posix()
            if self.hostname is None:
                self.hostname = socket.gethostname()

            stat = self.path.stat()
            self.size = stat.st_size
            self.created = pd.Timestamp(stat.st_ctime_ns)
            self.modified = pd.Timestamp(stat.st_mtime_ns)

            if self.hashing_algorithm not in self._get_hash_algorithm_mappings():
                raise ValueError(
                    f"'{self.hashing_algorithm}' is not a supported hashing algorithm."
                )

    @staticmethod
    def _get_hash_algorithm_mappings() -> Dict:
        """Get a mapping between hashing algorithm name and corresponding python class.

        Returns
        -------
        Dict :
            A dictionary that maps a hashing algorithm name to a corresponding hashing
            class

        """
        return {"MD5": md5, "SHA-256": sha256}

    @staticmethod
    def _get_hashing_class(algorithm: str) -> Any:
        """Get a class that implements the requested hashing algorithm.

        Parameters
        ----------
        algorithm : str
            Name of the hashing algorithm (MD5, SHA-256)

        Returns
        -------
        Any :
            Class that implements the requested hashing algorithm.

        """
        hashing_class_type = ExternalFile._get_hash_algorithm_mappings().get(algorithm)

        if hashing_class_type is None:
            raise ValueError(f"'{algorithm}' is not a supported hashing algorithm.")

        return hashing_class_type()

    @staticmethod
    def calculate_hash_of_buffer(buffer: bytes, algorithm: str) -> str:
        """Calculate the hash of a buffer.

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
        hashing_class = ExternalFile._get_hashing_class(algorithm)

        hashing_class.update(buffer)
        return hashing_class.hexdigest()

    @staticmethod
    def calculate_hash_of_file(
        path: Union[str, Path], algorithm: str, buffer_size: int = 65536
    ) -> str:
        """Calculate the hash of a file.

        Parameters
        ----------
        path : Union[str, Path]
            Path of the file
        algorithm : str
            Name of the desired hashing algorithm
        buffer_size : int
            Size of the internally used buffer. The file will be read in
            corresponding chunks.

        Returns
        -------
        str :
            The calculated hash

        """
        hashing_class = ExternalFile._get_hashing_class(algorithm)
        with open(path, "rb") as file:
            while True:
                data = file.read(buffer_size)
                if not data:
                    break
                hashing_class.update(data)
        return hashing_class.hexdigest()

    def get_file_content(self) -> bytes:
        """Get the contained bytes of the file.

        Returns
        -------
        bytes :
            The file's content

        """
        if self.file_system is None:
            return self.path.read_bytes()
        return self.file_system.readbytes(self.path)

    def write_to(self, directory: Union[str, Path], file_system=None):
        """Write the file to the specified destination.

        Parameters
        ----------
        directory : :Union[str, Path]
            Directory where the file should be written.
        file_system :
            The target file system.

        """
        path = Path(f"{directory}/{self.filename}")

        buffer = self.buffer
        if buffer is None:
            buffer = self.get_file_content()

        if file_system is None:
            path.write_bytes(buffer)
        else:
            file_system.writebytes(path.as_posix(), buffer)
