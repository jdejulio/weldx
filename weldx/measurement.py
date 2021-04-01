"""Contains measurement related classes and functions."""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, List, Tuple, Union  # noqa: F401

import xarray as xr
from numpy import signedinteger

if TYPE_CHECKING:  # pragma: no cover
    from networkx import DiGraph

    from weldx.core import MathematicalExpression, TimeSeries


# measurement --------------------------------------------------------------------------
@dataclass
class Data:
    """Simple dataclass implementation for measurement data."""

    name: str
    data: xr.DataArray  # skipcq: PTC-W0052


@dataclass
class Error:
    """Simple dataclass implementation for signal transformation errors."""

    deviation: float


@dataclass
class Signal:
    """Simple dataclass implementation for measurement signals."""

    signal_type: str
    unit: str
    data_name: str = None
    data: Union[Data, None] = None


@dataclass
class DataTransformation:
    """Simple dataclass implementation for signal transformations."""

    name: str
    input_signal: Signal
    output_signal: Signal
    error: Error
    func: str = None
    meta: str = None


@dataclass
class SignalTransformation:
    name: str
    error: Error
    input_signal: Signal
    output_signal: Signal
    func: "MathematicalExpression" = None
    input_shape: Tuple = None
    output_shape: Tuple = None


@dataclass
class Source:
    """Simple dataclass implementation for signal sources."""

    name: str
    output_signal: Signal
    error: Error


# DRAFT SECTION START ##################################################################

# todo: - remove data from signal
#       - factory for transformations?
#       - remove signals from transformation? -> defined by edge
#       - which classes can be removed? -> Data
#       - tutorial


class MeasurementChainGraph:
    """Simple dataclass implementation for measurement chains."""

    def __init__(
        self,
        name: str,
        source_name: str,
        source_error: Error,
        output_signal_type: str,
        output_signal_unit: str,
    ):
        """Create a new measurement chain.

        Parameters
        ----------
        name:
            Name of the measurement chain
        source_name :
            Name of the source
        source_error :
            The error of the source
        output_signal_type :
            Type of the source's output signal (analog or digital)
        output_signal_unit :
            The unit of the source's output signal

        """
        from networkx import DiGraph

        self._raise_if_invalid_signal_type(output_signal_type)

        self._name = name
        self._source = {"name": source_name, "error": source_error}
        self._prev_added_signal = None

        self._graph = DiGraph()
        self._add_signal(
            node_id=source_name, signal_type=output_signal_type, unit=output_signal_unit
        )

    @staticmethod
    def construct_from_tree(tree: Dict) -> "MeasurementChainGraph":
        mc = MeasurementChainGraph(
            name=tree["name"],
            source_name="source",
            source_error=Error(1),
            output_signal_type="analog",
            output_signal_unit="V",
        )
        # todo: implement correct version, when schema is ready
        return mc

    def _add_signal(self, node_id: str, signal_type: str, unit: str):
        """Add a new signal node to internal graph.

        Parameters
        ----------
        node_id :
            The name that will be used for the internal graphs' node. This is identical
            to the name of the signals source.
        signal_type :
            Type of the signal (analog or digital)
        unit :
            Unit of the signal

        """
        self._raise_if_node_exist(node_id)
        self._raise_if_invalid_signal_type(signal_type)

        self._graph.add_node(node_id, signal_type=signal_type, unit=unit)
        self._prev_added_signal = node_id

    def _raise_if_node_exist(self, node_id: str):
        """Raise en error if the graph already contains a node with the passed id.

        Parameters
        ----------
        node_id :
            Name that should be checked

        """
        if node_id in self._graph.nodes:
            raise KeyError(
                f"The internal graph already contains a node with the id {node_id}"
            )

    def _raise_if_invalid_signal_type(self, signal_type: str):
        """Raise an error if the passed signal type is invalid.

        Parameters
        ----------
        signal_type :
            The signal type

        """
        if signal_type not in ["analog", "digital"]:
            raise ValueError(f"{signal_type} is an invalid signal type.")

    def _raise_if_data_exist(self, name: str):
        """Raise an error if a data set with the passed name already exists

        Parameters
        ----------
        name :
            Name that should be searched for

        """
        for _, attr in self._graph.nodes.items():
            if "data_name" in attr and attr["data_name"] == name:
                raise ValueError(
                    "The measurement chain already contains a data set with the name "
                    f"'{name}'."
                )

    def _check_and_get_node_name(self, node_name: str) -> str:
        """Check if a node is part of the internal graph and return its name.

        If no name is provided, the name of the last added node is returned.

        Parameters
        ----------
        node_name :
            Name of the node that should be checked.

        """
        if node_name is None:
            return self._prev_added_signal
        elif node_name not in self._graph.nodes:
            raise ValueError(f"No signal with source '{node_name}' found")
        return node_name

    def add_transformation(
        self,
        name: str,
        error: Error,
        output_signal_type: str,
        output_signal_unit: str,
        func: "MathematicalExpression" = None,
        input_signal_source: str = None,
    ):
        """Add transformation to the measurement chain.

        Parameters
        ----------
        name :
            Name of the transformation
        error :
            The error of the transformation
        output_signal_type :
            Type of the output signal (analog or digital)
        output_signal_unit :
            Unit of the output signal
        func :
            A function describing the transformation
        input_signal_source :
            The source of the signal that should be used as input of the transformation.
            If `None` is provided, the name of the last added transformation (or the
            source, if no transformation was added to the chain) is used.

        """
        input_signal_source = self._check_and_get_node_name(input_signal_source)

        self._add_signal(
            node_id=name, signal_type=output_signal_type, unit=output_signal_unit
        )
        self._graph.add_edge(input_signal_source, name, error=error, func=func)

    def add_signal_data(self, name: str, data: "TimeSeries", signal_source: str = None):
        """Add data to a signal.

        Parameters
        ----------
        name :
            Name of the data
        data :
            The data that should be added
        signal_source :
            The source of the signal that the data should be attached to.
            If `None` is provided, the name of the last added transformation (or the
            source, if no transformation was added to the chain) is used.

        """
        self._raise_if_data_exist(name)

        signal_source = self._check_and_get_node_name(signal_source)
        signal = self._graph.nodes[signal_source]

        signal["data_name"] = name
        signal["data"] = data

    def attach_transformation(
        self, transformation: SignalTransformation, input_signal_source: str = None
    ):
        """Add a transformation from an `SignalTransformation` instance.

        Parameters
        ----------
        transformation :
            The class containing the transformation data.
        input_signal_source :
            The source of the signal that should be used as input of the transformation.
            If `None` is provided, the name of the last added transformation (or the
            source, if no transformation was added to the chain) is used.

        """
        if input_signal_source is None:
            input_signal_source = self._prev_added_signal

        source_node = self._graph.nodes[input_signal_source]
        if (
            transformation.input_signal.signal_type != source_node["signal_type"]
            or transformation.input_signal.unit != source_node["unit"]
        ):
            raise ValueError(
                f"The provided transformations input signal is incompatible to the "
                f"output signal of {input_signal_source}:\n"
                f"transformation: {transformation.input_signal.signal_type} in ["
                f"{transformation.input_signal.unit}]\n"
                f"output signal : {source_node['signal_type']} in ["
                f"{source_node['unit']}]"
            )

        self.add_transformation(
            transformation.name,
            transformation.error,
            transformation.output_signal.signal_type,
            transformation.output_signal.unit,
            transformation.func,
            input_signal_source,
        )

    def get_data(self, name: str) -> xr.DataArray:
        """

        Parameters
        ----------
        name :
            Name of the data that should be returned

        Returns
        -------
        xarray.DataArray :
            The requested data

        """
        for _, attr in self._graph.nodes.items():
            data_name = attr.get("data_name")
            if data_name is not None and data_name == name:
                return attr["data"]
        raise ValueError(f"No data with name {name} found")

    @property
    def data_names(self) -> List[str]:
        """Get the names of all attached data sets.

        Returns
        -------
        List[str] :
            List of the names from all attached data sets

        """
        return [
            attr["data_name"]
            for _, attr in self._graph.nodes.items()
            if "data_name" in attr
        ]

    def get_signal(self, signal_source: str) -> Signal:
        """Get a signal.

        Parameters
        ----------
        signal_source :
            Name of the signals source.

        Returns
        -------
        Signal :
            The requested signal

        """
        if signal_source not in self._graph.nodes:
            raise ValueError(f"No signal with source '{signal_source}' found")
        return Signal(**self._graph.nodes[signal_source])

    def get_transformation(self, name: str) -> SignalTransformation:
        """Get a transformation.

        Parameters
        ----------
        name :
            Name of the transformation

        Returns
        -------
        SignalTransformation :
            The requested transformation

        """
        for edge in self._graph.edges:
            if edge[1] == name:
                node_in = self._graph.nodes[edge[0]]
                node_out = self._graph.nodes[edge[1]]

                return SignalTransformation(
                    name=name,
                    input_signal=Signal(node_in["signal_type"], node_in["unit"]),
                    output_signal=Signal(node_out["signal_type"], node_out["unit"]),
                    **self._graph.edges[edge],
                )

        raise ValueError(f"No transformation with name '{name}' found")


# DRAFT SECTION END ####################################################################


@dataclass
class MeasurementChain:
    """Simple dataclass implementation for measurement chains."""

    name: str
    data_source: Source
    data_processors: List = field(default_factory=lambda: [])

    @staticmethod
    def _add_node(
        node: str,
        parent_node: str,
        node_label: str,
        position: Tuple[float, float],
        container: Tuple["DiGraph", List, Dict, Dict],
    ):  # pragma: no cover
        """Add a new node to several containers.

        This is a helper for the plot function.

        Parameters
        ----------
        node :
            Name of the new node
        parent_node :
            Name of the parent node
        node_label :
            Displayed name of the node
        position :
            Position of the node
        container :
            Tuple of containers that should be updated.

        """
        [graph, node_list, labels, positions] = container
        graph.add_node(node)
        node_list.append(node)
        labels[node] = node_label
        positions[node] = position
        if parent_node is not None:
            graph.add_edge(parent_node, node)

    def plot(self, axes=None):  # pragma: no cover
        """Plot the measurement chain.

        Parameters
        ----------
        axes :
            Matplotlib axes object that should be drawn to. If None is provided, this
            function will create one.

        Returns
        -------
        matplotlib.axes.Axes
            The matplotlib axes object the graph has been drawn to

        """
        import matplotlib.pyplot as plt
        from networkx import DiGraph, draw, draw_networkx_edge_labels

        def _signal_label(signal):
            return f"{signal.signal_type}\n[{signal.unit}]"

        if axes is None:
            _, axes = plt.subplots(nrows=1, figsize=(12, 6))

        axes.set_ylim(0, 1)
        axes.set_title(self.name, fontsize=20, fontweight="bold")

        # create necessary containers
        graph = DiGraph()
        signal_node_list = []
        data_node_list = []
        data_labels = {}
        signal_node_edge_list = []
        signal_labels = {}
        positions = {}
        edge_labels = {}

        # gather containers in tuples
        signal_container = (graph, signal_node_list, signal_labels, positions)
        data_container = (graph, data_node_list, data_labels, positions)

        # Add source signal
        c_node = "node_0"
        p_node = None
        delta_pos = 2 / (len(self.data_processors) + 1)
        x_pos = delta_pos / 2
        label = _signal_label(self.data_source.output_signal)

        self._add_node(c_node, p_node, label, (x_pos, 0.75), signal_container)

        for i, processor in enumerate(self.data_processors):
            # update node data
            x_pos += delta_pos
            p_node = c_node
            c_node = f"node_{i+1}"
            label = _signal_label(processor.output_signal)

            # add signal node and edge
            self._add_node(c_node, p_node, label, (x_pos, 0.75), signal_container)
            signal_node_edge_list.append((p_node, c_node))
            edge_label_text = processor.name
            if processor.func:
                edge_label_text += f"\n{processor.func.expression}"
            if processor.error and processor.error.deviation != 0.0:
                edge_label_text += f"\nerr: {processor.error.deviation}"

            edge_labels[(p_node, c_node)] = edge_label_text

            # add data node and edge
            if processor.output_signal.data is not None:
                d_name = processor.output_signal.data.name
                self._add_node(d_name, c_node, d_name, (x_pos, 0.25), data_container)

        # draw signal nodes and all edges
        draw(
            graph,
            positions,
            axes,
            nodelist=signal_node_list,
            with_labels=True,
            labels=signal_labels,
            font_weight="bold",
            font_color="k",
            node_size=3000,
            node_shape="s",
            node_color="#bbbbbb",
        )

        # draw data nodes
        draw(
            graph,
            positions,
            axes,
            nodelist=data_node_list,
            with_labels=True,
            labels=data_labels,
            font_weight="bold",
            font_color="k",
            edgelist=[],
            node_size=3000,
            node_color="#bbbbbb",
        )

        # draw edge labels
        draw_networkx_edge_labels(graph, positions, edge_labels, ax=axes)

        return axes


@dataclass
class Measurement:
    """Simple dataclass implementation for generic measurements."""

    name: str
    data: Data
    measurement_chain: MeasurementChain


# equipment ----------------------------------------------------------------------------
@dataclass
class GenericEquipment:
    """Simple dataclass implementation for generic equipment."""

    name: str
    sources: List = field(default_factory=lambda: [])
    data_transformations: List = field(default_factory=lambda: [])
