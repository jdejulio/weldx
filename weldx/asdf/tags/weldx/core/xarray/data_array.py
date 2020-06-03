from xarray import DataArray

from weldx.asdf.types import WeldxType


class XarrayDataArrayASDF(WeldxType):
    """Serialization class for xarray.DataArray"""

    name = "core/xarray/data_array"
    version = "1.0.0"
    types = [DataArray]
    requires = ["weldx"]
    handle_dynamic_subclasses = True

    @classmethod
    def to_tree(cls, node: DataArray, ctx):
        """Convert an xarray.DataArray to a tagged tree"""
        tree = node.to_dict(data=False)
        tree["data"] = node.data

        # remove obsolete fields
        del tree["dtype"]
        del tree["shape"]
        for coord in node.coords:
            tree["coords"][coord]["data"] = node.coords[coord].data
            del tree["coords"][coord]["dtype"]
            del tree["coords"][coord]["shape"]

        return tree

    @classmethod
    def from_tree(cls, tree, ctx):
        """Convert a tagged tree to an xarray.DataArray"""
        obj = DataArray.from_dict(tree)
        return obj
