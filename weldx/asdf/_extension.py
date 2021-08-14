"""Legacy asdf extension code."""

from asdf.extension import AsdfExtension, BuiltinExtension

from weldx.asdf.constants import (
    WELDX_SCHEMA_URI_BASE,
    WELDX_TAG_BASE,
    WELDX_URL_MAPPING,
)
from weldx.asdf.validators import (
    wx_property_tag_validator,
    wx_shape_validator,
    wx_unit_validator,
)

from ._types import WeldxType, _weldx_asdf_types, _weldx_types


class WeldxLegacyValidatorType(WeldxType):
    """Dummy class to register weldx validators using legacy asdf API."""

    name = "legacy/validators"
    version = "1.0.0"
    types = []
    validators = {
        "wx_property_tag": wx_property_tag_validator,
        "wx_unit": wx_unit_validator,
        "wx_shape": wx_shape_validator,
    }


class WeldxLegacyExtension(AsdfExtension):
    """Extension class registering types with both tags and schemas defined by weldx."""

    @property
    def types(self):
        # There are no types yet!
        return _weldx_types

    @property
    def tag_mapping(self):
        return [(WELDX_TAG_BASE, WELDX_SCHEMA_URI_BASE + "{tag_suffix}")]

    @property
    def url_mapping(self):
        return WELDX_URL_MAPPING

    @property
    def yaml_tag_handles(self):
        return {"!weldx!": "asdf://weldx.bam.de/weldx/tags/"}


class WeldxLegacyAsdfExtension(BuiltinExtension):
    """This extension is used to register custom tag types that have schemas defined
    by ASDF, but have tag implementations defined in the weldx package

    """

    @property
    def types(self):
        return _weldx_asdf_types
