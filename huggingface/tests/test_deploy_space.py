import sys
import unittest
from pathlib import Path
from unittest.mock import Mock


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


from huggingface import deploy_space  # noqa: E402


class DeploySpaceTests(unittest.TestCase):
    def test_resolve_space_repo_id_from_space_url(self):
        repo_id = deploy_space.resolve_space_repo_id(
            space_url="https://huggingface.co/spaces/amirtavasoli/marketing_campaign_generator/tree/main"
        )

        self.assertEqual(repo_id, "amirtavasoli/marketing_campaign_generator")

    def test_resolve_space_repo_id_prefers_explicit_repo_id(self):
        repo_id = deploy_space.resolve_space_repo_id(
            space_url="https://huggingface.co/spaces/ignored/ignored/tree/main",
            repo_id="owner/real-space",
        )

        self.assertEqual(repo_id, "owner/real-space")

    def test_default_ignore_patterns_cover_env_and_runtime_files(self):
        patterns = deploy_space.default_ignore_patterns()

        self.assertIn(".env", patterns)
        self.assertIn(".env.*", patterns)
        self.assertIn("*.env", patterns)
        self.assertIn("*.env.*", patterns)
        self.assertIn("runtime-artifacts", patterns)
        self.assertIn("runtime-artifacts/**", patterns)
        self.assertIn("tests", patterns)

    def test_upload_space_folder_passes_expected_arguments(self):
        api = Mock()

        commit_url = deploy_space.upload_space_folder(
            api=api,
            folder_path="huggingface",
            repo_id="owner/space",
        )

        self.assertIs(commit_url, api.upload_folder.return_value)
        api.upload_folder.assert_called_once_with(
            repo_id="owner/space",
            repo_type="space",
            folder_path="huggingface",
            ignore_patterns=deploy_space.default_ignore_patterns(),
        )


if __name__ == "__main__":
    unittest.main()
