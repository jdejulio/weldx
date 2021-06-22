from weldx.asdf.util import dataclass_serialization_class
from weldx.geometry import SpatialData


def to_tree_mod(tree):
    tree["coordinates"] = tree["coordinates"].data
    return tree


SpatialDataTypeASDF = dataclass_serialization_class(
    class_type=SpatialData,
    class_name="core/geometry/spatial_data",
    version="1.0.0",
    to_tree_mod=to_tree_mod,
)
