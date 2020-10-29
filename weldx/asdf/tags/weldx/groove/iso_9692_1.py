"""ISO 9692-1 welding groove type definitions"""

from dataclasses import dataclass, field
from typing import List

import pint
from asdf.tagged import tag_object

from weldx.asdf.constants import WELDX_TAG_BASE
from weldx.asdf.types import WeldxType
from weldx.asdf.utils import drop_none_attr
from weldx.asdf.validators import wx_unit_validator
from weldx.constants import WELDX_QUANTITY as Q_
from weldx.utility import ureg_check_class


class IsoBaseGroove:
    """Generic base class for all groove types."""

    def parameters(self):
        """Return groove parameters as dictionary of quantities."""
        return {k: v for k, v in self.__dict__.items() if isinstance(v, pint.Quantity)}

    def param_strings(self):
        """Generate string representation of parameters."""
        return [f"{k}={v:~}" for k, v in self.parameters().items()]


@ureg_check_class("[length]", "[length]", None)
@dataclass
class IGroove(IsoBaseGroove):
    # noinspection PyUnresolvedReferences
    """An I-Groove.

    For a detailed description of the execution look in get_groove.

    Parameters
    ----------
    t : pint.Quantity
        workpiece thickness
    b : pint.Quantity
        root gap
    code_number :
        Numbers of the standard

    """

    t: pint.Quantity
    b: pint.Quantity = Q_(0, "mm")
    code_number: List[str] = field(default_factory=lambda: ["1.2.1", "1.2.2", "2.1"])


@ureg_check_class("[length]", "[]", "[length]", "[length]", None)
@dataclass
class VGroove(IsoBaseGroove):
    # noinspection PyUnresolvedReferences
    """A Single-V Groove.

    For a detailed description of the execution look in get_groove.

    Parameters
    ----------
    t :
        workpiece thickness
    alpha :
        groove angle
    b :
        root gap
    c :
        root face
    code_number :
        Numbers of the standard

    """

    t: pint.Quantity
    alpha: pint.Quantity
    c: pint.Quantity = Q_(0, "mm")
    b: pint.Quantity = Q_(0, "mm")
    code_number: List[str] = field(default_factory=lambda: ["1.3", "1.5"])


@ureg_check_class("[length]", "[]", "[]", "[length]", "[length]", "[length]", None)
@dataclass
class VVGroove(IsoBaseGroove):
    # noinspection PyUnresolvedReferences
    """A VV-Groove.

    For a detailed description of the execution look in get_groove.

    Parameters
    ----------
    t :
        workpiece thickness
    alpha :
        groove angle
    beta :
        bevel angle
    b :
        root gap
    c :
        root face
    h :
        root face 2
    code_number :
        Numbers of the standard

    """

    t: pint.Quantity
    alpha: pint.Quantity
    beta: pint.Quantity
    h: pint.Quantity
    c: pint.Quantity = Q_(0, "mm")
    b: pint.Quantity = Q_(0, "mm")
    code_number: List[str] = field(default_factory=lambda: ["1.7"])


@ureg_check_class("[length]", "[]", "[]", "[length]", "[length]", "[length]", None)
@dataclass
class UVGroove(IsoBaseGroove):
    # noinspection PyUnresolvedReferences
    """A UV-Groove.

    For a detailed description of the execution look in get_groove.

    Parameters
    ----------
    t :
        workpiece thickness
    alpha :
        groove angle
    beta :
        bevel angle
    R :
        bevel radius
    b :
        root gap
    h :
        root face
    code_number :
        Numbers of the standard

    """

    t: pint.Quantity
    alpha: pint.Quantity
    beta: pint.Quantity
    R: pint.Quantity
    h: pint.Quantity = Q_(0, "mm")
    b: pint.Quantity = Q_(0, "mm")
    code_number: List[str] = field(default_factory=lambda: ["1.6"])


@ureg_check_class("[length]", "[]", "[length]", "[length]", "[length]", None)
@dataclass
class UGroove(IsoBaseGroove):
    # noinspection PyUnresolvedReferences
    """An U-Groove.

    For a detailed description of the execution look in get_groove.

    Parameters
    ----------
    t :
        workpiece thickness
    beta :
        bevel angle
    R :
        bevel radius
    b :
        root gap
    c :
        root face
    code_number :
        Numbers of the standard

    """

    t: pint.Quantity
    beta: pint.Quantity
    R: pint.Quantity
    c: pint.Quantity = Q_(0, "mm")
    b: pint.Quantity = Q_(0, "mm")
    code_number: List[str] = field(default_factory=lambda: ["1.8"])


@ureg_check_class("[length]", "[]", "[length]", "[length]", None)
@dataclass
class HVGroove(IsoBaseGroove):
    # noinspection PyUnresolvedReferences
    """A HV-Groove.

    For a detailed description of the execution look in get_groove.

    Parameters
    ----------
    t :
        workpiece thickness
    beta :
        bevel angle
    b :
        root gap
    c :
        root face
    code_number :
        Numbers of the standard

    """

    t: pint.Quantity
    beta: pint.Quantity
    c: pint.Quantity = Q_(0, "mm")
    b: pint.Quantity = Q_(0, "mm")
    code_number: List[str] = field(default_factory=lambda: ["1.9.1", "1.9.2", "2.8"])


@ureg_check_class("[length]", "[]", "[length]", "[length]", "[length]", None)
@dataclass
class HUGroove(IsoBaseGroove):
    # noinspection PyUnresolvedReferences
    """A HU-Groove.

    For a detailed description of the execution look in get_groove.

    Parameters
    ----------
    t :
        workpiece thickness
    beta :
        bevel angle
    R :
        bevel radius
    b :
        root gap
    c :
        root face
    code_number :
        Numbers of the standard

    """

    t: pint.Quantity
    beta: pint.Quantity
    R: pint.Quantity
    c: pint.Quantity = Q_(0, "mm")
    b: pint.Quantity = Q_(0, "mm")
    code_number: List[str] = field(default_factory=lambda: ["1.11", "2.10"])


@ureg_check_class(
    "[length]", "[]", "[]", "[length]", "[length]", "[length]", "[length]", None
)
@dataclass
class DVGroove(IsoBaseGroove):
    # noinspection PyUnresolvedReferences
    """A DV-Groove.

    For a detailed description of the execution look in get_groove.

    Parameters
    ----------
    t :
        workpiece thickness
    alpha_1 :
        groove angle (upper)
    alpha_2 :
        groove angle (lower)
    b :
        root gap
    c :
        root face (middle)
    h1 :
        root face (upper)
    h2 :
        root face (lower)
    code_number :
        Numbers of the standard

    """

    t: pint.Quantity
    alpha_1: pint.Quantity
    alpha_2: pint.Quantity
    c: pint.Quantity = Q_(0, "mm")
    h1: pint.Quantity = None
    h2: pint.Quantity = None
    b: pint.Quantity = Q_(0, "mm")
    code_number: List[str] = field(default_factory=lambda: ["2.4", "2.5.1", "2.5.2"])

    def __post_init__(self):
        if self.h1 is None and self.h2 is None:
            self.h1 = (self.t - self.c) / 2
            self.h2 = (self.t - self.c) / 2
        elif self.h1 is not None and self.h2 is None:
            self.h2 = self.h1
        elif self.h1 is None and self.h2 is not None:
            self.h1 = self.h2


@ureg_check_class(
    "[length]",
    "[]",
    "[]",
    "[length]",
    "[length]",
    "[length]",
    "[length]",
    "[length]",
    "[length]",
    None,
)
@dataclass
class DUGroove(IsoBaseGroove):
    # noinspection PyUnresolvedReferences
    """A DU-Groove

    For a detailed description of the execution look in get_groove.

    Parameters
    ----------
    t :
        workpiece thickness
    beta_1 :
        bevel angle (upper)
    beta_2 :
        bevel angle (lower)
    R :
        bevel radius (upper)
    R2 :
        bevel radius (lower)
    b :
        root gap
    c :
        root face (middle)
    h1 :
        root face (upper)
    h2 :
        root face (lower)
    code_number :
        Numbers of the standard

    """

    t: pint.Quantity
    beta_1: pint.Quantity
    beta_2: pint.Quantity
    R: pint.Quantity
    R2: pint.Quantity
    c: pint.Quantity = Q_(3, "mm")
    h1: pint.Quantity = None
    h2: pint.Quantity = None
    b: pint.Quantity = Q_(0, "mm")
    code_number: List[str] = field(default_factory=lambda: ["2.7"])

    def __post_init__(self):
        if self.h1 is None and self.h2 is None:
            self.h1 = (self.t - self.c) / 2
            self.h2 = (self.t - self.c) / 2
        elif self.h1 is not None and self.h2 is None:
            self.h2 = self.h1
        elif self.h1 is None and self.h2 is not None:
            self.h1 = self.h2


@ureg_check_class(
    "[length]", "[]", "[]", "[length]", "[length]", "[length]", "[length]", None
)
@dataclass
class DHVGroove(IsoBaseGroove):
    # noinspection PyUnresolvedReferences
    """A DHV-Groove.

    For a detailed description of the execution look in get_groove.

    Parameters
    ----------
    t :
        workpiece thickness
    beta_1 :
        bevel angle (upper)
    beta_2 :
        bevel angle (lower)
    b :
        root gap
    c :
        root face (middle)
    h1 :
        root face (upper)
    h2 :
        root face (lower)
    code_number :
        Numbers of the standard

    """

    t: pint.Quantity
    beta_1: pint.Quantity
    beta_2: pint.Quantity
    c: pint.Quantity = Q_(0, "mm")
    h1: pint.Quantity = None
    h2: pint.Quantity = None
    b: pint.Quantity = Q_(0, "mm")
    code_number: List[str] = field(default_factory=lambda: ["2.9.1", "2.9.2"])

    def __post_init__(self):
        if self.h1 is None and self.h2 is None:
            self.h1 = (self.t - self.c) / 2
            self.h2 = (self.t - self.c) / 2
        elif self.h1 is not None and self.h2 is None:
            self.h2 = self.h1
        elif self.h1 is None and self.h2 is not None:
            self.h1 = self.h2


@ureg_check_class(
    "[length]",
    "[]",
    "[]",
    "[length]",
    "[length]",
    "[length]",
    "[length]",
    "[length]",
    "[length]",
    None,
)
@dataclass
class DHUGroove(IsoBaseGroove):
    # noinspection PyUnresolvedReferences
    """A DHU-Groove.

    For a detailed description of the execution look in get_groove.

    Parameters
    ----------
    t :
        workpiece thickness
    beta_1 :
        bevel angle (upper)
    beta_2 :
        bevel angle (lower)
    R :
        bevel radius (upper)
    R2 :
        bevel radius (lower)
    b :
        root gap
    c :
        root face (middle)
    h1 :
        root face (upper)
    h2 :
        root face (lower)
    code_number :
        Numbers of the standard

    """

    t: pint.Quantity
    beta_1: pint.Quantity
    beta_2: pint.Quantity
    R: pint.Quantity
    R2: pint.Quantity
    c: pint.Quantity = Q_(0, "mm")
    h1: pint.Quantity = None
    h2: pint.Quantity = None
    b: pint.Quantity = Q_(0, "mm")
    code_number: List[str] = field(default_factory=lambda: ["2.11"])

    def __post_init__(self):
        if self.h1 is None and self.h2 is None:
            self.h1 = (self.t - self.c) / 2
            self.h2 = (self.t - self.c) / 2
        elif self.h1 is not None and self.h2 is None:
            self.h2 = self.h1
        elif self.h1 is None and self.h2 is not None:
            self.h1 = self.h2


@ureg_check_class(
    "[length]", "[length]", "[]", "[length]", "[length]", None,
)
@dataclass
class FFGroove(IsoBaseGroove):
    # noinspection PyUnresolvedReferences
    """A Frontal Face Groove.

    For a detailed description of the execution look in get_groove.

    Parameters
    ----------
    t_1 :
        workpiece thickness
    t_2 :
        workpiece thickness, if second thickness is needed
    alpha :
        groove angle
    b :
        root gap
    e :
        special depth
    code_number :
        Numbers of the standard

    """

    t_1: pint.Quantity
    t_2: pint.Quantity = None
    alpha: pint.Quantity = None
    # ["1.12", "1.13", "2.12", "3.1.1", "3.1.2", "3.1.3", "4.1.1", "4.1.2", "4.1.3"]
    code_number: str = None
    b: pint.Quantity = None
    e: pint.Quantity = None


def _get_class_from_tag(instance_tag: str):
    groove_tag = instance_tag.rpartition("/iso_9692_1/")[-1]
    return groove_tag.rpartition("-")[0]


_ISO_GROOVE_SCHEMA = "groove/iso_9692_1/"

# create class <-> name mapping
_groove_type_to_name = {cls: cls.__name__ for cls in IsoBaseGroove.__subclasses__()}
_groove_name_to_type = {cls.__name__: cls for cls in IsoBaseGroove.__subclasses__()}


def get_groove(
    groove_type: str,
    workpiece_thickness=None,
    workpiece_thickness2=None,
    root_gap=None,
    root_face=None,
    root_face2=None,
    root_face3=None,
    bevel_radius=None,
    bevel_radius2=None,
    bevel_angle=None,
    bevel_angle2=None,
    groove_angle=None,
    groove_angle2=None,
    special_depth=None,
    code_number=None,
):
    # get list of function parameters
    _loc = locals()

    _mapping = {
        "VGroove": {
            "t": "workpiece_thickness",
            "alpha": "groove_angle",
            "b": "root_gap",
            "c": "root_face",
        }
    }

    groove_cls = _groove_name_to_type[groove_type]

    # convert function arguments to groove arguments
    args = {k: _loc[v] for k, v in _mapping[groove_type].items() if _loc[v] is not None}

    return groove_cls(**args)


class IsoGrooveType(WeldxType):
    """ASDF Groove type."""

    name = [_ISO_GROOVE_SCHEMA + g for g in _groove_name_to_type.keys()]
    version = "1.0.0"
    types = [IsoBaseGroove]
    requires = ["weldx"]
    validators = {"wx_unit": wx_unit_validator}

    @classmethod
    def to_tree(cls, node: IsoBaseGroove, ctx):
        """Convert tree and remove all None entries from node dictionary."""
        tree = drop_none_attr(node)
        return tree

    @classmethod
    def to_tree_tagged(cls, node: IsoBaseGroove, ctx):
        """Serialize tree with custom tag definition."""
        tree = cls.to_tree(node, ctx)
        tag = (
            WELDX_TAG_BASE
            + "/"
            + _ISO_GROOVE_SCHEMA
            + type(node).__name__
            + "-"
            + str(cls.version)
        )
        return tag_object(tag, tree, ctx=ctx)

    @classmethod
    def from_tree_tagged(cls, tree, ctx):
        """Convert from tagged tree to a groove."""
        groove_name = _get_class_from_tag(tree._tag)
        groove = _groove_name_to_type[groove_name](**tree)
        return groove
