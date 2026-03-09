"""Helpers for syncing the local Hugging Face app folder to a Space repo."""

from __future__ import annotations

import os
from typing import Iterable
from urllib.parse import urlparse


def default_ignore_patterns() -> list[str]:
    """Return files that should never be uploaded to the Space repo."""
    return [
        ".env",
        ".env.*",
        "*.env",
        "*.env.*",
        "__pycache__",
        "__pycache__/**",
        "tests",
        "tests/**",
        "*.pyc",
        "runtime-artifacts",
        "runtime-artifacts/**",
    ]


def resolve_space_repo_id(space_url: str | None = None, repo_id: str | None = None) -> str:
    """Resolve a Hugging Face Space repo id from explicit input or a Space URL."""
    if repo_id:
        return repo_id.strip()

    if not space_url:
        raise ValueError(
            "Provide HUGGING_FACE_SPACE_REPO_ID or HUGGING_FACE_SPACE_URL before deploying."
        )

    parts = urlparse(space_url).path.strip("/").split("/")
    if len(parts) >= 3 and parts[0] == "spaces":
        return "/".join(parts[1:3])
    if len(parts) >= 2:
        return "/".join(parts[-2:])
    raise ValueError(f"Could not resolve a Space repo id from: {space_url}")


def upload_space_folder(*, api, folder_path: str, repo_id: str, ignore_patterns: Iterable[str] | None = None):
    """Upload the Space folder to Hugging Face."""
    return api.upload_folder(
        repo_id=repo_id,
        repo_type="space",
        folder_path=folder_path,
        ignore_patterns=list(ignore_patterns or default_ignore_patterns()),
    )


def main() -> None:
    """Deploy the local huggingface folder using environment-provided credentials."""
    token = os.environ.get("HUGGING_FACE_API_TOKEN")
    if not token:
        raise SystemExit("HUGGING_FACE_API_TOKEN is required.")

    repo_id = resolve_space_repo_id(
        space_url=os.environ.get("HUGGING_FACE_SPACE_URL"),
        repo_id=os.environ.get("HUGGING_FACE_SPACE_REPO_ID"),
    )

    try:
        from huggingface_hub import HfApi
    except ImportError as exc:
        raise SystemExit("huggingface_hub is required to deploy the Space.") from exc

    result = upload_space_folder(
        api=HfApi(token=token),
        folder_path="huggingface",
        repo_id=repo_id,
    )
    print(repo_id)
    print(result)


if __name__ == "__main__":
    main()
