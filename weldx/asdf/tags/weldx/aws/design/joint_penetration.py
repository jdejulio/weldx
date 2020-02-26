from dataclasses import dataclass
from typing import List  # noqa: F401
from asdf import yamlutil
from weldx.asdf.types import WeldxType


@dataclass
class JointPenetration:
    """<CLASS DOCSTRING>"""

    complete_or_partial: str
    units: str
    root_penetration: float
    groove_weld_size: float = None
    incomplete_joint_penetration: float = None
    weld_size: float = None
    weld_size_E1: float = None
    weld_size_E2: float = None
    depth_of_fusion: float = None


class JointPenetrationType(WeldxType):
    """<ASDF TYPE DOCSTRING>"""

    name = "aws/design/joint_penetration"
    version = "1.0.0"
    types = [JointPenetration]
    requires = ["weldx"]
    handle_dynamic_subclasses = True

    @classmethod
    def to_tree(cls, node, ctx):
        # convert to tagged tree
        tree_full = dict(
            complete_or_partial=yamlutil.custom_tree_to_tagged_tree(
                node.complete_or_partial, ctx
            ),
            units=yamlutil.custom_tree_to_tagged_tree(node.units, ctx),
            root_penetration=yamlutil.custom_tree_to_tagged_tree(
                node.root_penetration, ctx
            ),
            groove_weld_size=yamlutil.custom_tree_to_tagged_tree(
                node.groove_weld_size, ctx
            ),
            incomplete_joint_penetration=yamlutil.custom_tree_to_tagged_tree(
                node.incomplete_joint_penetration, ctx
            ),
            weld_size=yamlutil.custom_tree_to_tagged_tree(node.weld_size, ctx),
            weld_size_E1=yamlutil.custom_tree_to_tagged_tree(node.weld_size_E1, ctx),
            weld_size_E2=yamlutil.custom_tree_to_tagged_tree(node.weld_size_E2, ctx),
            depth_of_fusion=yamlutil.custom_tree_to_tagged_tree(
                node.depth_of_fusion, ctx
            ),
        )

        # drop None values
        tree = {k: v for (k, v) in tree_full.items() if v is not None}
        return tree

    @classmethod
    def from_tree(cls, tree, ctx):
        obj = JointPenetration(**tree)
        return obj
