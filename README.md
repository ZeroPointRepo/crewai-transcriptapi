# crewai-transcriptapi

**TranscriptAPI: hosted YouTube transcript + video-discovery API for AI agents.** CrewAI tools edition. Also available as an [n8n community node](https://github.com/ZeroPointRepo/n8n-nodes-transcriptapi), an [MCP server](https://github.com/ZeroPointRepo/youtube-mcp) and [agent skills](https://github.com/ZeroPointRepo/youtube-skills).

Fetch a YouTube transcript, search YouTube, and pull a video's metadata from a CrewAI agent, via three tools over [TranscriptAPI](https://transcriptapi.com). For Python developers building research, summarization, fact-checking, or content-analysis agents.

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

## Tools

### TranscriptAPITool

Fetches the transcript of a YouTube video.

- **Inputs:** `video_url` (str, required) full URL or bare 11-character ID; `output_format` (str, default `"text"`) `"text"` or `"json"`; `language` (str, optional) preferred transcript language code, e.g. `"es"`.
- **Output:** a JSON envelope containing the transcript (plain text or timestamped segments) plus video metadata (title, author, thumbnail); metadata is always included.
- **Use for:** reading, quoting, translating, or summarizing what was said in a video.

### TranscriptAPISearchTool

Searches YouTube for videos, channels, playlists, or movies.

- **Inputs:** `query` (str, required); `search_type` (str, default `"video"`) `"video"`, `"channel"`, `"playlist"`, or `"movie"`; optional `sort` (`"relevance"`/`"views"`), `upload_date` (`hour`/`today`/`week`/`month`/`year`, videos only), `duration` (`short`/`medium`/`long`, videos only), `features` (comma-separated, e.g. `"hd,subtitles"`).
- **Output:** a JSON envelope with a `results` list (titles, IDs, thumbnails, view counts, publish dates). This tool always requests the first page; it does not expose the API's continuation token for further pages.
- **Use for:** finding videos, channels, playlists, or movies about a topic before pulling anything else.

### TranscriptAPIVideoMetadataTool

Fetches a video's metadata without touching captions.

- **Inputs:** `video_url` (str, required); `include` (str, optional) comma-separated `"details"` and/or `"related"`.
- **Output:** a JSON envelope with view/like-count text, publish date, description, uploading-channel summary, and thumbnails; `include=details` adds duration, category, tags, and the caption-track inventory; `include=related` adds related videos.
- **Use for:** checking a video's counts, publish date, description, or related videos, without spending a call on its transcript.

The full REST API and MCP server expose more: channel profiles, uploads, Shorts, streams, playlists, community posts, and curated sections. See [Resources](#resources).

## When to use what

| Job | Reach for |
|---|---|
| Read, quote, translate, or summarize what was said in a video | `TranscriptAPITool` |
| Find videos, channels, playlists, or movies about a topic | `TranscriptAPISearchTool` |
| Check a video's counts, publish date, description, or related videos before transcribing it | `TranscriptAPIVideoMetadataTool` |
| Need a channel's profile, uploads, playlists, posts, or sections | Step up to the REST API or MCP server; not exposed by this package |

## Use cases

- **Screen before you transcribe.** `TranscriptAPISearchTool` (`search_type="video"`, `sort="views"`) shortlists candidates on a topic, `TranscriptAPIVideoMetadataTool` checks each one's publish date and view count, `TranscriptAPITool` transcribes only the ones worth it.
- **Verify, then quote.** Given a video URL, `TranscriptAPIVideoMetadataTool` confirms the uploading channel and publish date, `TranscriptAPITool` pulls the transcript for the agent to quote from.
- **Beyond this package.** `TranscriptAPISearchTool` (`search_type="playlist"`) finds a playlist on a topic; listing that playlist's videos or browsing the channel that made it are REST/MCP operations (`playlist/videos`, `channel/videos`), not part of this package's 3 tools.

## Costs

A successful call costs 1 credit: `TranscriptAPITool` per transcript, `TranscriptAPISearchTool` per call (first page only), `TranscriptAPIVideoMetadataTool` per lookup (`include` does not change the price). Failed calls and rate-limited (429) calls cost 0.

## Response envelope

All three tools return a JSON string and never raise:

```json
{"success": true, "data": {"transcript": "...", "metadata": {"title": "..."}}}
```

```json
{"success": false, "error": {"code": "out_of_credits", "message": "The account is out of credits. See https://transcriptapi.com/billing."}}
```

Error codes: `missing_api_key`, `invalid_api_key`, `out_of_credits`, `not_found`, `rate_limited`, `network`, `bad_response`, `http_<status>`.

## Resources

- TranscriptAPI documentation: [https://transcriptapi.com/docs](https://transcriptapi.com/docs)
- REST API reference: [https://transcriptapi.com/docs/api](https://transcriptapi.com/docs/api)
- MCP reference: [https://transcriptapi.com/docs/mcp](https://transcriptapi.com/docs/mcp)
- [Pricing](https://transcriptapi.com)
- Family: [n8n node](https://github.com/ZeroPointRepo/n8n-nodes-transcriptapi) · [MCP server](https://github.com/ZeroPointRepo/youtube-mcp) · [agent skills](https://github.com/ZeroPointRepo/youtube-skills)

## Disclosure

TranscriptAPI is an independent product and is not affiliated with or endorsed by YouTube or Google. Use of these tools is subject to the [TranscriptAPI terms](https://transcriptapi.com/terms).

## License

[MIT](LICENSE)
