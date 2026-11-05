from __future__ import annotations

from typing import Any, Mapping

import pydantic

from bird._exceptions import BirdError
from bird._types import Omit


class BaseModel(pydantic.BaseModel):
    """Base for every generated wire model.

    Forward-compatible by default: a field the server adds later is
    accepted and preserved rather than raising, so an older SDK keeps working
    against a newer API. The generator sets ``extra="allow"`` on each model via
    ``--extra-fields``; this base reasserts it and adds the config the facade needs.
    """

    model_config = pydantic.ConfigDict(
        extra="allow",
        populate_by_name=True,  # facade builds requests by field name (e.g. from_)
        validate_default=True,  # coerce enum defaults so a dump never warns
    )


def _validate(model_cls: type[pydantic.BaseModel], data: Mapping[str, Any]) -> pydantic.BaseModel:
    """Validate request fields through the generated model, re-raising a client-side
    ``pydantic.ValidationError`` as a ``BirdError`` so everything the SDK raises is a
    ``BirdError`` — and never collides with the SDK's own ``ValidationError`` (a 422
    server response). The message reports which field failed and why (field path +
    reason) but never the offending value, so a caller logging the error can't leak
    recipient/subject content; the original validation error is preserved as
    ``__cause__``.
    """
    try:
        supplied = _without_omit(data)
        # Existing optional nonnullable keyword parameters use None for omission.
        # Apply that convention only at this facade boundary; nested supplied
        # None values retain their meaning and are validated below.
        omitted = _optional_nonnullable_keys(model_cls)
        supplied = {key: value for key, value in supplied.items() if value is not None or key not in omitted}
        model = model_cls.model_validate(supplied)
        _validate_request_nulls(model, "")
        return model
    except pydantic.ValidationError as exc:
        reasons = "; ".join(f"{'.'.join(str(p) for p in e['loc'])}: {e['msg']}" for e in exc.errors())
        raise BirdError(f"invalid request: {reasons}") from exc


def _without_omit(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _without_omit(item) for key, item in value.items() if not isinstance(item, Omit)}
    if isinstance(value, (list, tuple)):
        return [_without_omit(item) for item in value]
    return value


def _optional_nonnullable_keys(model_cls: type[pydantic.BaseModel]) -> set[str]:
    keys: set[str] = set()
    for name, field in model_cls.model_fields.items():
        metadata = field.json_schema_extra
        if not field.is_required() and isinstance(metadata, dict) and metadata.get("x-bird-nullable") is False:
            keys.add(name)
            if isinstance(field.alias, str):
                keys.add(field.alias)
            if isinstance(field.validation_alias, str):
                keys.add(field.validation_alias)
    return keys


def _reject_nested_input_nulls(model_cls: type[pydantic.BaseModel], data: Mapping[str, Any]) -> None:
    # Batch messages have an authored friendly mapper before model validation.
    # Check their supplied keys before that mapper applies the root None-default
    # convention and erases whether a nested property was explicitly null.
    for key in _optional_nonnullable_keys(model_cls):
        if key in data and data[key] is None:
            raise BirdError(f"invalid request: {key}: null is not allowed")


def _validate_request_nulls(value: Any, path: str) -> None:
    # Response models retain their permissive defaults. Only a request's supplied
    # fields are checked against the generator's independent nullable contract.
    if isinstance(value, pydantic.BaseModel):
        for name in value.model_fields_set:
            field = type(value).model_fields.get(name)
            item = getattr(value, name)
            key = (field.serialization_alias or field.alias or name) if field else name
            child = f"{path}.{key}" if path else key
            metadata = field.json_schema_extra if field else None
            if item is None and isinstance(metadata, dict) and metadata.get("x-bird-nullable") is False:
                raise BirdError(f"invalid request: {child}: null is not allowed")
            _validate_request_nulls(item, child)
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _validate_request_nulls(item, f"{path}.{index}")
    elif isinstance(value, Mapping):
        for key, item in value.items():
            _validate_request_nulls(item, f"{path}.{key}" if path else str(key))


def to_wire(model_cls: type[pydantic.BaseModel], data: Mapping[str, Any]) -> dict[str, Any]:
    """Validate supplied request fields, preserving explicit nulls at every depth.

    Optional nonnullable root None values keep their existing omission convention;
    nullable and nested None values remain explicit. Omit also omits a field.
    Generated model defaults never enter a request.
    ``by_alias`` maps Python identifiers such as ``from_`` to their wire names.
    """
    return _validate(model_cls, data).model_dump(by_alias=True, exclude_unset=True, mode="json")

