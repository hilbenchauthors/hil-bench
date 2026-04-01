from __future__ import annotations

from pydantic import BaseModel


class Argument(BaseModel):
    name: str
    type: str
    description: str
    required: bool


class Command(BaseModel):
    name: str
    docstring: str
    arguments: list[Argument] = []

    def get_function_calling_tool(self) -> dict:
        properties = {
            arg.name: {"type": arg.type, "description": arg.description} for arg in self.arguments
        }
        required = [arg.name for arg in self.arguments if arg.required]
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.docstring,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        }
