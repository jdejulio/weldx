"""Serialization for xarray.DataArray."""
from typing import List

from asdf.tagged import TaggedDict
from xarray import DataArray

import weldx.tags.core.common_types as ct
from weldx.asdf.types import WeldxConverter
from weldx.asdf.util import _get_instance_shape


class XarrayDataArrayConverter(WeldxConverter):
    """Serialization class for xarray.DataArray."""

    name = "core/data_array"
    version = "0.1.0"
    types = [DataArray]

    def to_yaml_tree(self, obj: DataArray, tag: str, ctx) -> dict:
        """Convert to python dict."""
        attributes = obj.attrs
        coordinates = [
            ct.Variable(name, coord_data.dims, coord_data.data, attrs=coord_data.attrs)
            for name, coord_data in obj.coords.items()
        ]
        data = ct.Variable("data", obj.dims, obj.data, attrs={})

        tree = {
            "attributes": attributes,
            "coordinates": coordinates,
            "data": data,
        }

        return tree

    def from_yaml_tree(self, node: dict, tag: str, ctx):
        """Convert basic types representing YAML trees into an `xarray.DataArray`."""
        data = node["data"].data
        dims = node["data"].dimensions
        coords = {c.name: (c.dimensions, c.data, c.attrs) for c in node["coordinates"]}
        attrs = node["attributes"]

        da = DataArray(data=data, coords=coords, dims=dims, attrs=attrs)

        return da

    @staticmethod
    def shape_from_tagged(node: TaggedDict) -> List[int]:
        """Calculate the shape from static tagged tree instance."""
        return _get_instance_shape(node["data"]["data"])
