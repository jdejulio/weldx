from dataclasses import dataclass
from typing import List  # noqa: F401
from asdf import yamlutil
from weldx.asdf.types import WeldxType


@dataclass
class BaseMetal:
    """<CLASS DOCSTRING>"""

    common_name: str
    m_number: str = None
    group_number: str = None
    product_form: str
    thickness: float
    diameter: float = None
    specification_number: str = None
    specification_version: str = None
    specification_organization: str = None
    UNS_number: str = None
    CAS_number: str = None
    heat_lot_identification: str = None
    composition: str = None
    manufacturing_history: str = None
    service_history: str = None
    applied_coating_specification: str = None


class BaseMetalType(WeldxType):
    """<ASDF TYPE DOCSTRING>"""

    name = "aws/design/base_metal"
    version = "1.0.0"
    types = [BaseMetal]
    requires = ["weldx"]
    handle_dynamic_subclasses = True

    @classmethod
    def to_tree(cls, node, ctx):
        # convert to tagged tree
        tree_full = dict(
            common_name=yamlutil.custom_tree_to_tagged_tree(node.common_name, ctx),
            m_number=yamlutil.custom_tree_to_tagged_tree(node.m_number, ctx),
            group_number=yamlutil.custom_tree_to_tagged_tree(node.group_number, ctx),
            product_form=yamlutil.custom_tree_to_tagged_tree(node.product_form, ctx),
            thickness=yamlutil.custom_tree_to_tagged_tree(node.thickness, ctx),
            diameter=yamlutil.custom_tree_to_tagged_tree(node.diameter, ctx),
            specification_number=yamlutil.custom_tree_to_tagged_tree(
                node.specification_number, ctx
            ),
            specification_version=yamlutil.custom_tree_to_tagged_tree(
                node.specification_version, ctx
            ),
            specification_organization=yamlutil.custom_tree_to_tagged_tree(
                node.specification_organization, ctx
            ),
            UNS_number=yamlutil.custom_tree_to_tagged_tree(node.UNS_number, ctx),
            CAS_number=yamlutil.custom_tree_to_tagged_tree(node.CAS_number, ctx),
            heat_lot_identification=yamlutil.custom_tree_to_tagged_tree(
                node.heat_lot_identification, ctx
            ),
            composition=yamlutil.custom_tree_to_tagged_tree(node.composition, ctx),
            manufacturing_history=yamlutil.custom_tree_to_tagged_tree(
                node.manufacturing_history, ctx
            ),
            service_history=yamlutil.custom_tree_to_tagged_tree(
                node.service_history, ctx
            ),
            applied_coating_specification=yamlutil.custom_tree_to_tagged_tree(
                node.applied_coating_specification, ctx
            ),
        )

        # drop None values
        tree = {k: v for (k, v) in tree_full.items() if v is not None}
        return tree

    @classmethod
    def from_tree(cls, tree, ctx):
        obj = BaseMetal(**tree)
        return obj
