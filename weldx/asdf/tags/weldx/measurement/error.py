from weldx.asdf.types import WeldxType
from weldx.asdf.utils import drop_none_attr
from weldx.measurement import Error

__all__ = ["Error", "ErrorType"]


class ErrorType(WeldxType):
    """<TODO ASDF TYPE DOCSTRING>"""

    name = "measurement/error"
    version = "1.0.0"
    types = [Error]
    requires = ["weldx"]
    handle_dynamic_subclasses = True

    @classmethod
    def to_tree(cls, node: Error, ctx):
        """convert to tagged tree and remove all None entries from node dictionary"""
        tree = drop_none_attr(node)
        return tree

    @classmethod
    def from_tree(cls, tree, ctx):
        obj = Error(**tree)
        return obj
