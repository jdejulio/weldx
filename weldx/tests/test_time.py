"""Test the `Time` class."""

import math
from typing import List, Tuple, Type, Union

import numpy as np
import pandas as pd
import pytest
import xarray as xr
from pandas import DatetimeIndex, Timedelta, TimedeltaIndex, Timestamp

from weldx import Q_
from weldx.time import Time, pandas_time_delta_to_quantity
from weldx.types import types_time_like


def _initialize_delta_type(cls_type, values, unit):
    """Initialize the passed time type."""
    if cls_type is np.timedelta64:
        if isinstance(values, List):
            return np.array(values, dtype=f"timedelta64[{unit}]")
        return np.timedelta64(values, unit)
    if cls_type is Time:
        return Time(Q_(values, unit))
    if cls_type is str:
        if not isinstance(values, List):
            return f"{values}{unit}"
        return [f"{v}{unit}" for v in values]
    return cls_type(values, unit)


def _initialize_datetime_type(cls_type, values):
    """Initialize the passed datetime type."""
    if cls_type is np.datetime64:
        if isinstance(values, List):
            return np.array(values, dtype="datetime64")
        return np.datetime64(values)
    if cls_type is str:
        return values
    return cls_type(values)


def _initialize_date_time_quantity(timedelta, unit, time_ref):
    """Initialize a quantity that represents a datetime by adding a ``time_ref``."""
    quantity = Q_(timedelta, unit)
    setattr(quantity, "time_ref", Timestamp(time_ref))
    return quantity


def _transform_array(data, is_array, is_scalar):
    """Transform an array into a scalar, single value array or return in unmodified."""
    if not is_array:
        return data[0]
    if is_scalar:
        return [data[0]]
    return data


def _initialize_time_type(
    input_type, delta_val, abs_val, is_timedelta, is_array, is_scalar, unit="s"
):
    """Create an instance of the desired input type."""
    val = delta_val if is_timedelta else abs_val
    if not is_timedelta and input_type is Q_:
        val = [v - delta_val[0] for v in delta_val]
    val = _transform_array(val, is_array=is_array, is_scalar=is_scalar)

    # create the time input ---------------------------------
    if is_timedelta:
        return _initialize_delta_type(input_type, val, unit)
    if input_type is not Q_:
        return _initialize_datetime_type(input_type, val)
    return _initialize_date_time_quantity(val, unit, abs_val[0])


def _is_timedelta(cls_type):
    """Return ``True`` if the passed type is a timedelta type."""
    return cls_type in [TimedeltaIndex, Timedelta, np.timedelta64] or (
        cls_type is Time and not Time.is_absolute
    )


def _is_datetime(cls_type):
    """Return ``True`` if the passed type is a datetime type."""
    return not _is_timedelta(cls_type)


class TestTime:
    """Test the time class."""

    # test_init helper functions -------------------------------------------------------

    @staticmethod
    def _parse_time_type_test_input(
        type_input,
    ) -> Tuple[Union[types_time_like, Time], bool]:
        """Return the time type and a bool that defines if the returned type is a delta.

        This is mainly used in generalized tests where a type like `Time` itself can
        represent deltas and absolute times. In this case one can use this function
        to extract the information from a tuple.

        """
        if isinstance(type_input, Tuple):
            # to avoid wrong test setups due to spelling mistakes
            assert type_input[1] in ["timedelta", "datetime"]
            time_type = type_input[0]
            is_timedelta = type_input[1] == "timedelta"
        else:
            time_type = type_input
            is_timedelta = _is_timedelta(type_input)
        return time_type, is_timedelta

    @classmethod
    def _get_init_exp_values(
        cls,
        is_timedelta,
        time_ref,
        data_was_scalar,
        delta_val,
        abs_val,
    ):
        """Get the expected result values for the `__init__` test."""
        exp_is_absolute = time_ref is not None or not is_timedelta

        # expected reference time
        exp_time_ref = None
        if exp_is_absolute:
            exp_time_ref = Timestamp(time_ref if time_ref is not None else abs_val[0])

        # expected time delta values
        val = delta_val
        if exp_is_absolute:
            offset = 0
            if not is_timedelta:
                if time_ref is not None:
                    offset = Timestamp(abs_val[0]) - Timestamp(time_ref)
                    offset = offset.total_seconds()
                offset -= delta_val[0]

            val = [v + offset for v in delta_val]

        val = val[0] if data_was_scalar else val
        exp_timedelta = (
            Timedelta(val, "s") if data_was_scalar else TimedeltaIndex(val, "s")
        )

        # expected datetime
        exp_datetime = None
        if exp_is_absolute:
            time_ref = Timestamp(time_ref if time_ref is not None else abs_val[0])
            exp_datetime = time_ref + exp_timedelta

        return dict(
            is_absolute=exp_is_absolute,
            time_ref=exp_time_ref,
            timedelta=exp_timedelta,
            datetime=exp_datetime,
        )

    # test_init ------------------------------------------------------------------------

    @pytest.mark.parametrize("scl, arr", [(True, False), (True, True), (False, True)])
    @pytest.mark.parametrize("set_time_ref", [False, True])
    @pytest.mark.parametrize(
        "input_vals",
        [
            (str, "timedelta"),
            (Time, "timedelta"),
            (Q_, "timedelta"),
            TimedeltaIndex,
            Timedelta,
            np.timedelta64,
            (str, "datetime"),
            (Time, "datetime"),
            (Q_, "datetime"),
            DatetimeIndex,
            Timestamp,
            np.datetime64,
        ],
    )
    def test_init(
        self,
        input_vals: Union[Type, Tuple[Type, str]],
        set_time_ref: bool,
        scl: bool,
        arr: bool,
    ):
        """Test the `__init__` method of the time class.

        Parameters
        ----------
        input_vals :
            Either a compatible time type or a tuple of two values. The tuple is needed
            in case the tested time type can either represent relative time values as
            well as absolute ones. In this case, the first value is the type. The
            second value is a string specifying if the type represents absolute
            ("datetime") or relative ("timedelta") values.
        set_time_ref :
            If `True`, a reference time will be passed to the `__init__` method
        scl :
            If `True`, the data of the passed type consists of a single value.
        arr :
            If `True`, the data of the passed type is an array

        """
        input_type, is_timedelta = self._parse_time_type_test_input(input_vals)

        # skip matrix cases that do not work --------------------
        if arr and input_type in [Timedelta, Timestamp]:
            pytest.skip()
        if not arr and input_type in [DatetimeIndex, TimedeltaIndex]:
            pytest.skip()

        # create input values -----------------------------------
        delta_val = [1, 2, 3]
        abs_val = [f"2000-01-01 16:00:0{v}" for v in delta_val]

        time = _initialize_time_type(
            input_type, delta_val, abs_val, is_timedelta, arr, scl
        )
        time_ref = "2000-01-01 15:00:00" if set_time_ref else None

        # create `Time` instance --------------------------------
        time_class_instance = Time(time, time_ref)

        # check results -----------------------------------------
        exp = self._get_init_exp_values(is_timedelta, time_ref, scl, delta_val, abs_val)

        assert time_class_instance.is_absolute == exp["is_absolute"]
        assert time_class_instance.reference_time == exp["time_ref"]
        assert np.all(time_class_instance.as_timedelta() == exp["timedelta"])
        if exp["is_absolute"]:
            assert np.all(time_class_instance.as_datetime() == exp["datetime"])
        else:
            with pytest.raises(TypeError):
                time_class_instance.as_datetime()

    # todo: issues
    #   - time parameter can be None

    # test_init_exceptions -------------------------------------------------------------

    @staticmethod
    @pytest.mark.parametrize(
        "time, time_ref, raises",
        [
            (TimedeltaIndex([3, 2, 1]), None, ValueError),
            (DatetimeIndex(["2010", "2000"]), None, ValueError),
            (["2010", "2000"], None, ValueError),
            (Q_([3, 2, 1], "s"), None, ValueError),
            (np.array([3, 2, 1], dtype="timedelta64[s]"), None, ValueError),
        ],
    )
    def test_init_exception(time, time_ref, raises):
        """Test initialization of the `Time` class with all supported types."""
        with pytest.raises(raises):
            Time(time, time_ref)

    # test_add_timedelta ---------------------------------------------------------------

    @pytest.mark.parametrize("other_on_rhs", [True, False])
    @pytest.mark.parametrize("time_class_is_array", [False, True])
    @pytest.mark.parametrize("other_is_array", [False, True])
    @pytest.mark.parametrize("unit", ["s", "h"])
    @pytest.mark.parametrize(
        "other_type",
        [
            (str, "timedelta"),
            (Time, "timedelta"),
            (Q_, "timedelta"),
            TimedeltaIndex,
            Timedelta,
            np.timedelta64,
            (str, "datetime"),
            (Time, "datetime"),
            (Q_, "datetime"),
            DatetimeIndex,
            Timestamp,
            np.datetime64,
        ],
    )
    def test_add_timedelta(
        self,
        other_type,
        other_on_rhs: bool,
        unit: str,
        time_class_is_array: bool,
        other_is_array: bool,
    ):
        """Test the `__add__` method if the `Time` class represents a time delta.

        Parameters
        ----------
        other_type :
            The type of the other object
        other_on_rhs :
            If `True`, the other type is on the rhs of the + sign and on the lhs
            otherwise
        unit :
            The time unit to use
        time_class_is_array :
            If `True`, the `Time` instance contains 3 time values and 1 otherwise
        other_is_array :
            If `True`, the other time object contains 3 time values and 1 otherwise

        """
        other_type, is_timedelta = self._parse_time_type_test_input(other_type)

        # skip array cases where the type does not support arrays
        if other_type in [Timedelta, Timestamp] and other_is_array:
            pytest.skip()
        if not other_is_array and other_type in [DatetimeIndex, TimedeltaIndex]:
            pytest.skip()

        # skip __radd__ cases where we got conflicts with the other types' __add__
        if not other_on_rhs and other_type in (
            Q_,
            np.ndarray,
            np.timedelta64,
            np.datetime64,
        ):
            pytest.skip()

        # setup rhs
        delta_val = [4, 6, 8]
        if unit == "s":
            abs_val = [f"2000-01-01 10:00:0{v}" for v in delta_val]
        else:
            abs_val = [f"2000-01-01 1{v}:00:00" for v in delta_val]
        other = _initialize_time_type(
            other_type,
            delta_val,
            abs_val,
            is_timedelta,
            other_is_array,
            not other_is_array,
            unit,
        )

        # setup lhs
        time_class_values = [1, 2, 3] if time_class_is_array else [1]
        time_class = Time(Q_(time_class_values, unit))

        # setup expected values
        add = delta_val if other_is_array else delta_val[0]
        exp_val = np.array(time_class_values) + add
        exp_val += 0 if is_timedelta else time_class_values[0] - exp_val[0]

        exp_time_ref = None if is_timedelta else abs_val[0]
        exp = Time(Q_(exp_val, unit), exp_time_ref)

        # calculate and evaluate result
        res = time_class + other if other_on_rhs else other + time_class

        assert res.reference_time == exp.reference_time
        assert np.all(res.as_timedelta() == exp.as_timedelta())
        assert np.all(res == exp)

    # test_convert_util ----------------------------------------------------------------

    @staticmethod
    def test_convert_util():
        """Test basic conversion functions from/to xarray/pint."""
        t = pd.date_range("2020", periods=10, freq="1s")
        ts = t[0]

        arr = xr.DataArray(
            np.arange(10),
            dims=["time"],
            coords={"time": t - ts},
        )
        arr.time.weldx.time_ref = ts
        time = Time(arr)

        assert time.length == len(t)
        assert time.equals(Time(t))

        time_q = time.as_quantity()
        assert np.all(time_q == Q_(range(10), "s"))
        assert time_q.time_ref == ts

        arr2 = time.as_data_array().weldx.time_ref_restore()
        assert arr.time.identical(arr2.time)


# test_pandas_time_delta_to_quantity ---------------------------------------------------


def test_pandas_time_delta_to_quantity():
    """Test the 'pandas_time_delta_to_quantity' utility function."""
    is_close = np.vectorize(math.isclose)

    def _check_close(t1, t2):
        assert np.all(is_close(t1.magnitude, t2.magnitude))
        assert t1.units == t2.units

    time_single = pd.TimedeltaIndex([1], unit="s")

    _check_close(pandas_time_delta_to_quantity(time_single), Q_(1, "s"))
    _check_close(pandas_time_delta_to_quantity(time_single, "ms"), Q_(1000, "ms"))
    _check_close(pandas_time_delta_to_quantity(time_single, "us"), Q_(1000000, "us"))
    _check_close(pandas_time_delta_to_quantity(time_single, "ns"), Q_(1000000000, "ns"))

    time_multi = pd.TimedeltaIndex([1, 2, 3], unit="s")
    _check_close(pandas_time_delta_to_quantity(time_multi), Q_([1, 2, 3], "s"))
    _check_close(
        pandas_time_delta_to_quantity(time_multi, "ms"), Q_([1000, 2000, 3000], "ms")
    )
    _check_close(
        pandas_time_delta_to_quantity(time_multi, "us"),
        Q_([1000000, 2000000, 3000000], "us"),
    )
    _check_close(
        pandas_time_delta_to_quantity(time_multi, "ns"),
        Q_([1000000000, 2000000000, 3000000000], "ns"),
    )
