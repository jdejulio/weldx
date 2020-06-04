from typing import Any, Callable, Iterator, List, Mapping, OrderedDict

import dpath
from asdf import ValidationError

from weldx.constants import WELDX_QUANTITY as Q_
from weldx.constants import WELDX_UNIT_REGISTRY as UREG


def _walk_validator(
    instance: OrderedDict,
    validator_dict: OrderedDict,
    validator_function: Callable[[Mapping, Any, str], Iterator[ValidationError]],
    position="",
) -> Iterator[ValidationError]:
    """Walk instance and validation dict entries in parallel and apply a validator func.

    This function can be used to recursively walk both the instance dictionary and the
    custom validation dictionary in parallel. Once a leaf dictionary entry is reached,
    the validation function is applied to the selected items.

    Parameters
    ----------
    instance:
        Tree serialization (with default dtypes) of the instance
    validator_dict:
        OrderedDict representation of the validation structure.
    validator_function:
        Custom python validator function to apply along the (nested) dictionary
    position:
        String representation of the current nested schema position

    Yields
    ------
    asdf.ValidationError

    """
    if isinstance(validator_dict, dict):
        for key, item in validator_dict.items():
            if isinstance(item, Mapping):
                yield from _walk_validator(
                    instance[key],
                    validator_dict[key],
                    validator_function,
                    position=position + "/" + key,
                )
            else:
                yield from validator_function(instance[key], item, position + "/" + key)
    else:
        yield from validator_function(instance, validator_dict, position)


def _unit_validator(
    instance: Mapping, expected_dimensionality: str, position: str
) -> Iterator[ValidationError]:
    """Validate the 'unit' key of the instance against the given string.

    Parameters
    ----------
    instance:
        Tree serialization with 'unit' key to validate.
    expected_dimensionality:
        String representation of the unit dimensionality to test against.
    position:
        Current position in nested structure for debugging

    Yields
    ------
    asdf.ValidationError

    """
    unit = instance["unit"]
    valid = Q_(unit).check(UREG.get_dimensionality(expected_dimensionality))
    if not valid:
        yield ValidationError(
            f"Error validating unit dimension for property '{position}'. "
            f"Expected unit of dimension '{expected_dimensionality}' but got unit '{unit}'"
        )


def _shape_validator(
    instance: Mapping, expected_shape: List[int], position: str
) -> Iterator[ValidationError]:
    """Validate the 'shape' key of the instance against the given list of ints.

    Parameters
    ----------
    instance:
        Tree serialization with 'shape' key to validate.
    expected_shape:
        String representation of the unit dimensionality to test against.
    position:
        Current position in nested structure for debugging

    Yields
    ------
    asdf.ValidationError

    """
    shape = instance["shape"]
    valid = shape == expected_shape  # TODO: custom shape validator with "any" syntax
    if not valid:
        yield ValidationError(
            f"Error validating shape for property '{position}'. "
            f"Expected shape '{expected_shape}' but got '{shape}'"
        )


def validate_unit_dimension(
    validator, wx_unit_validate, instance, schema
) -> Iterator[ValidationError]:
    """Custom validator for checking dimensions for objects with 'unit' property.

    ASDF documentation:
    https://asdf.readthedocs.io/en/2.6.0/asdf/extensions.html#adding-custom-validators

    Parameters
    ----------
    validator:
        A jsonschema.Validator instance.
    wx_unit_validate:
        Enable unit validation for this schema.
    instance:
        Tree serialization (with default dtypes) of the instance
    schema:
        Dict representing the full ASDF schema.

    Yields
    ------
    asdf.ValidationError

    """
    if wx_unit_validate:
        schema_key_list = [
            k for k in dpath.util.search(schema, "**/wx_unit", yielded=True)
        ]
        schema_key_list = [
            (s[0].replace("properties/", "").split("/"), s[1]) for s in schema_key_list
        ]
        for s in schema_key_list:
            if len(s[0]) > 1:
                position = "/".join(s[0][:-1])
                instance_dict = dpath.util.get(instance, s[0][:-1])
            else:
                position = ""
                instance_dict = instance
            yield from _walk_validator(
                instance=instance_dict,
                validator_dict=s[1],
                validator_function=_unit_validator,
                position=position,
            )


def validate_array_shape(
    validator, wx_shape, instance, schema
) -> Iterator[ValidationError]:
    """Custom validator for checking dimensions for objects with 'shape' property.

    ASDF documentation:
    https://asdf.readthedocs.io/en/2.6.0/asdf/extensions.html#adding-custom-validators

    Parameters
    ----------
    validator:
        A jsonschema.Validator instance.
    wx_shape:
        Dict with property keys and array dimensions as list to validate.
    instance:
        Tree serialization (with default dtypes) of the instance
    schema:
        Dict representing the full ASDF schema.

    Yields
    ------
    asdf.ValidationError

    """
    yield from _walk_validator(
        instance=instance, validator_dict=wx_shape, validator_function=_shape_validator,
    )
