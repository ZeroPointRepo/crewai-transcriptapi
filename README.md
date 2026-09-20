# crewai-transcriptapi

**TranscriptAPI: hosted YouTube transcript + video-discovery API for AI agents.** CrewAI tools edition. Also available as an [n8n community node](https://github.com/ZeroPointRepo/n8n-nodes-transcriptapi), an [MCP server](https://github.com/ZeroPointRepo/youtube-mcp) and [agent skills](https://github.com/ZeroPointRepo/youtube-skills).

## Why this package

Give a CrewAI agent eyes and ears on YouTube without shelling out to `yt-dlp` (blocked on most cloud IPs), scraping HTML, or juggling the Google YouTube Data API and its quota. [TranscriptAPI](https://transcriptapi.com) is a hosted backend built for this: fast transcript extraction, video search, and rich video metadata, wrapped here as three [CrewAI](https://www.crewai.com/) tools that drop straight into an `Agent`'s `tools` list.

This package is deliberately **curated**, not a full mirror of the API: three tools cover the core research loop (find a video, learn about it, read what was said in it). See [The full TranscriptAPI surface](#the-full-transcriptapi-surface) below for the rest (channel browsing, playlists, community posts) via the REST API or MCP.

## Installation

```bash
pip install crewai-transcriptapi
```

## Credentials

You need a TranscriptAPI key (starts with `sk_`):

1. Create an account at [transcriptapi.com](https://transcriptapi.com): **100 free credits, no card (one-time)**; paid plans from **$5/mo (1,000 credits)**.
2. Create an API key on the dashboard.
3. Export it:

```bash
export TRANSCRIPTAPI_API_KEY="sk_..."
```

## Tools

| Tool | What it does | Cost |
|---|---|---|
| **TranscriptAPITool** | Fetch the transcript of a YouTube video (full URL, youtu.be, embed, Shorts, or bare ID) as plain text or timestamped JSON, with metadata | 1 credit/call |
| **TranscriptAPISearchTool** | Search YouTube for videos, channels, playlists, or movies, with sort/upload-date/duration/feature filters | 1 credit/page |
| **TranscriptAPIVideoMetadataTool** | Pull a video's view/like counts, publish date, description, links, uploading channel, and optional player details or related videos, without touching captions | 1 credit/call |

## When to use what

| Job | Tool |
|---|---|
| Need the spoken content of a video: summarize, quote, translate, fact-check | `TranscriptAPITool` |
| Need to discover videos, channels, playlists, or movies about a topic before pulling anything else | `TranscriptAPISearchTool` |
| Need facts about a video without spending time (or a credit) on its captions: view/like counts, publish date, description, duration, tags, related videos | `TranscriptAPIVideoMetadataTool` |
| Building a research pipeline: find candidates, then decide which ones are worth a full transcript | `TranscriptAPISearchTool` -> `TranscriptAPIVideoMetadataTool` -> `TranscriptAPITool` |

## Usage

Basic setup: search, then transcribe.

```python
from crewai import Agent
from crewai_transcriptapi import TranscriptAPITool, TranscriptAPISearchTool

researcher = Agent(
    role="Video researcher",
    goal="Find and summarize YouTube content on a topic",
    backstory="Researches spoken video content via transcripts.",
    tools=[TranscriptAPISearchTool(), TranscriptAPITool()],
)
```

The agent can then search for videos on a topic and fetch each transcript for summarizing, quoting, translating or analysis.

### Research crew example: search, screen, then transcribe

Adding `TranscriptAPIVideoMetadataTool` lets the agent screen search results (view count, publish date, duration) before spending a credit on a transcript it doesn't need:

```python
from crewai import Agent, Task, Crew
from crewai_transcriptapi import (
    TranscriptAPITool,
    TranscriptAPISearchTool,
    TranscriptAPIVideoMetadataTool,
)

researcher = Agent(
    role="Video researcher",
    goal="Find the most relevant, well-established videos on a topic and summarize them",
    backstory=(
        "Searches YouTube for candidates, checks each one's metadata to judge "
        "relevance and credibility before spending a transcript credit, then "
        "reads the transcripts of the ones worth reading."
    ),
    tools=[
        TranscriptAPISearchTool(),
        TranscriptAPIVideoMetadataTool(),
        TranscriptAPITool(),
    ],
)

task = Task(
    description=(
        "Find 3 well-established videos about {topic}. For each, check the "
        "view count and publish date before deciding it's worth summarizing, "
        "then fetch the transcript and write a 5-bullet summary."
    ),
    expected_output="A markdown report with one section per video.",
    agent=researcher,
)

Crew(agents=[researcher], tasks=[task]).kickoff(inputs={"topic": "transformer architectures"})
```

### Calling a tool directly

Every tool returns a JSON string, so you can call it outside of a `Crew` for scripting or testing:

```python
import json
from crewai_transcriptapi import TranscriptAPIVideoMetadataTool

tool = TranscriptAPIVideoMetadataTool()
result = json.loads(tool.run(video_url="dQw4w9WgXcQ", include="details,related"))
if result["success"]:
    print(result["data"]["title"], result["data"]["viewCountText"])
```

## Tool reference

### TranscriptAPITool

| Argument | Type | Default | Description |
|---|---|---|---|
| `video_url` | str | required | Full YouTube URL (watch, youtu.be, embed, Shorts) or bare 11-character video ID |
| `output_format` | str | `"text"` | `"text"` for plain transcript, `"json"` for timestamped segments |
| `language` | str | none | Optional preferred transcript language code, for example `"es"` |

### TranscriptAPISearchTool

| Argument | Type | Default | Description |
|---|---|---|---|
| `query` | str | required | Search query, 1 to 200 characters |
| `search_type` | str | `"video"` | `"video"`, `"channel"`, `"playlist"`, or `"movie"` |
| `sort` | str | none | `"relevance"` or `"views"` |
| `upload_date` | str | none | `"hour"`, `"today"`, `"week"`, `"month"`, or `"year"` (videos only) |
| `duration` | str | none | `"short"` (<4m), `"medium"` (4-20m), or `"long"` (>20m) (videos only) |
| `features` | str | none | Comma-separated filters, e.g. `"hd,subtitles,cc,live,4k,hdr,360,creative_commons"` |

### TranscriptAPIVideoMetadataTool

| Argument | Type | Default | Description |
|---|---|---|---|
| `video_url` | str | required | Full YouTube URL (watch, youtu.be, embed, Shorts) or bare 11-character video ID |
| `include` | str | none | Comma-separated extras: `"details"` and/or `"related"` |

## Response envelope

All three tools return a stable JSON string and never raise:

```json
{"success": true, "data": {"transcript": "...", "metadata": {"title": "..."}}}
```

```json
{"success": false, "error": {"code": "out_of_credits", "message": "The account is out of credits. See https://transcriptapi.com/billing."}}
```

Error codes: `missing_api_key`, `invalid_api_key`, `out_of_credits`, `not_found`, `rate_limited`, `network`, `bad_response`, `http_<status>`. Failed calls are never charged.

## The full TranscriptAPI surface

This package ships 3 curated tools for the core research loop. TranscriptAPI itself covers more ground: channel profiles, uploads, Shorts, live streams, playlists, community posts, and curated channel sections. That breadth is available today via the [REST API](https://transcriptapi.com/docs/api) or the [MCP server](https://transcriptapi.com/docs/mcp) (12 tools), and via the [n8n community node](https://github.com/ZeroPointRepo/n8n-nodes-transcriptapi) (11 operations). If your CrewAI agents need channel or playlist browsing, call the REST API directly with a custom tool, or open an issue.

## Resources

- [TranscriptAPI documentation](https://transcriptapi.com/docs)
- [REST API reference](https://transcriptapi.com/docs/api)
- [MCP reference](https://transcriptapi.com/docs/mcp)
- [Pricing](https://transcriptapi.com)
- Family: [n8n node](https://github.com/ZeroPointRepo/n8n-nodes-transcriptapi) · [MCP server](https://github.com/ZeroPointRepo/youtube-mcp) · [agent skills](https://github.com/ZeroPointRepo/youtube-skills)

## Disclosure

TranscriptAPI is an independent product and is not affiliated with or endorsed by YouTube or Google. Use of these tools is subject to the [TranscriptAPI terms](https://transcriptapi.com/terms).

## License

[MIT](LICENSE)
