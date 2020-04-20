import warnings

# asdf extensions and tags
import weldx.asdf

# geometry packages
import weldx.geometry
import weldx.transformations
import weldx.utility

# versioneer
from ._version import get_versions
from .constants import WELDX_QUANTITY as Q_

__all__ = ["geometry", "transformations", "utility", "asdf", "Q_"]


with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    Q_([])

__version__ = get_versions()["version"]
del get_versions
