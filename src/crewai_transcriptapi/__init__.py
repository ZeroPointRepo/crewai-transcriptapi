"""crewai-transcriptapi: CrewAI tools for TranscriptAPI (transcriptapi.com)."""

from .transcriptapi_tool import (
    TranscriptAPISearchToolSchema,
    TranscriptAPIToolSchema,
    TranscriptAPIVideoMetadataToolSchema,
)

try:
    from .transcriptapi_tool import (
        TranscriptAPISearchTool,
        TranscriptAPITool,
        TranscriptAPIVideoMetadataTool,
    )
except ImportError:  # pragma: no cover - crewai not installed
    pass

__version__ = "0.2.0"

__all__ = [
    "TranscriptAPITool",
    "TranscriptAPISearchTool",
    "TranscriptAPIVideoMetadataTool",
    "TranscriptAPIToolSchema",
    "TranscriptAPISearchToolSchema",
    "TranscriptAPIVideoMetadataToolSchema",
    "__version__",
]
