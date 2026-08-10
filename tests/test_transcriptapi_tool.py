"""Tests for crewai-transcriptapi. No network, no crewai install required.

crewai.tools is stubbed with faithful pydantic-based stand-ins BEFORE the tool
module imports (the DB2 test pattern: stub optional externals so import-time
validation still runs through real pydantic).
"""

import json
import os
import sys
import types
import unittest
from unittest import mock

from pydantic import BaseModel

# ── stub crewai.tools before importing the module under test ─────────────────
crewai_mod = types.ModuleType("crewai")
tools_mod = types.ModuleType("crewai.tools")


class BaseTool(BaseModel):
    """Faithful minimal stand-in: pydantic model with a run() entrypoint."""

    name: str = ""
    description: str = ""

    def run(self, **kwargs):
        return self._run(**kwargs)


class EnvVar(BaseModel):
    name: str
    description: str = ""
    required: bool = False


tools_mod.BaseTool = BaseTool
tools_mod.EnvVar = EnvVar
crewai_mod.tools = tools_mod
sys.modules.setdefault("crewai", crewai_mod)
sys.modules["crewai.tools"] = tools_mod

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from crewai_transcriptapi.transcriptapi_tool import (  # noqa: E402
    TranscriptAPISearchTool,
    TranscriptAPISearchToolSchema,
    TranscriptAPITool,
    TranscriptAPIToolSchema,
)


def _fake_response(status=200, payload=None, text=""):
    resp = mock.Mock()
    resp.status_code = status
    resp.text = text
    if payload is None:
        resp.json.side_effect = ValueError("no json")
    else:
        resp.json.return_value = payload
    return resp


class SchemaTests(unittest.TestCase):
    def test_transcript_schema_requires_video_url(self):
        with self.assertRaises(Exception):
            TranscriptAPIToolSchema()

    def test_transcript_schema_rejects_bad_format(self):
        with self.assertRaises(Exception):
            TranscriptAPIToolSchema(video_url="dQw4w9WgXcQ", output_format="xml")

    def test_transcript_schema_defaults(self):
        s = TranscriptAPIToolSchema(video_url="dQw4w9WgXcQ")
        self.assertEqual(s.output_format, "text")
        self.assertIsNone(s.language)

    def test_search_schema_bounds(self):
        with self.assertRaises(Exception):
            TranscriptAPISearchToolSchema(query="")
        with self.assertRaises(Exception):
            TranscriptAPISearchToolSchema(query="x", search_type="playlist")


class EnvTests(unittest.TestCase):
    def test_missing_key_returns_envelope_not_exception(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            out = json.loads(TranscriptAPITool().run(video_url="dQw4w9WgXcQ"))
        self.assertFalse(out["success"])
        self.assertEqual(out["error"]["code"], "missing_api_key")

    def test_env_vars_declared(self):
        tool = TranscriptAPITool()
        self.assertEqual(tool.env_vars[0].name, "TRANSCRIPTAPI_API_KEY")
        self.assertTrue(tool.env_vars[0].required)


class RequestTests(unittest.TestCase):
    def _run_with(self, resp, **kwargs):
        with mock.patch.dict(os.environ, {"TRANSCRIPTAPI_API_KEY": "sk_test"}, clear=True):
            with mock.patch("requests.get", return_value=resp) as getter:
                out = json.loads(TranscriptAPITool().run(**kwargs))
        return out, getter

    def test_request_construction(self):
        resp = _fake_response(payload={"transcript": "hello", "video_id": "dQw4w9WgXcQ"})
        out, getter = self._run_with(
            resp, video_url="dQw4w9WgXcQ", output_format="json", language="es"
        )
        self.assertTrue(out["success"])
        url = getter.call_args.args[0]
        kwargs = getter.call_args.kwargs
        self.assertEqual(url, "https://transcriptapi.com/api/v2/youtube/transcript")
        self.assertEqual(kwargs["params"]["video_url"], "dQw4w9WgXcQ")
        self.assertEqual(kwargs["params"]["format"], "json")
        self.assertEqual(kwargs["params"]["language"], "es")
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer sk_test")
        self.assertIn("crewai-transcriptapi", kwargs["headers"]["User-Agent"])

    def test_language_omitted_when_none(self):
        resp = _fake_response(payload={"transcript": "hi"})
        _, getter = self._run_with(resp, video_url="dQw4w9WgXcQ")
        self.assertNotIn("language", getter.call_args.kwargs["params"])

    def test_success_envelope(self):
        resp = _fake_response(payload={"transcript": "hello world"})
        out, _ = self._run_with(resp, video_url="dQw4w9WgXcQ")
        self.assertTrue(out["success"])
        self.assertEqual(out["data"]["transcript"], "hello world")

    def test_402_maps_to_out_of_credits(self):
        out, _ = self._run_with(_fake_response(status=402), video_url="dQw4w9WgXcQ")
        self.assertFalse(out["success"])
        self.assertEqual(out["error"]["code"], "out_of_credits")

    def test_404_and_429_and_unknown(self):
        for status, code in ((404, "not_found"), (429, "rate_limited"), (500, "http_500")):
            out, _ = self._run_with(_fake_response(status=status), video_url="dQw4w9WgXcQ")
            self.assertEqual(out["error"]["code"], code)

    def test_network_error_envelope(self):
        import requests

        with mock.patch.dict(os.environ, {"TRANSCRIPTAPI_API_KEY": "sk_test"}, clear=True):
            with mock.patch(
                "requests.get",
                side_effect=requests.exceptions.ConnectionError("boom"),
            ):
                out = json.loads(TranscriptAPITool().run(video_url="dQw4w9WgXcQ"))
        self.assertEqual(out["error"]["code"], "network")

    def test_non_json_body_envelope(self):
        out, _ = self._run_with(_fake_response(payload=None), video_url="dQw4w9WgXcQ")
        self.assertEqual(out["error"]["code"], "bad_response")


class SearchToolTests(unittest.TestCase):
    def test_search_request_and_envelope(self):
        resp = _fake_response(payload={"results": [{"title": "a video"}]})
        with mock.patch.dict(os.environ, {"TRANSCRIPTAPI_API_KEY": "sk_test"}, clear=True):
            with mock.patch("requests.get", return_value=resp) as getter:
                out = json.loads(
                    TranscriptAPISearchTool().run(query="machine learning", search_type="channel")
                )
        self.assertTrue(out["success"])
        self.assertEqual(
            getter.call_args.args[0], "https://transcriptapi.com/api/v2/youtube/search"
        )
        self.assertEqual(getter.call_args.kwargs["params"]["q"], "machine learning")
        self.assertEqual(getter.call_args.kwargs["params"]["type"], "channel")


if __name__ == "__main__":
    unittest.main()
