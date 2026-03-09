import os
import sys
import unittest
from base64 import b64encode
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from huggingface.marketing_agent import (  # noqa: E402
    MarketingAgentService,
    MarketingAppError,
    MarketingPromptPayload,
    MarketingRelevanceDecision,
    create_service_from_env,
)


class FakeResponsesAPI:
    def __init__(self, parsed_values):
        self._parsed_values = list(parsed_values)
        self.calls = []

    def parse(self, **kwargs):
        self.calls.append(kwargs)
        parsed = self._parsed_values.pop(0)
        return SimpleNamespace(status="completed", output_parsed=parsed)


class FakeClient:
    def __init__(self, parsed_values):
        self.responses = FakeResponsesAPI(parsed_values)


class FakeImagesAPI:
    def __init__(self, payload_bytes):
        self.payload_bytes = payload_bytes
        self.calls = []

    def generate(self, **kwargs):
        self.calls.append(kwargs)
        encoded = b64encode(self.payload_bytes).decode("utf-8")
        return SimpleNamespace(data=[SimpleNamespace(b64_json=encoded)])


class FakeDownloadedVideo:
    def __init__(self, payload):
        self.payload = payload

    def write_to_file(self, path):
        Path(path).write_bytes(self.payload)


class FakeVideosAPI:
    def __init__(self, statuses, payload_bytes):
        self._statuses = list(statuses)
        self.payload_bytes = payload_bytes
        self.create_calls = []
        self.retrieve_calls = []
        self.download_calls = []

    def create(self, **kwargs):
        self.create_calls.append(kwargs)
        return SimpleNamespace(id="video_123", status=self._statuses.pop(0), progress=5)

    def retrieve(self, video_id):
        self.retrieve_calls.append(video_id)
        status = self._statuses.pop(0)
        progress = 100 if status == "completed" else 75
        return SimpleNamespace(id=video_id, status=status, progress=progress)

    def download_content(self, video_id, variant="video"):
        self.download_calls.append((video_id, variant))
        return FakeDownloadedVideo(self.payload_bytes)


class FakeGenericVideosClient:
    def __init__(self, statuses, payload_bytes):
        self._statuses = list(statuses)
        self.payload_bytes = payload_bytes
        self.post_calls = []
        self.get_calls = []

    def post(self, path, *, cast_to, body=None, options=None, files=None, stream=False, stream_cls=None):
        self.post_calls.append(
            {
                "path": path,
                "cast_to": cast_to,
                "body": body,
                "options": options,
                "files": files,
                "stream": stream,
                "stream_cls": stream_cls,
            }
        )
        return {"id": "video_fallback_123", "status": self._statuses.pop(0), "progress": 5}

    def get(self, path, *, cast_to, options=None, stream=False, stream_cls=None):
        self.get_calls.append(
            {
                "path": path,
                "cast_to": cast_to,
                "options": options,
                "stream": stream,
                "stream_cls": stream_cls,
            }
        )
        if path.endswith("/content?variant=video"):
            return self.payload_bytes

        status = self._statuses.pop(0)
        progress = 100 if status == "completed" else 75
        return {"id": "video_fallback_123", "status": status, "progress": progress}


class FakeOpenAIStyleClientWithoutVideos:
    def __init__(self):
        self.default_headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": "Bearer test-key",
            "OpenAI-Project": "proj_123",
            "X-Omit-Me": object(),
        }
        self.base_url = "https://api.openai.com/v1/"


class MarketingAgentServiceTests(unittest.TestCase):
    def test_validate_marketing_input_returns_cleaned_text_when_relevant(self):
        client = FakeClient(
            [SimpleNamespace(relevant=True, reason="Marketing brief is valid.")]
        )
        service = MarketingAgentService(client=client, text_model="gpt-test")

        result = service.validate_marketing_input("  launch a spring beverage ad  ", "brief")

        self.assertEqual(result, "launch a spring beverage ad")
        self.assertEqual(client.responses.calls[0]["model"], "gpt-test")
        self.assertIs(client.responses.calls[0]["text_format"], MarketingRelevanceDecision)

    def test_validate_marketing_input_blocks_irrelevant_text(self):
        client = FakeClient(
            [SimpleNamespace(relevant=False, reason="This is unrelated to marketing.")]
        )
        service = MarketingAgentService(client=client)

        with self.assertRaisesRegex(MarketingAppError, "Only marketing-related requests"):
            service.validate_marketing_input("help me debug a Python script", "brief")

    def test_expand_prompts_returns_structured_prompt_pair(self):
        client = FakeClient(
            [
                SimpleNamespace(
                    image_prompt="Editorial citrus poster with copper highlights",
                    video_prompt="Macro bottle reveal with warm reflections",
                )
            ]
        )
        service = MarketingAgentService(client=client)

        prompts = service.expand_prompts("sparkling water launch")

        self.assertEqual(
            prompts["image_prompt"], "Editorial citrus poster with copper highlights"
        )
        self.assertEqual(
            prompts["video_prompt"], "Macro bottle reveal with warm reflections"
        )
        self.assertIs(client.responses.calls[0]["text_format"], MarketingPromptPayload)

    def test_refine_prompts_requests_structured_prompt_payload(self):
        client = FakeClient(
            [
                SimpleNamespace(
                    image_prompt="Refined editorial pastry still life",
                    video_prompt="Refined bakery window reveal",
                )
            ]
        )
        service = MarketingAgentService(client=client)

        prompts = service.refine_prompts(
            {
                "image_prompt": "Original pastry still life",
                "video_prompt": "Original bakery window reveal",
            },
            "Make it feel more neighborhood-focused.",
        )

        self.assertEqual(prompts["image_prompt"], "Refined editorial pastry still life")
        self.assertEqual(prompts["video_prompt"], "Refined bakery window reveal")
        self.assertIs(client.responses.calls[0]["text_format"], MarketingPromptPayload)

    def test_create_service_from_env_requires_openai_api_key(self):
        previous = os.environ.pop("OPENAI_API_KEY", None)
        try:
            with self.assertRaisesRegex(MarketingAppError, "OPENAI_API_KEY"):
                create_service_from_env()
        finally:
            if previous is not None:
                os.environ["OPENAI_API_KEY"] = previous

    def test_generate_image_writes_an_output_file(self):
        payload = b"fake-image-bytes"
        client = SimpleNamespace(images=FakeImagesAPI(payload))
        service = MarketingAgentService(client=client)

        with TemporaryDirectory() as tmp_dir:
            artifact = service.generate_image("hero bottle portrait", output_dir=tmp_dir)
            saved_path = Path(artifact["path"])
            self.assertTrue(saved_path.exists())
            self.assertEqual(saved_path.read_bytes(), payload)

    def test_generate_video_polls_until_completed_and_writes_file(self):
        payload = b"fake-video-bytes"
        client = SimpleNamespace(
            videos=FakeVideosAPI(["queued", "in_progress", "completed"], payload)
        )
        service = MarketingAgentService(client=client, video_poll_interval_seconds=0)
        statuses = []

        with TemporaryDirectory() as tmp_dir:
            with patch("huggingface.marketing_agent.time.sleep") as sleep_mock:
                artifact = service.generate_video(
                    "bottle reveal",
                    output_dir=tmp_dir,
                    status_callback=statuses.append,
                )
                saved_path = Path(artifact["path"])
                self.assertTrue(saved_path.exists())
                self.assertEqual(saved_path.read_bytes(), payload)
                self.assertGreaterEqual(len(client.videos.retrieve_calls), 2)
                self.assertIn("Status: in_progress", statuses[0])
                sleep_mock.assert_called()

    def test_generate_video_uses_generic_http_fallback_when_videos_resource_is_missing(self):
        payload = b"fake-fallback-video-bytes"
        client = FakeGenericVideosClient(["queued", "in_progress", "completed"], payload)
        service = MarketingAgentService(client=client, video_poll_interval_seconds=0)
        statuses = []

        with TemporaryDirectory() as tmp_dir:
            with patch("huggingface.marketing_agent.time.sleep") as sleep_mock:
                artifact = service.generate_video(
                    "bakery storefront reveal",
                    output_dir=tmp_dir,
                    status_callback=statuses.append,
                )
                saved_path = Path(artifact["path"])
                self.assertTrue(saved_path.exists())
                self.assertEqual(saved_path.read_bytes(), payload)
                self.assertEqual(client.post_calls[0]["path"], "/videos")
                self.assertEqual(client.post_calls[0]["cast_to"], dict)
                self.assertEqual(
                    client.post_calls[0]["files"],
                    [
                        ("model", (None, service.video_model)),
                        ("prompt", (None, "bakery storefront reveal")),
                        ("size", (None, service.video_size)),
                        ("seconds", (None, service.video_duration_seconds)),
                    ],
                )
                self.assertEqual(
                    client.get_calls[-1]["path"],
                    "/videos/video_fallback_123/content?variant=video",
                )
                self.assertIn("Status: in_progress", statuses[0])
                sleep_mock.assert_called()

    def test_start_video_generation_uses_raw_multipart_request_when_openai_client_lacks_videos_resource(self):
        client = FakeOpenAIStyleClientWithoutVideos()
        service = MarketingAgentService(client=client)
        response = unittest.mock.Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {"id": "video_http_123", "status": "queued", "progress": 0}
        http_client = unittest.mock.Mock()
        http_client.__enter__ = unittest.mock.Mock(return_value=http_client)
        http_client.__exit__ = unittest.mock.Mock(return_value=False)
        http_client.post.return_value = response

        with patch("huggingface.marketing_agent.httpx.Client", return_value=http_client):
            job = service.start_video_generation("pastry reveal")

        self.assertEqual(job.id, "video_http_123")
        self.assertEqual(job.status, "queued")
        http_client.post.assert_called_once()
        _, kwargs = http_client.post.call_args
        self.assertEqual(kwargs["url"], "https://api.openai.com/v1/videos")
        self.assertNotIn("Content-Type", kwargs["headers"])
        self.assertNotIn("X-Omit-Me", kwargs["headers"])
        self.assertEqual(
            kwargs["files"],
            service._video_form_fields("pastry reveal"),
        )

    def test_poll_and_download_video_use_raw_http_when_openai_client_lacks_videos_resource(self):
        client = FakeOpenAIStyleClientWithoutVideos()
        service = MarketingAgentService(client=client)
        status_response = unittest.mock.Mock()
        status_response.raise_for_status.return_value = None
        status_response.json.return_value = {
            "id": "video_http_123",
            "status": "completed",
            "progress": 100,
        }
        content_response = unittest.mock.Mock()
        content_response.raise_for_status.return_value = None
        content_response.content = b"video-bytes"
        http_client = unittest.mock.Mock()
        http_client.__enter__ = unittest.mock.Mock(return_value=http_client)
        http_client.__exit__ = unittest.mock.Mock(return_value=False)
        http_client.get.side_effect = [status_response, content_response]

        with TemporaryDirectory() as tmp_dir:
            with patch("huggingface.marketing_agent.httpx.Client", return_value=http_client):
                status = service.poll_video_status("video_http_123")
                artifact = service.download_video("video_http_123", output_dir=tmp_dir)
                saved_path = Path(artifact["path"])
                self.assertEqual(status.id, "video_http_123")
                self.assertEqual(status.status, "completed")
                self.assertTrue(saved_path.exists())
                self.assertEqual(saved_path.read_bytes(), b"video-bytes")
                first_get = http_client.get.call_args_list[0].kwargs
                second_get = http_client.get.call_args_list[1].kwargs
                self.assertEqual(first_get["url"], "https://api.openai.com/v1/videos/video_http_123")
                self.assertEqual(
                    second_get["url"],
                    "https://api.openai.com/v1/videos/video_http_123/content?variant=video",
                )
                self.assertNotIn("Content-Type", first_get["headers"])
                self.assertNotIn("Content-Type", second_get["headers"])


if __name__ == "__main__":
    unittest.main()
