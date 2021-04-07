"""Test the measurement package."""

from typing import Dict

import asdf
import pytest
import sympy
import xarray as xr

import weldx.measurement as msm
from tests._helpers import get_test_name
from weldx.asdf.util import _write_read_buffer
from weldx.constants import WELDX_QUANTITY as Q_
from weldx.core import MathematicalExpression
from weldx.measurement import Error, MeasurementChainGraph


def test_generic_measurement():
    """Test basic measurement creation and ASDF read/write."""
    data_01 = msm.Data(
        name="Welding current", data=xr.DataArray([1, 2, 3, 4], dims=["time"])
    )

    data_02 = msm.Data(
        name="Welding voltage", data=xr.DataArray([10, 20, 30, 40], dims=["time"])
    )

    src_01 = msm.Source(
        name="Current Sensor",
        output_signal=msm.Signal("analog", "V", data=None),
        error=msm.Error(1337.42),
    )

    src_02 = msm.Source(
        name="Voltage Sensor",
        output_signal=msm.Signal("analog", "V", data=None),
        error=msm.Error(1),
    )

    dp_01 = msm.DataTransformation(
        name="AD conversion current measurement",
        input_signal=src_01.output_signal,
        output_signal=msm.Signal("digital", "V", data=None),
        error=msm.Error(999.0),
    )

    dp_02 = msm.DataTransformation(
        name="Calibration current measurement",
        input_signal=dp_01.output_signal,
        output_signal=msm.Signal("digital", "A", data=data_01),
        error=msm.Error(43.0),
    )

    dp_03 = msm.DataTransformation(
        name="AD conversion voltage measurement",
        input_signal=dp_02.output_signal,
        output_signal=msm.Signal("digital", "V", data=None),
        error=msm.Error(2.0),
    )

    dp_04 = msm.DataTransformation(
        name="Calibration voltage measurement",
        input_signal=dp_03.output_signal,
        output_signal=msm.Signal("digital", "V", data=data_02),
        error=msm.Error(Q_(3.0, "percent")),
    )

    chn_01 = msm.MeasurementChain(
        name="Current measurement", data_source=src_01, data_processors=[dp_01, dp_02]
    )

    chn_02 = msm.MeasurementChain(
        name="Voltage measurement", data_source=src_02, data_processors=[dp_03, dp_04]
    )

    eqp_01 = msm.GenericEquipment(
        "Current Sensor", sources=[src_01], data_transformations=[dp_02]
    )
    eqp_02 = msm.GenericEquipment(
        "AD Converter", sources=None, data_transformations=[dp_01, dp_03]
    )
    eqp_03 = msm.GenericEquipment(
        "Voltage Sensor", sources=None, data_transformations=[dp_04]
    )

    measurement_01 = msm.Measurement(
        name="Current measurement", data=[data_01], measurement_chain=chn_01
    )
    measurement_02 = msm.Measurement(
        name="Voltage measurement", data=[data_02], measurement_chain=chn_02
    )

    equipment = [eqp_01, eqp_02, eqp_03]
    measurement_data = [data_01, data_02]
    measurement_chains = [chn_01]
    measurements = [measurement_01, measurement_02]
    sources = [src_01]
    processors = [dp_01, dp_02]

    [a, x, b] = sympy.symbols("a x b")
    expr_01 = MathematicalExpression(a * x + b)
    expr_01.set_parameter("a", 2)
    expr_01.set_parameter("b", 3)
    print(expr_01.parameters)
    print(expr_01.get_variable_names())
    print(expr_01.evaluate(x=3))

    tree = {
        "equipment": equipment,
        "data": measurement_data,
        "measurements": measurements,
        # "expression": expr_01,
        "measurement_chains": measurement_chains,
        "data_sources": sources,
        "data_processors": processors,
    }

    _write_read_buffer(tree)


def test_measurement_chain_graph():
    mc = MeasurementChainGraph(
        name="Current measurement chain",
        source_name="Current Sensor",
        source_error=Error(13.37),
        output_signal_type="analog",
        output_signal_unit="V",
    )

    mc.add_transformation(
        "AD conversion current measurement",
        error=Error(0.97),
        output_signal_type="digital",
        output_signal_unit="",
    )

    mc.add_transformation(
        "Calibration",
        error=Error(1.23),
        output_signal_type="digital",
        output_signal_unit="A",
    )
    print(mc.get_signal("Calibration"))
    print(mc.get_transformation("Calibration"))
    mc.add_signal_data("Current data", [1, 2, 3])
    print(mc.get_signal("Calibration"))
    print(mc.get_data("Current data"))
    print(mc.data_names)
    tree = {"measurement_chain": mc}
    # _write_read_buffer(tree)

    with asdf.AsdfFile(tree) as af:
        af.write_to("test.asdf")


class TestMeasurementChain:
    """Test the `MeasurementChain` class."""

    # helper functions -----------------------------------------------------------------

    @staticmethod
    def _add_missing_init_kwargs(kwargs: Dict) -> Dict:
        """Add all missing keyword arguments that are required by the `__init__` method.

        Parameters
        ----------
        kwargs :
            A dictionary containing some key word arguments that should be passed to the
            `__init__` method

        """
        default_init_kwargs = dict(
            name="name",
            source_name="source",
            source_error=Error(0.01),
            output_signal_type="analog",
            output_signal_unit="V",
        )
        for key, value in default_init_kwargs.items():
            if key not in kwargs:
                kwargs[key] = value

    @staticmethod
    def _add_missing_add_transformation_kwargs(kwargs: Dict) -> Dict:
        """Add all missing keyword arguments that are required by `add_transformation`.

        Parameters
        ----------
        kwargs :
            A dictionary containing some key word arguments that should be passed to the
            `add_transformation` method

        """
        default_add_transformation_kwargs = dict(
            name="transformation",
            error=Error(0.02),
            output_signal_type="digital",
            output_signal_unit="",
        )
        for key, value in default_add_transformation_kwargs.items():
            if key not in kwargs:
                kwargs[key] = value

    @staticmethod
    def _default_measurement_chain():
        init_kwargs = {}
        TestMeasurementChain._add_missing_init_kwargs(init_kwargs)
        tf_kwargs = {}
        TestMeasurementChain._add_missing_add_transformation_kwargs(tf_kwargs)

        mc = MeasurementChainGraph(**init_kwargs)
        mc.add_transformation(**tf_kwargs)

        return mc

    # test_init ------------------------------------------------------------------------

    @staticmethod
    @pytest.mark.parametrize(
        "kwargs",
        [
            dict(output_signal_type="analog"),
            dict(output_signal_type="digital"),
            dict(output_signal_unit="V"),
            dict(output_signal_unit="m"),
        ],
    )
    def test_init(kwargs: Dict):
        """Test the `__init__` method of the `MeasurementChain`.

        Parameters
        ----------
        kwargs:
            A dictionary with keyword arguments that are passed to the `__init__`
            method. Missing arguments are added.

        """

        TestMeasurementChain._add_missing_init_kwargs(kwargs)
        MeasurementChainGraph(**kwargs)

    # test_init_exceptions -------------------------------------------------------------

    @staticmethod
    @pytest.mark.parametrize(
        "kwargs,  exception_type, test_name",
        [(dict(output_signal_type="some type"), ValueError, "# invalid signal type")],
        ids=get_test_name,
    )
    def test_init_exceptions(kwargs: Dict, exception_type, test_name: str):
        """Test the exceptions of the `__init__` method.

        Parameters
        ----------
        kwargs :
            A dictionary with keyword arguments that are passed to the `__init__`
            method. Missing arguments are added.
        exception_type :
            The expected exception type
        test_name :
            Name of the test

        """
        TestMeasurementChain._add_missing_init_kwargs(kwargs)
        with pytest.raises(exception_type):
            MeasurementChainGraph(**kwargs)

    # test_add_transformations ---------------------------------------------------------

    @staticmethod
    @pytest.mark.parametrize(
        "kwargs",
        [
            dict(output_signal_type="analog"),
            dict(output_signal_type="digital"),
            dict(output_signal_unit="V"),
            dict(output_signal_unit="m"),
        ],
    )
    def test_add_transformation(kwargs):
        """Test the `add_transformation` method of the `MeasurementChain`.

        Parameters
        ----------
        kwargs:
            A dictionary with keyword arguments that are passed to the
            `add_transformation` method. Missing arguments are added.

        """
        init_kwargs = {}
        TestMeasurementChain._add_missing_init_kwargs(init_kwargs)
        TestMeasurementChain._add_missing_add_transformation_kwargs(kwargs)

        mc = MeasurementChainGraph(**init_kwargs)
        mc.add_transformation(**kwargs)

    # test_add_transformation_exceptions -----------------------------------------------

    @staticmethod
    @pytest.mark.parametrize(
        "kwargs,  exception_type, test_name",
        [
            (dict(output_signal_type="some type"), ValueError, "# invalid signal type"),
            (dict(input_signal_source="what"), KeyError, "# invalid signal source"),
        ],
        ids=get_test_name,
    )
    def test_add_transformation_exceptions(
        kwargs: Dict, exception_type, test_name: str
    ):
        """Test the exceptions of the `add_transformation` method.

        Parameters
        ----------
        kwargs :
            A dictionary with keyword arguments that are passed to the
            `add_transformation` method. Missing arguments are added.
        exception_type :
            The expected exception type
        test_name :
            Name of the test

        """
        init_kwargs = {}
        TestMeasurementChain._add_missing_init_kwargs(init_kwargs)
        TestMeasurementChain._add_missing_add_transformation_kwargs(kwargs)

        mc = MeasurementChainGraph(**init_kwargs)

        with pytest.raises(exception_type):
            mc.add_transformation(**kwargs)

    # test_add_signal_data -------------------------------------------------------------

    @staticmethod
    @pytest.mark.parametrize(
        "kwargs",
        [dict(data=xr.DataArray([2, 3]))],
    )
    def test_add_signal_data(kwargs):
        """Test the `add_signal_data` method of the `MeasurementChain`.

        Parameters
        ----------
        kwargs:
            A dictionary with keyword arguments that are passed to the
            `add_signal_data` method. If no name is in the kwargs, a default one is
            added.

        """
        mc = TestMeasurementChain._default_measurement_chain()

        if "name" not in kwargs:
            kwargs["name"] = "my data"

        mc.add_signal_data(**kwargs)

    # test_add_signal_data -----------------------------------------------------------------

    @staticmethod
    @pytest.mark.parametrize(
        "kwargs,  exception_type, test_name",
        [
            (dict(signal_source="what"), KeyError, "# invalid signal source"),
        ],
        ids=get_test_name,
    )
    def test_add_signal_data_exceptions(kwargs: Dict, exception_type, test_name: str):
        """Test the exceptions of the `add_signal_data` method.

        Parameters
        ----------
        kwargs :
            A dictionary with keyword arguments that are passed to the `add_signal_data`
            method. Missing arguments are added.
        exception_type :
            The expected exception type
        test_name :
            Name of the test

        """
        mc = TestMeasurementChain._default_measurement_chain()

        if "name" not in kwargs:
            kwargs["name"] = "my data"
        if "data" not in kwargs:
            kwargs["data"] = xr.DataArray([1, 2])

        with pytest.raises(exception_type):
            mc.add_signal_data(**kwargs)
