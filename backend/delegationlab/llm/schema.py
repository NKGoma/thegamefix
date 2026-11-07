"""JSON schema helpers. Schemas sent to providers are flattened: no $ref / $defs."""

from typing import Any

from pydantic import BaseModel


def _inline(node: Any, defs: dict[str, Any]) -> Any:
    if isinstance(node, dict):
        if "$ref" in node:
            name = node["$ref"].rsplit("/", 1)[-1]
            merged = {**_inline(defs[name], defs), **{k: v for k, v in node.items() if k != "$ref"}}
            return merged
        return {k: _inline(v, defs) for k, v in node.items() if k != "$defs"}
    if isinstance(node, list):
        return [_inline(v, defs) for v in node]
    return node


def json_schema_for(model: type[BaseModel]) -> dict[str, Any]:
    schema = model.model_json_schema()
    return _inline(schema, schema.get("$defs", {}))  # type: ignore[no-any-return]
