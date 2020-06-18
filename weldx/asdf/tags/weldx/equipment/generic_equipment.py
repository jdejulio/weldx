from weldx.asdf.types import WeldxType
from weldx.asdf.utils import drop_none_attr
from weldx.measurement import GenericEquipment

__all__ = ["GenericEquipment", "GenericEquipmentType"]


class GenericEquipmentType(WeldxType):
    """<TODO ASDF TYPE DOCSTRING>"""

    name = "equipment/generic_equipment"
    version = "1.0.0"
    types = [GenericEquipment]
    requires = ["weldx"]
    handle_dynamic_subclasses = True

    @classmethod
    def to_tree(cls, node: GenericEquipment, ctx):
        """convert to tagged tree and remove all None entries from node dictionary"""
        tree = drop_none_attr(node)
        return tree

    @classmethod
    def from_tree(cls, tree, ctx):
        if "sources" not in tree:
            tree["sources"] = None
        obj = GenericEquipment(**tree)
        return obj
