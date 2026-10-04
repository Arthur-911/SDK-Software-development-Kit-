"""Base Pydantic model for Server Developer Kit."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class ServerBaseModel(BaseModel):
    """Base model with common serialization utilities."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
        arbitrary_types_allowed=True,
        str_strip_whitespace=True,
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert model instance into a Python dictionary."""
        return self.model_dump(by_alias=True)

    def to_json(self, indent: int = 2) -> str:
        """Convert model instance into a JSON formatted string."""
        return self.model_dump_json(indent=indent, by_alias=True)
