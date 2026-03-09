"""Pure action helpers that drive the Space UI flow."""

from __future__ import annotations

from typing import Callable, Optional

try:  # pragma: no cover - import path depends on deployment layout
    from huggingface.marketing_agent import MarketingAppError
    from huggingface.session_state import can_generate_assets, clone_state
except ModuleNotFoundError:  # pragma: no cover - Space-root fallback
    from marketing_agent import MarketingAppError
    from session_state import can_generate_assets, clone_state


def _set_status(state: dict, message: str) -> None:
    state["status_text"] = message.strip()
    state["last_error"] = ""


def _append_status(state: dict, message: str) -> None:
    current = (state.get("status_text") or "").strip()
    if current:
        state["status_text"] = f"{current}\n{message}"
    else:
        state["status_text"] = message


def generate_prompts(state: dict, brief: str, mode: str, service) -> dict:
    """Validate the brief, expand prompts, and reset previously generated assets."""
    next_state = clone_state(state)
    cleaned_brief = service.validate_marketing_input(brief, "initial creative brief")
    prompts = service.expand_prompts(cleaned_brief)

    next_state.update(
        {
            "brief": cleaned_brief,
            "generation_mode": mode,
            "feedback": "",
            "image_prompt": prompts.get("image_prompt", ""),
            "video_prompt": prompts.get("video_prompt", ""),
            "image_path": None,
            "video_path": None,
            "video_download_path": None,
        }
    )
    _set_status(next_state, "Prompts are ready for review.")
    return next_state


def refine_prompts(state: dict, feedback: str, service) -> dict:
    """Validate feedback and update the current prompts."""
    next_state = clone_state(state)
    if not next_state.get("image_prompt") and not next_state.get("video_prompt"):
        raise MarketingAppError("Generate prompts before refining them.")

    cleaned_feedback = service.validate_marketing_input(feedback, "feedback")
    prompts = service.refine_prompts(
        {
            "image_prompt": next_state.get("image_prompt", ""),
            "video_prompt": next_state.get("video_prompt", ""),
        },
        cleaned_feedback,
    )

    next_state.update(
        {
            "feedback": cleaned_feedback,
            "image_prompt": prompts.get("image_prompt", ""),
            "video_prompt": prompts.get("video_prompt", ""),
            "image_path": None,
            "video_path": None,
            "video_download_path": None,
        }
    )
    _set_status(next_state, "Prompts updated from feedback.")
    return next_state


def generate_assets(
    state: dict,
    service,
    status_callback: Optional[Callable[[str], None]] = None,
) -> dict:
    """Generate the assets required by the selected mode."""
    next_state = clone_state(state)
    if not can_generate_assets(next_state):
        raise MarketingAppError("Generate prompts before creating assets.")

    next_state["image_path"] = None
    next_state["video_path"] = None
    next_state["video_download_path"] = None
    _set_status(next_state, "Starting asset generation...")

    mode = next_state.get("generation_mode", "both")

    def on_status(message: str) -> None:
        _append_status(next_state, message)
        if status_callback:
            status_callback(message)

    if mode in {"image", "both"}:
        image_artifact = service.generate_image(next_state.get("image_prompt", ""))
        next_state["image_path"] = image_artifact.get("path")
        _append_status(next_state, "Image ready.")
        next_state["has_generated_assets"] = True

    if mode in {"video", "both"}:
        video_artifact = service.generate_video(
            next_state.get("video_prompt", ""),
            status_callback=on_status,
        )
        next_state["video_path"] = video_artifact.get("path")
        next_state["video_download_path"] = video_artifact.get("path")
        _append_status(next_state, "Video ready.")
        next_state["has_generated_assets"] = True

    return next_state


def generate_assets_from_brief(
    state: dict,
    brief: str,
    mode: str,
    service,
    status_callback: Optional[Callable[[str], None]] = None,
) -> dict:
    """Validate a fresh brief, build prompts, and generate assets in one step."""
    next_state = generate_prompts(state, brief, mode, service)
    return generate_assets(next_state, service, status_callback=status_callback)


def refine_and_generate_assets(
    state: dict,
    feedback: str,
    service,
    status_callback: Optional[Callable[[str], None]] = None,
) -> dict:
    """Optionally refine prompts using feedback and then generate assets immediately."""
    next_state = clone_state(state)
    if not next_state.get("has_generated_assets"):
        raise MarketingAppError("Generate assets before refining them.")

    if (feedback or "").strip():
        next_state = refine_prompts(next_state, feedback, service)
    else:
        next_state["feedback"] = ""

    return generate_assets(next_state, service, status_callback=status_callback)
