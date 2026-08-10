# crewai-transcriptapi

**TranscriptAPI: hosted YouTube transcript + video-discovery API for AI agents.** CrewAI tools edition. Also available as an [n8n community node](https://github.com/ZeroPointRepo/n8n-nodes-transcriptapi), an [MCP server](https://github.com/ZeroPointRepo/youtube-mcp) and [agent skills](https://github.com/ZeroPointRepo/youtube-skills).

This package gives [CrewAI](https://www.crewai.com/) agents two tools over [TranscriptAPI](https://transcriptapi.com):

- **TranscriptAPITool**: fetch the transcript of any YouTube video (full URL, youtu.be, Shorts, or bare ID) as plain text or timestamped JSON, with metadata. The hero tool: 1 credit per call.
- **TranscriptAPISearchTool**: search YouTube for videos or channels to discover content before fetching transcripts. 1 credit per page.

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

## Usage

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
| `search_type` | str | `"video"` | `"video"` or `"channel"` |

## Response envelope

Both tools return a stable JSON string and never raise:

```json
{"success": true, "data": {"transcript": "...", "metadata": {"title": "..."}}}
```

```json
{"success": false, "error": {"code": "out_of_credits", "message": "The account is out of credits. See https://transcriptapi.com/billing."}}
```

Error codes: `missing_api_key`, `invalid_api_key`, `out_of_credits`, `not_found`, `rate_limited`, `network`, `bad_response`, `http_<status>`. Failed calls are never charged.

## Resources

- [TranscriptAPI documentation](https://transcriptapi.com/docs)
- [Pricing](https://transcriptapi.com)
- Family: [n8n node](https://github.com/ZeroPointRepo/n8n-nodes-transcriptapi) · [MCP server](https://github.com/ZeroPointRepo/youtube-mcp) · [agent skills](https://github.com/ZeroPointRepo/youtube-skills)

## Disclosure

TranscriptAPI is an independent product and is not affiliated with or endorsed by YouTube or Google. Use of these tools is subject to the [TranscriptAPI terms](https://transcriptapi.com/terms).

## License

[MIT](LICENSE)
