"""Gradio Hugging Face Space for the OpenAI-backed marketing agent."""

from __future__ import annotations

import html
import tempfile
import time
from pathlib import Path
from typing import Callable, Tuple

import gradio as gr

try:  # pragma: no cover - import path depends on deployment layout
    from huggingface.actions import generate_prompts, refine_prompts
    from huggingface.marketing_agent import MarketingAppError, create_service_from_env
    from huggingface.session_state import (
        build_initial_session_state,
        can_generate_assets,
        can_refine_after_generation,
        clone_state,
    )
except ModuleNotFoundError:  # pragma: no cover - Space-root fallback
    from actions import generate_prompts, refine_prompts
    from marketing_agent import MarketingAppError, create_service_from_env
    from session_state import (
        build_initial_session_state,
        can_generate_assets,
        can_refine_after_generation,
        clone_state,
    )


APP_TITLE = "Campaign Studio"
APP_SUBTITLE = (
    "Turn a raw marketing brief into polished prompts and launch-ready campaign assets "
    "in one pass, then refine and regenerate once the first render is ready."
)
RUNTIME_DIR = Path(tempfile.gettempdir()) / "marketing-space-assets"


CUSTOM_CSS = """
:root {
  --canvas: #f4ecdf;
  --surface: rgba(255, 251, 245, 0.88);
  --surface-strong: #fff9f0;
  --ink: #231714;
  --muted: #5d4a42;
  --accent: #ab5c33;
  --accent-soft: rgba(171, 92, 51, 0.16);
  --line: rgba(35, 23, 20, 0.12);
  --success: #215c48;
  --warning: #8b5c18;
  --error: #902f22;
  --shadow: 0 28px 60px rgba(59, 35, 18, 0.12);
}

body, .gradio-container {
  background:
    radial-gradient(circle at top left, rgba(171, 92, 51, 0.18), transparent 28%),
    radial-gradient(circle at top right, rgba(33, 92, 72, 0.12), transparent 24%),
    linear-gradient(180deg, #f8f1e8 0%, var(--canvas) 100%);
  color: var(--ink);
  font-family: "IBM Plex Sans", sans-serif;
}

.gradio-container {
  max-width: 1400px !important;
  padding: 24px 18px 40px !important;
}

.studio-shell {
  position: relative;
}

.studio-shell::before {
  content: "";
  position: absolute;
  inset: 8px 12px auto auto;
  width: 180px;
  height: 180px;
  background: radial-gradient(circle, rgba(171, 92, 51, 0.12), transparent 68%);
  filter: blur(8px);
  pointer-events: none;
}

.hero-card, .panel-card {
  background: var(--surface);
  border: 1px solid rgba(255, 255, 255, 0.4);
  border-radius: 28px;
  box-shadow: var(--shadow);
  backdrop-filter: blur(16px);
}

.hero-card {
  padding: 28px 30px 24px;
  overflow: hidden;
  position: relative;
}

.hero-card::after {
  content: "";
  position: absolute;
  inset: auto -22px -26px auto;
  width: 170px;
  height: 170px;
  border-radius: 999px;
  background: linear-gradient(145deg, rgba(171, 92, 51, 0.28), rgba(171, 92, 51, 0));
}

.hero-kicker {
  display: inline-block;
  padding: 7px 12px;
  border-radius: 999px;
  background: rgba(35, 23, 20, 0.06);
  color: var(--muted);
  letter-spacing: 0.16em;
  text-transform: uppercase;
  font-size: 11px;
  font-weight: 600;
}

.hero-title {
  margin: 16px 0 10px;
  font-family: "Fraunces", serif;
  font-size: clamp(2.6rem, 4vw, 4.5rem);
  line-height: 0.94;
  letter-spacing: -0.04em;
}

.hero-copy {
  max-width: 760px;
  color: var(--muted);
  font-size: 1rem;
  line-height: 1.65;
}

.panel-card {
  padding: 22px;
}

.panel-title {
  margin: 0 0 14px;
  font-family: "Fraunces", serif;
  font-size: 1.3rem;
  letter-spacing: -0.03em;
  color: var(--ink) !important;
}

.panel-note {
  margin: 0 0 16px;
  color: var(--muted);
  font-size: 0.95rem;
}

.hero-title,
.hero-copy,
.panel-card h1,
.panel-card h2,
.panel-card h3,
.panel-card p,
.panel-card label,
.panel-card .label-wrap,
.panel-card .label-wrap span,
.panel-card .block-title,
.panel-card .block-info,
.panel-card .block_label,
.panel-card .block_label span,
.media-frame label,
.media-frame .label-wrap {
  color: var(--ink) !important;
}

.panel-card label > span,
.panel-card fieldset > span,
.panel-card .container > span,
.prompt-box label > span,
.status-box label > span,
.media-frame label > span {
  color: var(--muted) !important;
  font-weight: 500 !important;
}

.status-banner {
  border-radius: 20px;
  padding: 16px 18px;
  font-size: 0.95rem;
  line-height: 1.5;
  border: 1px solid var(--line);
  background: var(--surface-strong);
  color: var(--ink) !important;
}

.status-banner strong,
.status-banner span,
.status-banner div,
.status-banner p {
  display: block;
  margin-bottom: 2px;
  font-size: 0.8rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: inherit !important;
}

.status-banner div,
.status-banner p {
  display: initial;
  margin-bottom: 0;
  font-size: 0.95rem;
  letter-spacing: normal;
  text-transform: none;
}

.status-banner--neutral strong { color: var(--muted); }
.status-banner--ready strong,
.status-banner--success strong { color: var(--success); }
.status-banner--warning strong { color: var(--warning); }
.status-banner--error strong { color: var(--error); }

.status-banner--error {
  background: rgba(144, 47, 34, 0.09);
  border-color: rgba(144, 47, 34, 0.16);
}

.status-banner--warning {
  background: rgba(139, 92, 24, 0.09);
  border-color: rgba(139, 92, 24, 0.16);
}

.status-banner--success,
.status-banner--ready {
  background: rgba(33, 92, 72, 0.1);
  border-color: rgba(33, 92, 72, 0.18);
}

.panel-card .form,
.panel-card .block,
.panel-card .input-container,
.panel-card .container,
.panel-card .wrap,
.panel-card .icon-button-wrapper,
.media-frame .form,
.media-frame .block,
.media-frame .empty,
.media-frame .wrap,
.media-frame .container {
  background: rgba(255, 249, 240, 0.82) !important;
  color: var(--ink) !important;
  border-color: rgba(35, 23, 20, 0.14) !important;
  box-shadow: none !important;
}

.panel-card .form {
  background: transparent !important;
}

.panel-card .block,
.media-frame .block {
  border-radius: 20px !important;
}

.panel-card .block button,
.panel-card .icon-button,
.media-frame .icon-button,
.media-frame button {
  color: var(--ink) !important;
}

.controls fieldset label,
.controls .wrap label,
.controls .wrap label.selected,
.controls fieldset label.selected,
.controls fieldset label span,
.controls .wrap label span {
  background: rgba(255, 249, 240, 0.95) !important;
  color: var(--ink) !important;
  border-color: rgba(35, 23, 20, 0.18) !important;
  box-shadow: none !important;
}

.controls fieldset label.selected,
.controls .wrap label.selected {
  background: rgba(244, 231, 212, 0.98) !important;
  border-color: rgba(171, 92, 51, 0.42) !important;
}

.controls fieldset label input,
.controls .wrap label input {
  accent-color: var(--accent) !important;
}

.prompt-box textarea,
.controls textarea,
.controls input,
.status-box textarea {
  background: rgba(255, 255, 255, 0.52) !important;
  border: 1px solid var(--line) !important;
  border-radius: 18px !important;
  color: var(--ink) !important;
  font-family: "IBM Plex Sans", sans-serif !important;
  caret-color: var(--accent) !important;
}

.controls textarea::placeholder,
.status-box textarea::placeholder,
.prompt-box textarea::placeholder {
  color: rgba(93, 74, 66, 0.72) !important;
}

.status-box textarea {
  font-family: "IBM Plex Mono", monospace !important;
  font-size: 0.83rem !important;
}

.controls .gr-button-primary {
  background: linear-gradient(135deg, #8c4927, #c97245) !important;
  border: none !important;
  color: #fff8f1 !important;
}

.controls .gr-button-secondary {
  background: rgba(35, 23, 20, 0.06) !important;
  color: var(--ink) !important;
  border: 1px solid rgba(35, 23, 20, 0.12) !important;
}

.media-frame {
  border-radius: 22px;
  overflow: hidden;
  border: 1px solid rgba(35, 23, 20, 0.08);
}

.media-frame img,
.media-frame video,
.media-frame .empty {
  background: rgba(255, 252, 247, 0.9) !important;
}

.media-frame .float,
.media-frame .label-wrap,
.media-frame .icon-button-wrapper button,
.prompt-box .icon-button,
.status-box .icon-button {
  background: rgba(255, 249, 240, 0.96) !important;
  color: var(--ink) !important;
  border-color: rgba(35, 23, 20, 0.14) !important;
}

@media (max-width: 900px) {
  .gradio-container {
    padding: 14px 10px 26px !important;
  }

  .hero-card,
  .panel-card {
    border-radius: 22px;
    padding: 18px;
  }

  .hero-title {
    font-size: 2.3rem;
  }
}
"""

CUSTOM_HEAD = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link
  href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap"
  rel="stylesheet"
>
"""


def _build_banner(message: str, tone: str = "neutral") -> str:
    tone = tone if tone in {"neutral", "ready", "success", "warning", "error"} else "neutral"
    safe_message = html.escape(message or "Ready.")
    label = {
        "neutral": "Studio Status",
        "ready": "OpenAI Ready",
        "success": "Success",
        "warning": "Configuration",
        "error": "Blocked",
    }[tone]
    return (
        f'<div class="status-banner status-banner--{tone}">'
        f"<strong>{label}</strong>{safe_message}</div>"
    )


def _startup_banner(service_factory: Callable[[], object]) -> Tuple[str, str]:
    try:
        service_factory()
    except MarketingAppError as exc:
        return str(exc), "warning"
    except Exception as exc:  # pragma: no cover - defensive startup path
        return f"Startup warning: {exc}", "warning"
    return "OpenAI service available. Generate assets to begin.", "ready"


def _outputs_from_state(state: dict, banner_message: str, banner_tone: str):
    can_refine = can_refine_after_generation(state)
    return (
        state,
        _build_banner(banner_message, banner_tone),
        state.get("image_prompt", ""),
        state.get("video_prompt", ""),
        state.get("image_path"),
        state.get("video_path"),
        state.get("video_download_path"),
        gr.update(value=state.get("feedback", ""), interactive=can_refine),
        gr.update(interactive=can_refine),
    )


def _append_status(state: dict, message: str) -> None:
    current = (state.get("status_text") or "").strip()
    if current:
        state["status_text"] = f"{current}\n{message}"
    else:
        state["status_text"] = message


def build_demo(service_factory: Callable[[], object] = create_service_from_env) -> gr.Blocks:
    """Build the Gradio Blocks app for the Hugging Face Space."""
    startup_message, startup_tone = _startup_banner(service_factory)

    with gr.Blocks(
        title=APP_TITLE,
        css=CUSTOM_CSS,
        head=CUSTOM_HEAD,
        fill_height=True,
        analytics_enabled=False,
    ) as demo:
        session_state = gr.State(build_initial_session_state())

        with gr.Column(elem_classes=["studio-shell"]):
            gr.HTML(
                f"""
                <section class="hero-card">
                  <span class="hero-kicker">Hugging Face Space</span>
                  <h1 class="hero-title">{APP_TITLE}</h1>
                  <p class="hero-copy">{APP_SUBTITLE}</p>
                </section>
                """,
                padding=True,
            )

            with gr.Row(equal_height=False):
                with gr.Column(scale=5, elem_classes=["controls"]):
                    with gr.Column(elem_classes=["panel-card"]):
                        gr.HTML('<h2 class="panel-title">Creative Brief</h2>', padding=True)
                        gr.HTML(
                            '<p class="panel-note">Start with a concise campaign request. The studio will generate '
                            "the prompts and render the final assets in one pass.</p>",
                            padding=True,
                        )
                        brief_box = gr.Textbox(
                            label="Marketing Brief",
                            lines=6,
                            placeholder="Launch a premium sparkling tea for summer rooftop bars...",
                        )
                        mode_select = gr.Radio(
                            label="Generation Mode",
                            choices=["image", "video", "both"],
                            value="both",
                        )
                        generate_brief_assets_button = gr.Button(
                            "Generate Assets",
                            variant="primary",
                            size="lg",
                        )

                    with gr.Column(elem_classes=["panel-card"]):
                        gr.HTML('<h2 class="panel-title">Refinement Loop</h2>', padding=True)
                        gr.HTML(
                            '<p class="panel-note">After the first render, add feedback here and generate again. '
                            "The prompts update automatically before the new assets are created.</p>",
                            padding=True,
                        )
                        feedback_box = gr.Textbox(
                            label="Refinement Feedback",
                            lines=4,
                            placeholder="Make it feel more premium and editorial.",
                            interactive=False,
                        )
                        refine_generate_assets_button = gr.Button(
                            "Generate Assets",
                            variant="primary",
                            interactive=False,
                        )

                with gr.Column(scale=7):
                    status_banner = gr.HTML(
                        _build_banner(startup_message, startup_tone)
                    )
                    with gr.Column(elem_classes=["panel-card"]):
                        gr.HTML('<h2 class="panel-title">Prompt Review</h2>', padding=True)
                        gr.HTML(
                            '<p class="panel-note">These prompts are generated from the brief and refreshed automatically before each asset render.</p>',
                            padding=True,
                        )
                        image_prompt_box = gr.Textbox(
                            label="Image Prompt",
                            lines=7,
                            interactive=False,
                            show_copy_button=True,
                            elem_classes=["prompt-box"],
                        )
                        video_prompt_box = gr.Textbox(
                            label="Video Prompt",
                            lines=8,
                            interactive=False,
                            show_copy_button=True,
                            elem_classes=["prompt-box"],
                        )

                    with gr.Row(equal_height=False):
                        with gr.Column(elem_classes=["panel-card", "media-frame"]):
                            gr.HTML('<h2 class="panel-title">Final Image</h2>', padding=True)
                            image_output = gr.Image(
                                label="Generated Promotional Image",
                                type="filepath",
                                interactive=False,
                                show_download_button=True,
                            )
                        with gr.Column(elem_classes=["panel-card", "media-frame"]):
                            gr.HTML('<h2 class="panel-title">Final Video</h2>', padding=True)
                            video_output = gr.Video(
                                label="Generated Promotional Video",
                                interactive=False,
                            )
                            video_download = gr.File(
                                label="Download Video File",
                                interactive=False,
                            )

        def _stream_asset_generation(next_state: dict, service, mode: str, initial_message: str):
            next_state = clone_state(next_state)
            next_state["generation_mode"] = mode
            next_state["last_error"] = ""
            next_state["image_path"] = None
            next_state["video_path"] = None
            next_state["video_download_path"] = None
            next_state["status_text"] = "Starting asset generation..."

            try:
                if not can_generate_assets(next_state):
                    raise MarketingAppError("No prompts are available for asset generation.")

                yield _outputs_from_state(next_state, initial_message, "neutral")

                if mode in {"image", "both"}:
                    image_artifact = service.generate_image(
                        next_state.get("image_prompt", ""),
                        output_dir=str(RUNTIME_DIR),
                    )
                    next_state["image_path"] = image_artifact.get("path")
                    next_state["has_generated_assets"] = True
                    _append_status(next_state, "Image ready.")
                    if mode == "image":
                        yield _outputs_from_state(next_state, "Assets generated.", "success")
                    else:
                        yield _outputs_from_state(
                            next_state,
                            "Image generated. Continuing with video...",
                            "neutral",
                        )

                if mode in {"video", "both"}:
                    video_job = service.start_video_generation(next_state.get("video_prompt", ""))
                    _append_status(next_state, f"Video job created: {video_job.id}")
                    yield _outputs_from_state(next_state, "Video generation started.", "neutral")

                    while getattr(video_job, "status", None) in {"queued", "in_progress"}:
                        time.sleep(service.video_poll_interval_seconds)
                        video_job = service.poll_video_status(video_job.id)
                        progress = getattr(video_job, "progress", 0)
                        _append_status(
                            next_state,
                            f"Status: {video_job.status} | Progress: {progress}%",
                        )
                        yield _outputs_from_state(
                            next_state,
                            f"Video generation in progress ({progress}%).",
                            "neutral",
                        )

                    if getattr(video_job, "status", None) == "failed":
                        error = getattr(getattr(video_job, "error", None), "message", "")
                        raise MarketingAppError(error or "Video generation failed.")

                    video_artifact = service.download_video(video_job.id, output_dir=str(RUNTIME_DIR))
                    next_state["video_path"] = video_artifact.get("path")
                    next_state["video_download_path"] = video_artifact.get("path")
                    next_state["has_generated_assets"] = True
                    _append_status(next_state, "Video ready.")
                    yield _outputs_from_state(next_state, "Assets generated.", "success")
            except MarketingAppError as exc:
                next_state["last_error"] = str(exc)
                _append_status(next_state, str(exc))
                yield _outputs_from_state(next_state, str(exc), "error")
            except Exception as exc:  # pragma: no cover - defensive UI path
                next_state["last_error"] = f"Unexpected error: {exc}"
                _append_status(next_state, next_state["last_error"])
                yield _outputs_from_state(next_state, next_state["last_error"], "error")

        def on_generate_assets_from_brief(brief: str, mode: str, state: dict):
            next_state = clone_state(state)
            try:
                service = service_factory()
                next_state = generate_prompts(next_state, brief, mode, service)
                yield from _stream_asset_generation(
                    next_state,
                    service,
                    mode,
                    "Prompts generated. Creating assets now...",
                )
            except MarketingAppError as exc:
                next_state["last_error"] = str(exc)
                next_state["status_text"] = str(exc)
                yield _outputs_from_state(next_state, str(exc), "error")
            except Exception as exc:  # pragma: no cover - defensive UI path
                next_state["last_error"] = f"Unexpected error: {exc}"
                next_state["status_text"] = next_state["last_error"]
                yield _outputs_from_state(next_state, next_state["last_error"], "error")

        def on_refine_and_generate_assets(feedback: str, mode: str, state: dict):
            next_state = clone_state(state)
            try:
                service = service_factory()
                if not can_refine_after_generation(next_state):
                    raise MarketingAppError("Generate assets before refining them.")

                if (feedback or "").strip():
                    next_state = refine_prompts(next_state, feedback, service)
                    banner_message = "Prompts updated. Creating assets now..."
                else:
                    next_state["feedback"] = ""
                    banner_message = "Generating assets from the current prompts..."

                yield from _stream_asset_generation(next_state, service, mode, banner_message)
            except MarketingAppError as exc:
                next_state["last_error"] = str(exc)
                _append_status(next_state, str(exc))
                yield _outputs_from_state(next_state, str(exc), "error")
            except Exception as exc:  # pragma: no cover - defensive UI path
                next_state["last_error"] = f"Unexpected error: {exc}"
                _append_status(next_state, next_state["last_error"])
                yield _outputs_from_state(next_state, next_state["last_error"], "error")

        output_targets = [
            session_state,
            status_banner,
            image_prompt_box,
            video_prompt_box,
            image_output,
            video_output,
            video_download,
            feedback_box,
            refine_generate_assets_button,
        ]

        generate_brief_assets_button.click(
            on_generate_assets_from_brief,
            inputs=[brief_box, mode_select, session_state],
            outputs=output_targets,
            show_progress="full",
        )
        refine_generate_assets_button.click(
            on_refine_and_generate_assets,
            inputs=[feedback_box, mode_select, session_state],
            outputs=output_targets,
            show_progress="full",
        )

    demo.queue(default_concurrency_limit=4)
    return demo


demo = build_demo()


if __name__ == "__main__":
    demo.launch()
