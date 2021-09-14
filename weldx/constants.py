"""Define constants for global library use."""
from pathlib import Path as _Path

from pint import UnitRegistry as _ureg

WELDX_PATH = _Path(__file__).parent.resolve()

WELDX_UNIT_REGISTRY = _ureg(
    preprocessors=[lambda string: string.replace("%", "percent")],  # allow %-sign
    force_ndarray_like=True,
)

# add percent unit
WELDX_UNIT_REGISTRY.define("percent = 0.01*count = %")
# swap plank constant for hour definition
WELDX_UNIT_REGISTRY.define("hour = 60*minute = h = hr")

WELDX_QUANTITY = WELDX_UNIT_REGISTRY.Quantity
Q_ = WELDX_QUANTITY
U_ = WELDX_UNIT_REGISTRY.Unit

__all__ = (
    "WELDX_PATH",
    "WELDX_QUANTITY",
    "WELDX_UNIT_REGISTRY",
    "Q_",
    "U_",
)
