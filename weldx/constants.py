"""Define constants for global library use."""

from pint import UnitRegistry

WELDX_UNIT_REGISTRY = UnitRegistry(
    preprocessors=[
        lambda string: string.replace("%", "percent")
    ],  # allow use of %-sign
    force_ndarray_like=False,
    auto_reduce_dimensions=True,
)
WELDX_QUANTITY = WELDX_UNIT_REGISTRY.Quantity

# add percent unit
WELDX_UNIT_REGISTRY.define("percent = 0.01*count = %")
# swap plank constant for hour definition
WELDX_UNIT_REGISTRY.define("hour = 60*minute = h = hr")
