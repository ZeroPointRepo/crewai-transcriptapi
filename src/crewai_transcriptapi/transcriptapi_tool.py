"""CrewAI tools for TranscriptAPI (transcriptapi.com).

Two tools following the crewai-tools BaseTool conventions:

- TranscriptAPITool: fetch the transcript of a YouTube video (the hero use case)
- TranscriptAPISearchTool: search YouTube for videos or channels

Both return a stable JSON string envelope and never leak exceptions:
  {"success": true, "data": {...}}
  {"success": false, "error": {"code": "...", "message": "..."}}

Auth: TRANSCRIPTAPI_API_KEY environment variable (Bearer key, "sk_..." format).
"""

import json
import os
from typing import Any, Optional, Type

from pydantic import BaseModel, ConfigDict, Field

try:  # crewai is the runtime host; keep the import lazy-friendly for tests
    from crewai.tools import BaseTool, EnvVar
except ImportError:  # pragma: no cover - exercised only without crewai installed
    BaseTool = None  # type: ignore[assignment,misc]
    EnvVar = None  # type: ignore[assignment,misc]

BASE_URL = "https://transcriptapi.com/api/v2"
USER_AGENT = "crewai-transcriptapi/0.1.0 (+https://github.com/ZeroPointRepo/crewai-transcriptapi)"
TIMEOUT_SECONDS = 60

_ENV_KEY = "TRANSCRIPTAPI_API_KEY"

_ENV_VARS = (
    [
        EnvVar(
            name=_ENV_KEY,
            description=(
                "TranscriptAPI key (starts with sk_). Create one at "
                "https://transcriptapi.com: 100 free credits, no card (one-time)."
            ),
            required=True,
        )
    ]
    if EnvVar is not None
    else []
)


def _envelope_error(code: str, message: str) -> str:
    return json.dumps({"success": False, "error": {"code": code, "message": message}})


def _request(path: str, params: dict) -> str:
    """GET a TranscriptAPI endpoint and return the JSON string envelope."""
    key = os.environ.get(_ENV_KEY, "").strip()
    if not key:
        return _envelope_error(
            "missing_api_key",
            f"{_ENV_KEY} is not set. Get a free key at https://transcriptapi.com "
            "(100 free credits, no card, one-time).",
        )
    import requests  # lazy import so tests can stub it

    try:
        response = requests.get(
            BASE_URL + path,
            params={k: v for k, v in params.items() if v is not None},
            headers={
                "Authorization": f"Bearer {key}",
                "User-Agent": USER_AGENT,
                "Accept": "application/json",
            },
            timeout=TIMEOUT_SECONDS,
        )
    except requests.exceptions.RequestException as exc:
        return _envelope_error("network", str(exc))
    if response.status_code != 200:
        code = {
            401: "invalid_api_key",
            402: "out_of_credits",
            404: "not_found",
            429: "rate_limited",
        }.get(response.status_code, f"http_{response.status_code}")
        message = {
            401: "The API key was rejected. Check TRANSCRIPTAPI_API_KEY.",
            402: "The account is out of credits. See https://transcriptapi.com/billing.",
            404: "Not found: the video may not exist or has no captions.",
            429: "Rate limited. Wait and retry, respecting the Retry-After header.",
        }.get(response.status_code, response.text[:300])
        return _envelope_error(code, message)
    try:
        data = response.json()
    except ValueError:
        return _envelope_error("bad_response", "The API returned a non-JSON response.")
    return json.dumps({"success": True, "data": data})


class TranscriptAPIToolSchema(BaseModel):
    """Input for TranscriptAPITool."""

    video_url: str = Field(
        ...,
        min_length=6,
        description=(
            "Full YouTube URL (watch, youtu.be, embed, or Shorts) or the bare "
            "11-character video ID"
        ),
    )
    output_format: str = Field(
        default="text",
        pattern="^(text|json)$",
        description='Transcript format: "text" (plain transcript) or "json" (timestamped segments)',
    )
    language: Optional[str] = Field(
        default=None,
        description="Optional preferred transcript language code, for example 'es'",
    )


class TranscriptAPISearchToolSchema(BaseModel):
    """Input for TranscriptAPISearchTool."""

    query: str = Field(..., min_length=1, max_length=200, description="Search query")
    search_type: str = Field(
        default="video",
        pattern="^(video|channel)$",
        description='What to search for: "video" or "channel"',
    )


if BaseTool is not None:

    class TranscriptAPITool(BaseTool):
        """Fetch the transcript of a YouTube video via TranscriptAPI."""

        model_config = ConfigDict(arbitrary_types_allowed=True)
        name: str = "TranscriptAPI YouTube Transcript"
        description: str = (
            "Fetches the transcript of a YouTube video, with metadata, via the "
            "TranscriptAPI service. Accepts a full YouTube URL (watch, youtu.be, "
            "embed, Shorts) or a bare 11-character video ID. Use when the task "
            "needs the spoken content of a specific video: summarizing, quoting, "
            "translating or analyzing it. Costs 1 credit per successful call."
        )
        args_schema: Type[BaseModel] = TranscriptAPIToolSchema
        package_dependencies: list = Field(default_factory=lambda: ["requests"])
        env_vars: list = Field(default_factory=lambda: list(_ENV_VARS))

        def _run(self, **kwargs: Any) -> str:
            args = TranscriptAPIToolSchema(**kwargs)
            return _request(
                "/youtube/transcript",
                {
                    "video_url": args.video_url,
                    "format": args.output_format,
                    "send_metadata": "true",
                    "language": args.language,
                },
            )

    class TranscriptAPISearchTool(BaseTool):
        """Search YouTube for videos or channels via TranscriptAPI."""

        model_config = ConfigDict(arbitrary_types_allowed=True)
        name: str = "TranscriptAPI YouTube Search"
        description: str = (
            "Searches YouTube for videos or channels via the TranscriptAPI "
            "service and returns titles, IDs, thumbnails, view counts and "
            "publish dates. Use when the task needs to discover videos or "
            "channels about a topic before fetching transcripts. Costs 1 credit "
            "per page of results."
        )
        args_schema: Type[BaseModel] = TranscriptAPISearchToolSchema
        package_dependencies: list = Field(default_factory=lambda: ["requests"])
        env_vars: list = Field(default_factory=lambda: list(_ENV_VARS))

        def _run(self, **kwargs: Any) -> str:
            args = TranscriptAPISearchToolSchema(**kwargs)
            return _request(
                "/youtube/search",
                {"q": args.query, "type": args.search_type},
            )
