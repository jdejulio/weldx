from weldx.asdf.types import WeldxType
from weldx.asdf.utils import drop_none_attr
from weldx.measurement import Source

__all__ = ["Source", "SourceType"]


class SourceType(WeldxType):
    """Serialization class for measurement sources."""

    name = "measurement/source"
    version = "1.0.0"
    types = [Source]
    requires = ["weldx"]
    handle_dynamic_subclasses = True

    @classmethod
    def to_tree(cls, node: Source, ctx):
        """convert to tagged tree and remove all None entries from node dictionary"""
        tree = drop_none_attr(node)
        return tree

    @classmethod
    def from_tree(cls, tree, ctx):
        obj = Source(**tree)
        return obj
