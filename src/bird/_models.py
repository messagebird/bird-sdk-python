from __future__ import annotations

from typing import Any, Mapping

import pydantic

from bird._exceptions import BirdError


class BaseModel(pydantic.BaseModel):
    """Base for every generated wire model.

    Forward-compatible by default (ADR-0045): a field the server adds later is
    accepted and preserved rather than raising, so an older SDK keeps working
    against a newer API. The generator sets ``extra="allow"`` on each model via
    ``--extra-fields``; this base reasserts it and adds the config the facade needs.
    """

    model_config = pydantic.ConfigDict(
        extra="allow",
        populate_by_name=True,  # facade builds requests by field name (e.g. from_)
        validate_default=True,  # coerce enum defaults so a dump never warns
    )


def to_wire(model_cls: type[pydantic.BaseModel], data: Mapping[str, Any]) -> dict[str, Any]:
    """Validate request fields through the generated model, then emit wire JSON.

    ``by_alias`` maps ``from_`` to the wire field ``from``; ``exclude_none`` drops
    unset fields so the server applies its defaults. Client-side validation failures
    surface as ``BirdError`` (not a raw ``pydantic.ValidationError``) so everything the
    SDK raises is a ``BirdError`` — and never collides with the SDK's own
    ``ValidationError`` (a 422 server response). The message reports which field
    failed and why (field path + reason) but never the offending value, so a caller
    logging the error can't leak recipient/subject content; the original validation
    error is preserved as ``__cause__``.
    """
    try:
        model = model_cls.model_validate(dict(data))
    except pydantic.ValidationError as exc:
        reasons = "; ".join(f"{'.'.join(str(p) for p in e['loc'])}: {e['msg']}" for e in exc.errors())
        raise BirdError(f"invalid request: {reasons}") from exc
    return model.model_dump(by_alias=True, exclude_none=True, mode="json")
