import importlib
import sys
import unittest
from pathlib import Path

import gradio as gr


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from huggingface.app import CUSTOM_CSS, build_demo  # noqa: E402


class AppTests(unittest.TestCase):
    def test_custom_css_forces_light_gradio_surfaces(self):
        self.assertIn(".panel-card .form,", CUSTOM_CSS)
        self.assertIn(".panel-card .block,", CUSTOM_CSS)
        self.assertIn(".panel-card .label-wrap", CUSTOM_CSS)
        self.assertIn(".panel-card label > span,", CUSTOM_CSS)
        self.assertIn(".panel-card fieldset > span,", CUSTOM_CSS)
        self.assertIn(".media-frame .empty", CUSTOM_CSS)
        self.assertIn(".controls fieldset label,", CUSTOM_CSS)
        self.assertIn(".controls fieldset label.selected", CUSTOM_CSS)
        self.assertIn(".media-frame .float", CUSTOM_CSS)
        self.assertIn(".status-banner strong,", CUSTOM_CSS)

    def test_build_demo_returns_a_gradio_blocks_app(self):
        demo = build_demo(service_factory=lambda: object())
        try:
            self.assertIsInstance(demo, gr.Blocks)
        finally:
            demo.close()

    def test_build_demo_uses_single_step_generation_labels(self):
        demo = build_demo(service_factory=lambda: object())
        try:
            config = demo.get_config_file()
            labels = [component.get("props", {}).get("label") for component in config["components"]]
            button_values = [
                component.get("props", {}).get("value")
                for component in config["components"]
                if component.get("type") == "button"
            ]
            feedback_components = [
                component
                for component in config["components"]
                if component.get("props", {}).get("label") == "Refinement Feedback"
            ]

            self.assertNotIn("Generation Status", labels)
            self.assertNotIn("Generate Prompts", button_values)
            self.assertEqual(button_values.count("Generate Assets"), 2)
            self.assertEqual(len(feedback_components), 1)
            self.assertFalse(feedback_components[0].get("props", {}).get("interactive"))
        finally:
            demo.close()

    def test_app_can_import_from_space_root_layout(self):
        space_root = ROOT / "huggingface"
        sys.path.insert(0, str(space_root))
        sys.modules.pop("app", None)
        try:
            space_app = importlib.import_module("app")
            demo = space_app.build_demo(service_factory=lambda: object())
            try:
                self.assertIsInstance(demo, gr.Blocks)
            finally:
                demo.close()
        finally:
            sys.modules.pop("app", None)
            if str(space_root) in sys.path:
                sys.path.remove(str(space_root))


if __name__ == "__main__":
    unittest.main()
