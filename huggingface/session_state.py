"""Session-state helpers for the Hugging Face Space app."""

from copy import deepcopy
from typing import Dict, Optional


SessionState = Dict[str, Optional[str]]


def build_initial_session_state() -> dict:
    """Return the default per-session state for the Gradio app."""
    return {
        "brief": "",
        "generation_mode": "both",
        "feedback": "",
        "image_prompt": "",
        "video_prompt": "",
        "has_generated_assets": False,
        "status_text": "Enter a marketing brief to begin.",
        "image_path": None,
        "video_path": None,
        "video_download_path": None,
        "last_error": "",
    }


def clone_state(state: Optional[dict]) -> dict:
    """Create a detached state copy suitable for Gradio session updates."""
    return deepcopy(state or build_initial_session_state())


def can_generate_assets(state: Optional[dict]) -> bool:
    """Return True when the selected mode has the prompts required to run generation."""
    session = state or {}
    mode = session.get("generation_mode", "both")
    image_prompt = (session.get("image_prompt") or "").strip()
    video_prompt = (session.get("video_prompt") or "").strip()

    if mode == "image":
        return bool(image_prompt)
    if mode == "video":
        return bool(video_prompt)
    return bool(image_prompt and video_prompt)


def can_refine_after_generation(state: Optional[dict]) -> bool:
    """Return True when the user has already generated assets in this session."""
    session = state or {}
    return bool(session.get("has_generated_assets"))
