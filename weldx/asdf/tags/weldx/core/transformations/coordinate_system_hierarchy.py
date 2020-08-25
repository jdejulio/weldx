from copy import deepcopy
from dataclasses import dataclass
from typing import Dict, List, Tuple

from weldx.asdf.types import WeldxType
from weldx.transformations import CoordinateSystemManager, LocalCoordinateSystem


@dataclass
class CoordinateTransformation:
    """Stores data of a coordinate transformation."""

    name: str
    reference_system: str
    transformation: LocalCoordinateSystem


class CoordinateTransformationASDF(WeldxType):
    """Serialization class for CoordinateTransformation"""

    name = "core/transformations/coordinate_transformation"
    version = "1.0.0"
    types = [CoordinateTransformation]
    requires = ["weldx"]
    handle_dynamic_subclasses = True
    validators = {}

    @classmethod
    def to_tree(cls, node: CoordinateTransformation, ctx):
        """
        Convert a 'CoordinateTransformation' instance into YAML representations.

        Parameters
        ----------
        node :
            Instance of the 'CoordinateTransformation' type to be serialized.

        ctx :
            An instance of the 'AsdfFile' object that is being written out.

        Returns
        -------
            A basic YAML type ('dict', 'list', 'str', 'int', 'float', or
            'complex') representing the properties of the 'CoordinateTransformation'
            type to be serialized.

        """
        tree = {
            "name": node.name,
            "reference_system": node.reference_system,
            "transformation": node.transformation,
        }
        return tree

    @classmethod
    def from_tree(cls, tree, ctx):
        """
        Converts basic types representing YAML trees into a 'CoordinateTransformation'.

        Parameters
        ----------
        tree :
            An instance of a basic Python type (possibly nested) that
            corresponds to a YAML subtree.
        ctx :
            An instance of the 'AsdfFile' object that is being constructed.

        Returns
        -------
        CoordinateTransformation :
            An instance of the 'CoordinateTransformation' type.

        """
        return CoordinateTransformation(
            name=tree["name"],
            reference_system=tree["reference_system"],
            transformation=tree["transformation"],
        )


class LocalCoordinateSystemASDF(WeldxType):
    """Serialization class for weldx.transformations.LocalCoordinateSystem"""

    name = "core/transformations/coordinate_system_hierarchy"
    version = "1.0.0"
    types = [CoordinateSystemManager]
    requires = ["weldx"]
    handle_dynamic_subclasses = True
    validators = {}

    @classmethod
    def _extract_all_subsystems(
        cls, csm: CoordinateSystemManager, _recursive_call: bool = False
    ) -> List[Tuple[CoordinateSystemManager, str]]:
        """Return a list of all subsystems and their corresponding parent names.

        This function extracts all subsystems and nested subsystems of the passed
        coordinate system manager instance. Each subsystem is stored inside a tuple
        together with the parent systems' name.

        Parameters
        ----------
        csm:
            Coordinate system manager instance
        _recursive_call:
            Specifies if the current function call happened recursively

        Returns
        -------
        List[Tuple[CoordinateSystemManager, str]]:
            List of subsystems and their parent names

        """
        if not _recursive_call:
            csm = deepcopy(csm)

        subsystems = csm.unmerge()

        subsystems = [(subsystem, csm.name) for subsystem in subsystems]
        for subsystem, _ in subsystems:
            if subsystem.number_of_subsystems > 0:
                subsystems += cls._extract_all_subsystems(subsystem, True)

        return subsystems

    @classmethod
    def _extract_subsystem_data(cls, csm: CoordinateSystemManager) -> List[Dict]:
        """Get the subsystem data of a CoordinateSystemManager instance.

        Parameters
        ----------
        csm:
            CoordinateSystemManager instance.

        Returns
        -------

        """
        subsystems = cls._extract_all_subsystems(csm)
        subsystem_data = []
        for subsystem, parent in subsystems:
            subsystem_data += [
                {
                    "name": subsystem.name,
                    "root_cs": subsystem.root_system_name,
                    "parent_system": parent,
                    "members": subsystem.get_coordinate_system_names(),
                }
            ]
        return subsystem_data

    @classmethod
    def to_tree(cls, node: CoordinateSystemManager, ctx):
        """
        Convert a 'CoordinateSystemManager' instance into YAML representations.

        Parameters
        ----------
        node :
            Instance of the 'CoordinateSystemManager' type to be serialized.

        ctx :
            An instance of the 'AsdfFile' object that is being written out.

        Returns
        -------
            A basic YAML type ('dict', 'list', 'str', 'int', 'float', or
            'complex') representing the properties of the 'CoordinateSystemManager'
            type to be serialized.

        """
        graph = deepcopy(node.graph)  # TODO: Check if deepcopy is necessary

        # remove automatically computed edges (inverted directions)
        remove_edges = []
        for edge in graph.edges:
            if not graph.edges[edge]["defined"]:
                remove_edges.append(edge)
        graph.remove_edges_from(remove_edges)

        # find root coordinate system
        root_system_name = None
        for graph_node in graph.nodes:
            if graph.out_degree(graph_node) == 0:
                root_system_name = graph_node
                break

        coordinate_system_data = []

        for name, reference_system in graph.edges:
            transformation = CoordinateTransformation(
                name,
                reference_system,
                node.get_local_coordinate_system(name, reference_system),
            )
            coordinate_system_data.append(transformation)

        subsystems = cls._extract_subsystem_data(node)

        tree = {
            "name": node.name,
            "subsystems": subsystems,
            "root_system_name": root_system_name,
            "coordinate_systems": coordinate_system_data,
        }
        return tree

    @classmethod
    def from_tree(cls, tree, ctx):
        """
        Converts basic types representing YAML trees into a 'CoordinateSystemManager'.

        Parameters
        ----------
        tree :
            An instance of a basic Python type (possibly nested) that
            corresponds to a YAML subtree.
        ctx :
            An instance of the 'AsdfFile' object that is being constructed.

        Returns
        -------
        CoordinateSystemManager :
            An instance of the 'CoordinateSystemManager' type.

        """
        csm = CoordinateSystemManager(
            root_coordinate_system_name=tree["root_system_name"],
            coordinate_system_manager_name=tree["name"],
        )

        coordinate_systems = tree["coordinate_systems"]

        all_systems_included = False
        while not all_systems_included:
            all_systems_included = True
            for cs_data in coordinate_systems:
                if not csm.has_coordinate_system(cs_data.name):
                    if csm.has_coordinate_system(cs_data.reference_system):
                        csm.add_cs(
                            cs_data.name,
                            cs_data.reference_system,
                            cs_data.transformation,
                        )
                    else:  # pragma: no cover
                        all_systems_included = False  # TODO: test as soon as possible
        return csm
