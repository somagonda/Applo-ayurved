from dataclasses import dataclass


@dataclass(frozen=True)
class ToolResult:
    message: str
    transferred: bool = False

