import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from huggingface.session_state import (  # noqa: E402
    build_initial_session_state,
    can_generate_assets,
    can_refine_after_generation,
)


class SessionStateTests(unittest.TestCase):
    def test_initial_state_starts_empty_and_cannot_generate_assets(self):
        state = build_initial_session_state()

        self.assertEqual(state["brief"], "")
        self.assertEqual(state["generation_mode"], "both")
        self.assertEqual(state["image_prompt"], "")
        self.assertEqual(state["video_prompt"], "")
        self.assertFalse(state["has_generated_assets"])
        self.assertIsNone(state["image_path"])
        self.assertIsNone(state["video_path"])
        self.assertFalse(can_generate_assets(state))
        self.assertFalse(can_refine_after_generation(state))

    def test_can_generate_assets_requires_prompt_for_selected_mode(self):
        state = build_initial_session_state()
        state["generation_mode"] = "image"
        state["image_prompt"] = "Luxury bottle still life"

        self.assertTrue(can_generate_assets(state))

        state["generation_mode"] = "video"
        self.assertFalse(can_generate_assets(state))
        state["video_prompt"] = "Macro bottle reveal over textured backdrop"
        self.assertTrue(can_generate_assets(state))

    def test_can_refine_after_generation_unlocks_after_first_success(self):
        state = build_initial_session_state()
        self.assertFalse(can_refine_after_generation(state))

        state["has_generated_assets"] = True
        self.assertTrue(can_refine_after_generation(state))


if __name__ == "__main__":
    unittest.main()
