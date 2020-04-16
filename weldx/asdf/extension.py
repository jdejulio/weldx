# Licensed under a 3-clause BSD style license - see LICENSE
# -*- coding: utf-8 -*-

from asdf.extension import AsdfExtension, BuiltinExtension
from weldx.asdf.constants import WELDX_SCHEMA_URI_BASE, WELDX_URL_MAPPING

# Make sure that all tag implementations are imported by the time we create
# the extension class so that _weldx_asdf_types is populated correctly. We
# could do this using __init__ files, except it causes pytest import errors in
# the case that asdf is not installed.

# unit -----------------------------------------------------------------
from .tags.weldx.unit.pint_quantity import *  # noqa: F401,F403

# time -----------------------------------------------------------------
from .tags.weldx.time.timedelta import TimedeltaType  # noqa: F401,F403
from .tags.weldx.time.timedeltaindex import TimedeltaIndexType  # noqa: F401,F403
from .tags.weldx.time.timestamp import TimestampType  # noqa: F401,F403
from .tags.weldx.time.datetimeindex import DatetimeIndexType  # noqa: F401,F403

# welding process -----------------------------------------------------------------
from .tags.weldx.aws.process.gas_component import *  # noqa: F401,F403
from .tags.weldx.aws.process.shielding_gas_type import *  # noqa: F401,F403
from .tags.weldx.aws.process.shielding_gas_for_procedure import *  # noqa: F401,F403

# weld design -----------------------------------------------------------------
from .tags.weldx.aws.design.joint_penetration import *  # noqa: F401,F403
from .tags.weldx.aws.design.weld_details import *  # noqa: F401,F403
from .tags.weldx.aws.design.connection import *  # noqa: F401,F403
from .tags.weldx.aws.design.workpiece import *  # noqa: F401,F403
from .tags.weldx.aws.design.sub_assembly import *  # noqa: F401,F403
from .tags.weldx.aws.design.weldment import *  # noqa: F401,F403
from .tags.weldx.aws.design.base_metal import *  # noqa: F401,F403
from .tags.weldx.core.groove import *  # noqa: F401,F403

from .types import _weldx_types, _weldx_asdf_types

__all__ = ["WeldxExtension", "WeldxAsdfExtension"]


# This extension is used to register custom types that have both tags and
# schemas defined by weldx.
class WeldxExtension(AsdfExtension):
    @property
    def types(self):
        # There are no types yet!
        return _weldx_types

    @property
    def tag_mapping(self):
        return [("tag:weldx.bam.de:weldx", WELDX_SCHEMA_URI_BASE + "weldx{tag_suffix}")]

    @property
    def url_mapping(self):
        return WELDX_URL_MAPPING


# This extension is used to register custom tag types that have schemas defined
# by ASDF, but have tag implementations defined in the weldx package
class WeldxAsdfExtension(BuiltinExtension):
    @property
    def types(self):
        return _weldx_asdf_types
