"""Reusable OpenAI-backed marketing agent functions for the Space app."""

from __future__ import annotations

import base64
import os
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, Optional
from urllib.parse import quote

import httpx
from pydantic import BaseModel, Field


class MarketingAppError(RuntimeError):
    """Raised when the app cannot continue due to invalid input or configuration."""


class MarketingRelevanceDecision(BaseModel):
    """Structured classifier output for marketing relevance checks."""

    relevant: bool
    reason: str = Field(default="")


class MarketingPromptPayload(BaseModel):
    """Structured prompt payload returned by the text model."""

    image_prompt: str
    video_prompt: str


@dataclass
class MarketingAgentService:
    """Thin wrapper around the OpenAI APIs used by the notebook flow."""

    client: Any
    text_model: str = "gpt-5-mini"
    image_model: str = "gpt-image-1.5"
    video_model: str = "sora-2"
    text_reasoning_effort: str = "minimal"
    image_prompt_word_limit: int = 120
    video_prompt_word_limit: int = 160
    video_duration_seconds: str = "8"
    image_size: str = "1024x1536"
    image_quality: str = "medium"
    video_size: str = "720x1280"
    video_poll_interval_seconds: int = 10

    def validate_marketing_input(self, text: str, input_label: str = "user input") -> str:
        """Reject non-marketing prompts using the text model classifier."""
        cleaned = text.strip()
        if not cleaned:
            raise MarketingAppError(
                f"{input_label.capitalize()} cannot be empty. The session has been stopped."
            )

        parsed = self._parse_text_response(
            instructions=(
                "You are a strict relevance classifier for a marketing content generation tool. "
                "Return relevant=true when the text is usable as a marketing brief, business or product "
                "description, brand context, campaign idea, creative direction, ad concept, or prompt "
                "refinement request, even if it is short or not phrased as a direct command. "
                "Examples that should be allowed include short brand descriptions like "
                "'small bakery in downtown Chicago' or product concepts like 'sparkling tea for rooftop bars'. "
                "Return relevant=false only when the text is clearly unrelated to marketing or promotional "
                "content creation."
            ),
            input_text=f"Input label: {input_label}\nUser text: {cleaned}",
            schema=MarketingRelevanceDecision,
            failure_message="The model returned no marketing relevance decision. The session has been stopped.",
        )
        if not getattr(parsed, "relevant", False):
            raise MarketingAppError(
                "Only marketing-related requests are allowed. The session has been stopped."
            )

        return cleaned

    def expand_prompts(self, brief: str) -> Dict[str, str]:
        """Expand a short brief into structured image and video prompts."""
        parsed = self._parse_text_response(
            instructions=(
                "Create concise production-ready image and video prompts for a marketing campaign. "
                "If the user provides only a business, product, or brand description, infer a strong "
                "campaign direction from that context."
            ),
            input_text=f"User request: {brief}",
            schema=MarketingPromptPayload,
            failure_message="The model returned no prompt payload.",
        )

        return {
            "image_prompt": getattr(parsed, "image_prompt", "").strip(),
            "video_prompt": getattr(parsed, "video_prompt", "").strip(),
        }

    def refine_prompts(self, current_prompts: Dict[str, str], feedback: str) -> Dict[str, str]:
        """Refine the existing prompts based on user feedback."""
        parsed = self._parse_text_response(
            instructions="Refine the current marketing prompts using the feedback provided.",
            input_text=(
                f"Current image prompt:\n{current_prompts.get('image_prompt', '')}\n\n"
                f"Current video prompt:\n{current_prompts.get('video_prompt', '')}\n\n"
                f"Feedback:\n{feedback}"
            ),
            schema=MarketingPromptPayload,
            failure_message="The model returned no prompt payload.",
        )

        return {
            "image_prompt": getattr(parsed, "image_prompt", "").strip(),
            "video_prompt": getattr(parsed, "video_prompt", "").strip(),
        }

    def generate_image(self, image_prompt: str, output_dir: Optional[str] = None) -> Dict[str, str]:
        """Generate an image artifact and save it to local runtime storage."""
        prompt = image_prompt.strip()
        if not prompt:
            raise MarketingAppError("No image prompt is available.")

        response = self.client.images.generate(
            model=self.image_model,
            prompt=prompt,
            size=self.image_size,
            quality=self.image_quality,
        )

        image_payload = getattr(response.data[0], "b64_json", None)
        if not image_payload:
            raise MarketingAppError("The image API returned no image payload.")

        output_path = _build_output_path(output_dir, "marketing-image", ".png")
        output_path.write_bytes(base64.b64decode(image_payload))
        return {"path": str(output_path)}

    def generate_video(
        self,
        video_prompt: str,
        output_dir: Optional[str] = None,
        status_callback=None,
    ) -> Dict[str, str]:
        """Generate a video artifact, poll until completion, and save it locally."""
        prompt = video_prompt.strip()
        if not prompt:
            raise MarketingAppError("No video prompt is available.")

        video = self.start_video_generation(prompt)

        while getattr(video, "status", None) in {"queued", "in_progress"}:
            time.sleep(self.video_poll_interval_seconds)
            video = self.poll_video_status(video.id)
            progress = getattr(video, "progress", 0)
            if status_callback:
                status_callback(f"Status: {video.status} | Progress: {progress}%")

        if getattr(video, "status", None) == "failed":
            error = getattr(getattr(video, "error", None), "message", "")
            raise MarketingAppError(error or "Video generation failed.")

        return self.download_video(video.id, output_dir=output_dir)

    def start_video_generation(self, video_prompt: str):
        """Start a remote video job and return the provider job object."""
        prompt = video_prompt.strip()
        if not prompt:
            raise MarketingAppError("No video prompt is available.")

        videos_api = getattr(self.client, "videos", None)
        if videos_api is not None:
            return videos_api.create(
                model=self.video_model,
                prompt=prompt,
                size=self.video_size,
                seconds=self.video_duration_seconds,
            )

        if self._supports_raw_video_http():
            payload = self._start_video_generation_via_http(prompt)
        else:
            payload = self.client.post(
                "/videos",
                cast_to=dict,
                files=self._video_form_fields(prompt),
            )
        return _coerce_api_namespace(
            payload,
            failure_message="The video API returned no job payload.",
        )

    def poll_video_status(self, video_id: str):
        """Retrieve the latest status for a remote video job."""
        videos_api = getattr(self.client, "videos", None)
        if videos_api is not None:
            return videos_api.retrieve(video_id)

        if self._supports_raw_video_http():
            payload = self._poll_video_status_via_http(video_id)
        else:
            payload = self.client.get(
                f"/videos/{quote(video_id, safe='')}",
                cast_to=dict,
            )
        return _coerce_api_namespace(
            payload,
            failure_message="The video API returned no status payload.",
        )

    def download_video(self, video_id: str, output_dir: Optional[str] = None) -> Dict[str, str]:
        """Download the completed video artifact to local runtime storage."""
        output_path = _build_output_path(output_dir, "marketing-video", ".mp4")
        videos_api = getattr(self.client, "videos", None)
        if videos_api is not None:
            content = videos_api.download_content(video_id, variant="video")
            content.write_to_file(output_path)
            return {"path": str(output_path)}

        if self._supports_raw_video_http():
            content = self._download_video_via_http(video_id)
        else:
            content = self.client.get(
                f"/videos/{quote(video_id, safe='')}/content?variant=video",
                cast_to=bytes,
            )
        if not content:
            raise MarketingAppError("The video API returned no downloadable video payload.")
        output_path.write_bytes(content)
        return {"path": str(output_path)}

    def _video_form_fields(self, prompt: str) -> list[tuple[str, tuple[None, str]]]:
        """Build multipart form fields for the REST video creation fallback."""
        return [
            ("model", (None, self.video_model)),
            ("prompt", (None, prompt)),
            ("size", (None, self.video_size)),
            ("seconds", (None, self.video_duration_seconds)),
        ]

    def _start_video_generation_via_http(self, prompt: str) -> Dict[str, Any]:
        """Call the REST video endpoint directly when the SDK helper resource is unavailable."""
        headers = self._video_http_headers()
        url = self._video_url("")

        try:
            with httpx.Client(timeout=getattr(self.client, "timeout", None)) as http_client:
                response = http_client.post(
                    url=url,
                    headers=headers,
                    files=self._video_form_fields(prompt),
                )
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise MarketingAppError(
                _extract_http_error_message(
                    exc.response,
                    default_message="Video generation failed.",
                )
            ) from exc
        except httpx.HTTPError as exc:
            raise MarketingAppError("Video generation request failed.") from exc

        return response.json()

    def _poll_video_status_via_http(self, video_id: str) -> Dict[str, Any]:
        """Fetch a video job status via raw HTTP when the helper resource is unavailable."""
        try:
            with httpx.Client(timeout=getattr(self.client, "timeout", None)) as http_client:
                response = http_client.get(
                    url=self._video_url(video_id),
                    headers=self._video_http_headers(),
                )
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise MarketingAppError(
                _extract_http_error_message(
                    exc.response,
                    default_message="Unable to retrieve video status.",
                )
            ) from exc
        except httpx.HTTPError as exc:
            raise MarketingAppError("Video status request failed.") from exc

        return response.json()

    def _download_video_via_http(self, video_id: str) -> bytes:
        """Download video bytes via raw HTTP when the helper resource is unavailable."""
        try:
            with httpx.Client(timeout=getattr(self.client, "timeout", None)) as http_client:
                response = http_client.get(
                    url=self._video_url(f"{video_id}/content?variant=video"),
                    headers=self._video_http_headers(),
                )
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise MarketingAppError(
                _extract_http_error_message(
                    exc.response,
                    default_message="Unable to download the generated video.",
                )
            ) from exc
        except httpx.HTTPError as exc:
            raise MarketingAppError("Video download request failed.") from exc

        return response.content

    def _supports_raw_video_http(self) -> bool:
        """Return whether the client exposes enough config for direct HTTP fallback calls."""
        return hasattr(self.client, "default_headers") and hasattr(self.client, "base_url")

    def _video_http_headers(self) -> Dict[str, str | bytes]:
        """Build safe HTTP headers for raw video endpoint requests."""
        return {
            key: value
            for key, value in dict(getattr(self.client, "default_headers", {})).items()
            if key.lower() != "content-type" and isinstance(value, (str, bytes))
        }

    def _video_url(self, relative_path: str) -> str:
        """Build a full video endpoint URL from the configured OpenAI base URL."""
        base_url = str(self.client.base_url).rstrip("/")
        clean_path = relative_path.lstrip("/")
        if clean_path:
            return f"{base_url}/videos/{clean_path}"
        return f"{base_url}/videos"

    def _parse_text_response(
        self,
        *,
        instructions: str,
        input_text: str,
        schema: type[BaseModel],
        failure_message: str,
    ) -> BaseModel:
        """Request structured output from the text model and return the parsed payload."""
        try:
            response = self.client.responses.parse(
                model=self.text_model,
                reasoning={"effort": self.text_reasoning_effort},
                instructions=instructions,
                input=input_text,
                text_format=schema,
            )
        except Exception as exc:
            raise MarketingAppError(failure_message) from exc

        parsed = getattr(response, "output_parsed", None)
        if parsed is None:
            raise MarketingAppError(failure_message)
        return parsed


def create_service_from_env() -> MarketingAgentService:
    """Build a service from environment variables without importing OpenAI too early."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise MarketingAppError(
            "OPENAI_API_KEY is not set. Add it to the environment or Hugging Face Space secrets."
        )

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise MarketingAppError(
            "The OpenAI SDK is not installed. Install requirements before running the Space."
        ) from exc

    client = OpenAI(api_key=api_key)
    return MarketingAgentService(client=client)


def _build_output_path(output_dir: Optional[str], prefix: str, suffix: str) -> Path:
    """Create a unique runtime artifact path."""
    target_dir = Path(output_dir or ".").resolve()
    target_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{prefix}-{uuid.uuid4().hex[:8]}{suffix}"
    return target_dir / filename


def _coerce_api_namespace(payload: Any, *, failure_message: str) -> SimpleNamespace:
    """Convert a mapping payload into dot-access attributes for the app flow."""
    if not isinstance(payload, dict):
        raise MarketingAppError(failure_message)
    return _namespaceify(payload)


def _extract_http_error_message(response: httpx.Response, *, default_message: str) -> str:
    """Pull a readable provider error message from an HTTP response."""
    try:
        payload = response.json()
    except ValueError:
        return default_message

    error = payload.get("error") if isinstance(payload, dict) else None
    if isinstance(error, dict):
        message = error.get("message")
        if isinstance(message, str) and message.strip():
            return message.strip()
    return default_message


def _namespaceify(value: Any) -> Any:
    """Recursively convert API mappings into SimpleNamespace instances."""
    if isinstance(value, dict):
        return SimpleNamespace(**{key: _namespaceify(item) for key, item in value.items()})
    if isinstance(value, list):
        return [_namespaceify(item) for item in value]
    return value
