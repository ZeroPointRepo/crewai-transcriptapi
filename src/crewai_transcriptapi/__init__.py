"""crewai-transcriptapi: CrewAI tools for TranscriptAPI (transcriptapi.com)."""

from .transcriptapi_tool import (
    TranscriptAPISearchToolSchema,
    TranscriptAPIToolSchema,
)

try:
    from .transcriptapi_tool import TranscriptAPISearchTool, TranscriptAPITool
except ImportError:  # pragma: no cover - crewai not installed
    pass

__version__ = "0.1.0"

__all__ = [
    "TranscriptAPITool",
    "TranscriptAPISearchTool",
    "TranscriptAPIToolSchema",
    "TranscriptAPISearchToolSchema",
    "__version__",
]
