import pandas as pd

from weldx.asdf.types import WeldxConverter

__all__ = ["TimedeltaConverter"]


class TimedeltaConverter(WeldxConverter):
    """A simple implementation of serializing a single pandas Timedelta."""

    tags = ["asdf://weldx.bam.de/weldx/tags/time/timedelta-1.*"]
    types = [pd.Timedelta]

    def to_yaml_tree(self, obj: pd.Timedelta, tag, ctx):
        """Serialize timedelta to tree."""
        return dict(value=obj.isoformat())

    def from_yaml_tree(self, node, tag, ctx):
        """Construct timedelta from tree."""
        return pd.Timedelta(node["value"])
