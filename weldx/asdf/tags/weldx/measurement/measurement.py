from weldx.asdf.types import WeldxType
from weldx.asdf.utils import drop_none_attr
from weldx.measurement import Measurement

__all__ = ["Measurement", "MeasurementType"]


class MeasurementType(WeldxType):
    """Serialization class for measurement objects."""

    name = "measurement/measurement"
    version = "1.0.0"
    types = [Measurement]
    requires = ["weldx"]
    handle_dynamic_subclasses = True

    @classmethod
    def to_tree(cls, node: Measurement, ctx):
        """convert to tagged tree and remove all None entries from node dictionary"""
        tree = drop_none_attr(node)
        return tree

    @classmethod
    def from_tree(cls, tree, ctx):
        obj = Measurement(**tree)
        return obj
