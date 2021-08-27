"""Contains general (mostly internal) utility functions."""
from __future__ import annotations

import functools
import json
import re
import sys
import warnings
from collections.abc import Sequence
from functools import wraps
from inspect import getmembers, isfunction
from pathlib import Path
from typing import Callable, ClassVar, Collection, Mapping, Union

import numpy as np
import pandas as pd
import pint
import psutil
import xarray as xr
from asdf.tags.core import NDArrayType
from boltons import iterutils

from weldx.constants import WELDX_UNIT_REGISTRY as ureg


class WeldxDeprecationWarning(DeprecationWarning):
    """Deprecation warning type."""


def deprecated(since: str = None, removed: str = None, message: str = None) -> Callable:
    """Mark a functions as deprecated.

    This decorator emits a warning when the function is used.

    Parameters
    ----------
    since :
        The version that marked the function as deprecated
    removed :
        The version that will remove the function
    message :
        Additional information that should be added to the warning

    Returns
    -------
    Callable :
        Wrapped function

    Notes
    -----
    Original source: https://stackoverflow.com/a/30253848/6700329

    """

    def _decorator(func):
        @wraps(func)
        def _new_func(*args, **kwargs):
            wm = f"Call to deprecated function {func.__name__}.\n"
            if since is not None:
                wm += f"Deprecated since: {since}\n"
            if removed is not None:
                wm += f"Removed in: {removed}\n"
            if message is not None:
                wm += message

            warnings.warn(wm, category=WeldxDeprecationWarning, stacklevel=2)
            return func(*args, **kwargs)

        return _new_func

    return _decorator


def ureg_check_class(*args):
    """Decorate class :code:`__init__` function with `pint.UnitRegistry.check`.

    Useful for adding unit checks to classes created with :code:`@dataclass` decorator.

    Parameters
    ----------
    args: str or pint.util.UnitsContainer or None
        Dimensions of each of the input arguments.
        Use :code:`None` to skip argument conversion.

    Returns
    -------
    type
        The class with unit checks added to its :code:`__init__` function.

    Raises
    ------
    TypeError
        If number of given dimensions does not match the number of function parameters.
    ValueError
        If the any of the provided dimensions cannot be parsed as a dimension.

    Examples
    --------
    A simple dataclass could look like this::

        @ureg_check_class("[length]","[time]")
        @dataclass
        class A:
            a: pint.Quantity
            b: pint.Quantity

        A(Q_(3,"mm"),Q_(3,"s"))

    """

    def _inner_decorator(
        original_class,
    ):
        # Make copy of original __init__, so we can call it without recursion
        orig_init = original_class.__init__

        # apply pint check decorator
        new_init = ureg.check(None, *args)(orig_init)

        # set new init
        original_class.__init__ = new_init  # Set the class' __init__ to the new one
        return original_class

    return _inner_decorator


def _clean_notebook(file: Union[str, Path]):  # pragma: no cover
    """Clean ID metadata, output and execution count from jupyter notebook cells.

    This function overrides the existing notebook file, use with caution!

    Parameters
    ----------
    file :
        The jupyter notebook filename to clean.

    """
    with open(file, "r", encoding="utf-8") as f:
        data = json.load(f)

    for cell in data["cells"]:
        cell.pop("id", None)
        if "outputs" in cell:
            cell["outputs"] = []
        if "execution_count" in cell:
            cell["execution_count"] = None

    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
        f.write("\n")


def inherit_docstrings(cls):
    """Inherits (public) docstrings from parent classes.

    Traverses the MRO until it finds a docstring to use, or leave it blank,
    in case no parent has a docstring available.

    Parameters
    ----------
    cls: type
        The class to decorate.

    Returns
    -------
    cls: type
        The class with updated doc strings.

    """
    for name, func in getmembers(
        cls, predicate=lambda x: isfunction(x) or isinstance(x, property)
    ):
        if func.__doc__ or name.startswith("_"):
            continue
        for parent in cls.__mro__[1:]:
            if hasattr(parent, name):
                func.__doc__ = getattr(parent, name).__doc__
                if not func.__doc__:
                    warnings.warn(
                        f"could not derive docstring for {cls}.{name}",
                        stacklevel=2,
                        category=ImportWarning,
                    )
    return cls


def _array_equal(a, b):
    if a.shape != b.shape:
        return False
    return np.all(a == b)


_eq_compare_nested_input_types = Union[
    Sequence,
    Mapping,
    Collection,
]


class _EqCompareNested:
    """Compares nested data structures like lists, sets, tuples, arrays, etc."""

    # some types need special comparison handling.
    compare_funcs: ClassVar = {
        (np.ndarray, NDArrayType, pint.Quantity, pd.Index): _array_equal,
        (xr.DataArray, xr.Dataset): lambda x, y: x.identical(y),
    }
    # these types will be treated as equivalent.
    _type_equalities: ClassVar = [
        (np.ndarray, NDArrayType),
    ]

    @staticmethod
    def _compare(x, y) -> bool:
        # 1. strict type comparison (exceptions defined in _type_equalities).
        # 2. handle special comparison cases
        if not any(
            (type(x) in e and type(y) in e) for e in _EqCompareNested._type_equalities
        ) and type(x) is not type(y):
            return False

        for types, func in _EqCompareNested.compare_funcs.items():
            if isinstance(x, types):
                return func(x, y)

        return x == y

    @staticmethod
    def _enter(path, key, value):
        # Do not traverse types defined in compare_funcs. All other types are handled
        # like in boltons.iterutils.default_enter (e.g. descend into nested structures).
        # See `boltons.iterutils.remap` for details.
        if any(isinstance(value, t) for t in _EqCompareNested.compare_funcs):
            return value, False

        return iterutils.default_enter(path, key, value)

    @staticmethod
    def _visit(path, key, value, a, b) -> bool:
        """Traverses all elements in `compare_nested` argument a and b...

        and tries to obtain the path `p` in `b` using boltons.iterutils.get_path.
        The following cases can occur:
        1. If the path does not exist in `b` a KeyError will be raised.
        2. If the index `k` does not exist an IndexError is raised.
        3. If the other path exists, a comparison will be made using `_compare`.
           When the elements are not equal traversing `a` will be stopped
           by raising a RuntimeError.
        """
        data_structure = iterutils.get_path(a, path)
        other_data_structure = iterutils.get_path(b, path)

        # directly test for equality with sets
        if isinstance(data_structure, set) or isinstance(other_data_structure, set):
            if data_structure == other_data_structure:
                return True
            raise RuntimeError("sets not equal")

        other_value = other_data_structure[key]
        if not _EqCompareNested._enter(None, key, value)[1]:
            # check lengths of Sequence types first and raise
            # prior starting a more expensive comparison!
            if isinstance(other_data_structure, Sequence) and len(
                other_data_structure
            ) != len(iterutils.get_path(a, path)):
                raise RuntimeError("len does not match")
            if isinstance(other_data_structure, Mapping) and any(
                other_data_structure.keys() ^ iterutils.get_path(a, path).keys()
            ):
                raise RuntimeError("keys do not match")
            if not _EqCompareNested._compare(value, other_value):
                raise RuntimeError("not equal")
        return True

    @staticmethod
    def compare_nested(
        a: _eq_compare_nested_input_types, b: _eq_compare_nested_input_types
    ) -> bool:
        """Deeply compares [nested] data structures combined of tuples, lists, dicts...

        Also compares non-nested data-structures.
        Arrays are compared using np.all and xr.DataArray.identical

        Parameters
        ----------
        a :
            a [nested] data structure to compare to `b`.
        b :
            a [nested] data structure to compare to `a`.

        Returns
        -------
        bool :
            True, if all elements (including dict keys) of a and b are equal.

        Raises
        ------
        TypeError
            When a or b is not a nested structure.

        """
        # we bind the input structures a, b to the visit function.
        visit = functools.partial(_EqCompareNested._visit, a=a, b=b)

        try:
            iterutils.remap(a, visit=visit, reraise_visit=True)
        # Key not found in b, values not equal, more elements in a than in b
        except (KeyError, RuntimeError, IndexError):
            return False
        except TypeError:
            raise TypeError("either a or b are not a nested data structure.")

        return True


compare_nested = _EqCompareNested.compare_nested


def dataclass_nested_eq(original_class):
    """Set class :code:`__eq__` using :code:`util.compare_nested` on :code:`__dict__`.

    Useful for implementing :code:`__eq__` on classes
    created with :code:`@dataclass` decorator.

    Parameters
    ----------
    original_class:
        original class to decorate

    Returns
    -------
    type
        The class with overridden :code:`__eq__` function.

    Examples
    --------
    A simple dataclass could look like this::

        @dataclass_nested_eq
        @dataclass
        class A:
            a: np.ndarray

        a = A(np.arange(3))
        b = A(np.arange(3))
        assert a==b

    """

    def _new_eq(self, other):
        if not isinstance(other, type(self)):
            return False

        return compare_nested(self.__dict__, other.__dict__)

    # set new eq function
    original_class.__eq__ = _new_eq  # Set the class' __eq__ to the new one
    return original_class


def is_interactive_session() -> bool:
    """Check whether this Python session is interactive, e.g. Jupyter/IPython."""
    try:
        get_ipython = sys.modules["IPython"].get_ipython  # type: ignore[attr-defined]
        if not get_ipython():
            return False
        if "IPKernelApp" not in get_ipython().config:  # pragma: no cover
            return False
    except KeyError:
        return False
    else:
        return True


def is_jupyterlab_session() -> bool:
    """Heuristic to check whether we are in a Jupyter-Lab session.

    Notes
    -----
    False positive, if classic NB launched from JupyterLab.

    """
    return any(re.search("jupyter-lab", x) for x in psutil.Process().parent().cmdline())
