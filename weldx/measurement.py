"""Contains measurement related classes and functions."""

from dataclasses import dataclass, field
from typing import List, Union  # noqa: F401

import numpy as np
import pandas as pd
import pint
import xarray as xr

import weldx.utility as ut
from weldx.asdf.tags.weldx.core.mathematical_expression import MathematicalExpression
from weldx.constants import WELDX_QUANTITY as Q_
from weldx.constants import WELDX_UNIT_REGISTRY as UREG


# measurement --------------------------------------------------------------------------
@dataclass
class Data:
    """Simple dataclass implementation for measurement data."""

    name: str
    data: xr.DataArray


@dataclass
class Error:
    """Simple dataclass implementation for signal transformation errors."""

    deviation: float


@dataclass
class Signal:
    """Simple dataclass implementation for measurement signals."""

    signal_type: str
    unit: str
    data: Union[Data, None]


@dataclass
class DataTransformation:
    """Simple dataclass implementation for signal transformations."""

    name: str
    input_signal: Signal
    output_signal: Signal
    error: Error
    func: str = None
    meta: str = None


@dataclass
class Source:
    """Simple dataclass implementation for signal sources."""

    name: str
    output_signal: Signal
    error: Error


@dataclass
class MeasurementChain:
    """Simple dataclass implementation for measurement chains."""

    name: str
    data_source: Source
    data_processors: List = field(default_factory=lambda: [])


@dataclass
class Measurement:
    """Simple dataclass implementation for generic measurements."""

    name: str
    data: Data
    measurement_chain: MeasurementChain


# TODO: move to core package
# TODO: move mathematical expression too
class TimeSeries:
    """Describes a the behaviour of a quantity in time."""

    def __init__(self, data, time=None, interpolation=None):
        # TODO:
        #  - Data + expression one variable
        #  - All xarray except expressions
        self._time = None
        self._data = None
        self._expression = None
        self._interpolation = None
        self._time_var_name = None

        if isinstance(data, pint.Quantity):
            if isinstance(data.magnitude, np.ndarray):
                # TODO: check interpolation type (constant, linear, etc.)
                if interpolation is None:
                    raise ValueError(
                        "An interpolation method must be specified "
                        "if discrete values are used."
                    )

                self._data = xr.DataArray(
                    data=data, dims=["time"], coords={"time": time}
                )
                self._interpolation = interpolation
            else:
                # TODO: check if time is None or time range
                self._time = time
                self._data = data
        elif isinstance(data, MathematicalExpression):

            if data.num_variables() != 1:
                raise Exception(
                    "The mathematical expression must have exactly 1 free "
                    "variable that represents time."
                )
            time_var_name = data.get_variable_names()[0]
            try:
                data.evaluate(**{time_var_name: Q_([0, 1, 2], "second")})
            except (pint.errors.DimensionalityError):
                raise Exception(
                    "Expression can not be evaluated with"
                    ' "pint.Quantity([0,1,2], "seconds")". Ensure that '
                    "every parameter posses the correct unit and that "
                    "vectorization is supported"
                )

            self._expression = data
            self._time_var_name = time_var_name
        else:
            raise TypeError(f'The data type "{type(data)}" is not supported.')

    @property
    def data(self):
        if isinstance(self._data, xr.DataArray):
            return self._data.data
        return self._data

    @property
    def expression(self):
        return self._expression

    @property
    def interpolation(self):
        return self._interpolation

    @property
    def time(self):
        if isinstance(self._data, xr.DataArray):
            return ut.to_pandas_time_index(self._data.time.data)
        return self._time

    @classmethod
    def from_discrete_values(
        cls, time: pd.TimedeltaIndex, data: pint.Quantity, interpolation: str
    ):
        """
        Create a time series from discrete timestamps/time deltas and data points.

        Parameters
        ----------
        time
        data
        interpolation

        Returns
        -------

        """
        return cls(time=time, values=data, interpolation=interpolation)

    @classmethod
    def from_mathematical_expression(cls):
        pass

    def interp_time(self, time):
        if self._data is not None:
            if isinstance(self._data, xr.DataArray):
                if self._interpolation == "linear":
                    interp_data = ut.xr_interp_like(
                        self._data,
                        {"time": time},
                        assume_sorted=True,
                        broadcast_missing=False,
                    ).data
                    if len(time) == 1:
                        return interp_data[0]
                    else:
                        return interp_data
                raise Exception("not implemented")
            else:
                if len(time) == 1:
                    return self._data
                else:
                    return self._data * np.ones(len(time))

        if not isinstance(time, Q_) or not time.check(UREG.get_dimensionality("s")):
            raise ValueError('"time" must be a time quantity.')

        time = {self._time_var_name: time}
        return self._expression.evaluate(**time)

    def shape(self):
        # TODO: Math expression: Evaluate t=0
        # what about the time dimension? ---> : ???
        pass

    def unit(self):
        # TODO: Return pint unit string
        pass


# equipment ----------------------------------------------------------------------------
@dataclass
class GenericEquipment:
    """Simple dataclass implementation for generic equipment."""

    name: str
    sources: List = field(default_factory=lambda: [])
    data_transformations: List = field(default_factory=lambda: [])
