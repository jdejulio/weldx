"""Contains classes and functions related to time."""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Union

import numpy as np
import pandas as pd
import pint
import xarray as xr
from pandas import DatetimeIndex, Timedelta, TimedeltaIndex, Timestamp
from xarray import DataArray

from weldx.types import types_time_like, types_timestamp_like

from .util import get_time_union, pandas_time_delta_to_quantity, to_pandas_time_index

__all__ = ["Time"]


class Time:
    """Provides a unified interface for time related operations."""

    def __init__(
        self,
        time: Union[types_time_like, Time],
        time_ref: Union[types_timestamp_like, Time, None] = None,
    ):
        """Initialize a new `Time` class.

        Parameters
        ----------
        time :
            A supported class that represents either absolute or relative times. The
            data must be in ascending order.
        time_ref :
            An absolute reference point in time (timestamp). The return values of all
            accessors that return relative times will be calculated towards this
            reference time.
            This will turn the data of this class into absolute time values if relative
            times are passed as ``time`` parameter. In case ``time`` already contains
            absolute values and this parameter is set to ``None``, the first value of
            the data will be used as reference time.

        """
        if isinstance(time, Time):
            time_ref = time_ref if time_ref is not None else time._time_ref
            time = time._time

        time = to_pandas_time_index(time)

        if len(time) == 1:
            if isinstance(time, pd.DatetimeIndex):
                time = pd.Timestamp(time[0])
            elif isinstance(time, pd.TimedeltaIndex):
                time = pd.Timedelta(time[0])

        if time_ref is not None:
            time_ref = pd.Timestamp(time_ref)
            if isinstance(time, pd.Timedelta):
                time = time + time_ref

        if isinstance(time, pd.TimedeltaIndex) & (time_ref is not None):
            time = time + time_ref

        self._time = time
        self._time_ref = time_ref

    def __add__(self, other):
        # discuss what this is supposed to do. There are multiple possibilities
        return Time(time=self._time + Time(other).as_pandas())

    def __radd__(self, other):
        # custom implementation for right hand syntax with other time-like types
        return self + other

    def __sub__(self, other):
        # discuss what this is supposed to do. There are multiple possibilities
        return Time(time=self._time - Time(other).as_pandas())

    def __rsub__(self, other):
        # custom implementation for right hand syntax with other time-like types
        return Time(time=Time(other).as_pandas() - self._time)

    def __eq__(self, other: Union[types_time_like, Time]) -> bool:
        return self._time == Time(other).as_pandas()

    def all_close(self, other: Union[types_time_like, Time], tolerance) -> bool:
        """Return `True` if another object compares equal within a certain tolerance."""
        return np.allclose(self._time, Time(other).as_pandas())

    def as_quantity(self) -> pint.Quantity:
        """Return the data as `pint.Quantity`."""
        if self.is_absolute:
            q = pandas_time_delta_to_quantity(self._time - self._time_ref)
            setattr(q, "time_ref", self._time_ref)  # store time_ref info
            return q
        return pandas_time_delta_to_quantity(self._time)

    def as_timedelta(self) -> Union[Timedelta, TimedeltaIndex]:
        """Return the data as `pandas.TimedeltaIndex`."""
        if self.is_absolute:
            return self._time - self.reference_time
        return self._time

    def as_datetime(self) -> Union[Timestamp, DatetimeIndex]:
        """Return the data as `pandas.DatetimeIndex`."""
        if not self.is_absolute:
            raise TypeError("Cannot convert non absolute Time object to datetime")
        return self._time

    def as_pandas(self):
        """Return the underlying pandas time datatype."""
        return self._time

    def as_pandas_index(self):
        """Return a pandas index type regardless of length.

        This is useful when using time as coordinate in xarray types.
        """
        if isinstance(self._time, pd.Timestamp):
            return pd.DatetimeIndex([self._time])
        if isinstance(self._time, pd.Timedelta):
            return pd.TimedeltaIndex([self._time])
        return self._time

    def as_data_array(self) -> DataArray:
        """Return the data as `xarray.DataArray`."""
        da = xr.DataArray(self._time, coords={"time": self._time}, dims=["time"])
        da.attrs["time_ref"] = self.reference_time
        return da

    @property
    def reference_time(self) -> Union[Timestamp, None]:
        """Get the reference time."""
        if isinstance(self._time, DatetimeIndex):
            return self._time_ref if self._time_ref is not None else self._time[0]
        elif isinstance(self._time, Timestamp):
            return self._time_ref if self._time_ref is not None else self._time
        return None

    @reference_time.setter
    def reference_time(self, time_ref: Union[types_timestamp_like, Time]):
        """Set the reference time."""
        self._time_ref = pd.Timestamp(time_ref)

    @property
    def is_absolute(self) -> bool:
        """Return `True` if the class has a reference time and `False` otherwise."""
        return isinstance(self._time, (Timestamp, DatetimeIndex))

    @property
    def length(self) -> int:
        """Return the length of the data."""
        if isinstance(self._time, (pd.TimedeltaIndex, pd.DatetimeIndex)):
            return len(self._time)
        return 1

    @property
    def is_timestamp(self) -> bool:
        """Return `True` if the data represents a timestamp and `False` otherwise."""
        return isinstance(self._time, pd.Timestamp)

    def max(self) -> Union[Timedelta, Timestamp]:
        """Get the maximal time of the data."""
        if isinstance(self._time, (pd.TimedeltaIndex, pd.DatetimeIndex)):
            return self._time.max()
        return self._time

    def min(self) -> Union[Timedelta, Timestamp]:
        """Get the minimal time of the data."""
        if isinstance(self._time, (pd.TimedeltaIndex, pd.DatetimeIndex)):
            return self._time.min()
        return self._time

    @staticmethod
    def _from_quantity(time):
        return to_pandas_time_index(time)

    @staticmethod
    def union(times=List[Union[types_time_like, "Time"]]) -> Time:
        """Calculate the union of multiple `Time` instances.

        Parameters
        ----------
        times :
            A list of time class instances

        Returns
        -------
        weldx.Time :
            The time union

        """
        return Time(get_time_union(times))
