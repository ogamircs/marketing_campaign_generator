import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from huggingface.actions import (  # noqa: E402
    generate_assets,
    generate_assets_from_brief,
    generate_prompts,
    refine_and_generate_assets,
    refine_prompts,
)
from huggingface.marketing_agent import MarketingAppError  # noqa: E402
from huggingface.session_state import build_initial_session_state  # noqa: E402


class FakeService:
    def __init__(self):
        self.validations = []
        self.expand_calls = []
        self.refine_calls = []
        self.image_calls = []
        self.video_calls = []

    def validate_marketing_input(self, text, label):
        self.validations.append((text, label))
        if "python" in text.lower():
            raise MarketingAppError("Only marketing-related requests are allowed.")
        return text.strip()

    def expand_prompts(self, brief):
        self.expand_calls.append(brief)
        return {
            "image_prompt": f"image::{brief}",
            "video_prompt": f"video::{brief}",
        }

    def refine_prompts(self, current_prompts, feedback):
        self.refine_calls.append((current_prompts, feedback))
        return {
            "image_prompt": f"{current_prompts['image_prompt']}::{feedback}",
            "video_prompt": f"{current_prompts['video_prompt']}::{feedback}",
        }

    def generate_image(self, image_prompt):
        self.image_calls.append(image_prompt)
        return {"path": "/tmp/generated-image.png"}

    def generate_video(self, video_prompt, status_callback=None):
        self.video_calls.append(video_prompt)
        if status_callback:
            status_callback("queued")
            status_callback("complete")
        return {"path": "/tmp/generated-video.mp4"}


class ActionTests(unittest.TestCase):
    def test_generate_prompts_updates_state_and_clears_old_assets(self):
        service = FakeService()
        state = build_initial_session_state()
        state["image_path"] = "/tmp/old.png"
        state["video_path"] = "/tmp/old.mp4"

        updated = generate_prompts(state, "Sparkling tea launch", "both", service)

        self.assertEqual(updated["brief"], "Sparkling tea launch")
        self.assertEqual(updated["generation_mode"], "both")
        self.assertEqual(updated["image_prompt"], "image::Sparkling tea launch")
        self.assertEqual(updated["video_prompt"], "video::Sparkling tea launch")
        self.assertIsNone(updated["image_path"])
        self.assertIsNone(updated["video_path"])

    def test_refine_prompts_requires_existing_prompt_context(self):
        service = FakeService()
        state = build_initial_session_state()

        with self.assertRaisesRegex(MarketingAppError, "Generate prompts before refining"):
            refine_prompts(state, "make it brighter", service)

    def test_refine_prompts_updates_prompt_text(self):
        service = FakeService()
        state = build_initial_session_state()
        state["image_prompt"] = "image::tea launch"
        state["video_prompt"] = "video::tea launch"

        updated = refine_prompts(state, "make it brighter", service)

        self.assertIn("make it brighter", updated["image_prompt"])
        self.assertIn("make it brighter", updated["video_prompt"])

    def test_generate_assets_respects_image_only_mode(self):
        service = FakeService()
        state = build_initial_session_state()
        state["generation_mode"] = "image"
        state["image_prompt"] = "hero bottle portrait"

        updated = generate_assets(state, service)

        self.assertEqual(updated["image_path"], "/tmp/generated-image.png")
        self.assertIsNone(updated["video_path"])
        self.assertEqual(service.video_calls, [])

    def test_generate_assets_runs_both_modes_and_collects_status(self):
        service = FakeService()
        state = build_initial_session_state()
        state["generation_mode"] = "both"
        state["image_prompt"] = "hero bottle portrait"
        state["video_prompt"] = "bottle reveal"

        updated = generate_assets(state, service)

        self.assertEqual(updated["image_path"], "/tmp/generated-image.png")
        self.assertEqual(updated["video_path"], "/tmp/generated-video.mp4")
        self.assertIn("queued", updated["status_text"])
        self.assertIn("complete", updated["status_text"])
        self.assertTrue(updated["has_generated_assets"])

    def test_generate_assets_from_brief_creates_prompts_and_assets_in_one_step(self):
        service = FakeService()
        state = build_initial_session_state()

        updated = generate_assets_from_brief(
            state,
            "Bakery in downtown Toronto",
            "both",
            service,
        )

        self.assertEqual(updated["brief"], "Bakery in downtown Toronto")
        self.assertEqual(updated["image_prompt"], "image::Bakery in downtown Toronto")
        self.assertEqual(updated["video_prompt"], "video::Bakery in downtown Toronto")
        self.assertEqual(updated["image_path"], "/tmp/generated-image.png")
        self.assertEqual(updated["video_path"], "/tmp/generated-video.mp4")
        self.assertTrue(updated["has_generated_assets"])

    def test_refine_and_generate_assets_updates_prompts_automatically(self):
        service = FakeService()
        state = build_initial_session_state()
        state["generation_mode"] = "both"
        state["has_generated_assets"] = True
        state["image_prompt"] = "image::bakery"
        state["video_prompt"] = "video::bakery"

        updated = refine_and_generate_assets(state, "make it more cinematic", service)

        self.assertIn("make it more cinematic", updated["image_prompt"])
        self.assertIn("make it more cinematic", updated["video_prompt"])
        self.assertEqual(updated["image_path"], "/tmp/generated-image.png")
        self.assertEqual(updated["video_path"], "/tmp/generated-video.mp4")

    def test_refine_and_generate_assets_requires_first_generation(self):
        service = FakeService()
        state = build_initial_session_state()

        with self.assertRaisesRegex(MarketingAppError, "Generate assets before refining"):
            refine_and_generate_assets(state, "make it brighter", service)


if __name__ == "__main__":
    unittest.main()
