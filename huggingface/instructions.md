# Hugging Face Deployment Instructions

This file explains how to deploy the app in this folder to a Hugging Face Space.

The app root is this directory:

- `huggingface/`

The Space runtime entrypoint is:

- `app.py`

The required Hugging Face README frontmatter already lives in:

- `README.md`

## What You Need

Before deploying, make sure you have:

1. A Hugging Face account with access to create or update a Space.
2. A Hugging Face user access token with permission to manage that Space.
3. An OpenAI API key with access to the models used by this app.
4. Python 3.11 and `uv` installed locally if you want to test or script deployment.

## Required Space Secret

Set this secret in the Hugging Face Space:

- `OPENAI_API_KEY`

Without it, the UI will load but prompt generation and asset generation will be blocked.

## Optional GitHub Repo Secrets For Auto-Deploy

If you want GitHub Actions to push `huggingface/` changes to the Space after merges to `main`,
set these GitHub repository secrets:

- `HUGGING_FACE_API_TOKEN`
- `HUGGING_FACE_SPACE_REPO_ID`

You can use `HUGGING_FACE_SPACE_URL` instead of `HUGGING_FACE_SPACE_REPO_ID` if you prefer, but
the repo id is simpler and avoids URL parsing mistakes.

## Recommended Space Settings

Create the Space with these settings:

1. SDK: `Gradio`
2. Visibility: `Private` or `Public`, depending on your use case
3. Hardware: `CPU Basic` is enough for the UI because generation happens through the OpenAI APIs

## Files To Upload

Upload the contents of this folder as the Space repository root.

Keep these files:

- `README.md`
- `app.py`
- `actions.py`
- `marketing_agent.py`
- `session_state.py`
- `requirements.txt`
- `__init__.py`

Do not upload:

- `.env`
- `__pycache__/`
- `tests/`
- any local temp or generated files

## Local Smoke Test Before Deploying

From the `huggingface/` folder:

```bash
uv venv --python 3.11 .venv
uv pip install --python .venv/bin/python -r requirements.txt
export OPENAI_API_KEY="your-openai-key"
.venv/bin/python app.py
```

Then open:

- `http://127.0.0.1:7860`

Quick checks:

1. The page loads without crashing.
2. A short marketing brief can generate prompts.
3. Non-marketing input is blocked.
4. Prompt review panels populate after generation.

## Deployment Option 1: Hugging Face Web UI

Use this if you want the simplest manual flow.

1. Open your Space on Hugging Face.
2. Go to the `Files` tab.
3. Upload the app files from this folder to the root of the Space repo.
4. Open the `Settings` tab.
5. Add the `OPENAI_API_KEY` secret.
6. Wait for the rebuild to finish.

If the Space is private, you must be logged into Hugging Face to use it in the browser.

## Deployment Option 2: Scripted Upload With `huggingface_hub`

This is the easiest repeatable workflow from this repo.

Create a local `.env` in the `huggingface/` folder with variable names like:

```bash
HUGGING_FACE_API_TOKEN=...
HUGGING_FACE_SPACE_URL=https://huggingface.co/spaces/<user>/<space>/tree/main
OPENAI_API_KEY=...
```

Then run this from the repository worktree root:

```bash
set -a
source huggingface/.env
set +a

.venv/bin/python - <<'PY'
from huggingface_hub import HfApi
from urllib.parse import urlparse
import os

url = os.environ["HUGGING_FACE_SPACE_URL"]
parts = urlparse(url).path.strip("/").split("/")
repo_id = "/".join(parts[1:3]) if len(parts) >= 3 and parts[0] == "spaces" else "/".join(parts[-2:])

api = HfApi(token=os.environ["HUGGING_FACE_API_TOKEN"])
result = api.upload_folder(
    repo_id=repo_id,
    repo_type="space",
    folder_path="huggingface",
    ignore_patterns=[".env", "__pycache__", "tests", "*.pyc"],
)

print(repo_id)
print(result)
PY
```

That uploads the local `huggingface/` folder to the Space repository.

## Deployment Option 3: Automatic Deploy From GitHub Actions

This repository includes:

- `.github/workflows/deploy-huggingface-space.yml`
- `huggingface/deploy_space.py`

Behavior:

1. when a commit lands on `main`
2. and that commit changes files under `huggingface/`
3. GitHub Actions uploads the current `huggingface/` folder to the configured Space

Required GitHub repository secrets:

- `HUGGING_FACE_API_TOKEN`
- `HUGGING_FACE_SPACE_REPO_ID`

Optional alternative:

- `HUGGING_FACE_SPACE_URL`

Manual trigger:

- open the `Actions` tab
- run `Deploy Hugging Face Space`

## How To Confirm The Deploy Worked

You can confirm the Space state with `huggingface_hub`:

```bash
set -a
source huggingface/.env
set +a

.venv/bin/python - <<'PY'
from huggingface_hub import HfApi
from urllib.parse import urlparse
import os

url = os.environ["HUGGING_FACE_SPACE_URL"]
parts = urlparse(url).path.strip("/").split("/")
repo_id = "/".join(parts[1:3]) if len(parts) >= 3 and parts[0] == "spaces" else "/".join(parts[-2:])

api = HfApi(token=os.environ["HUGGING_FACE_API_TOKEN"])
runtime = api.get_space_runtime(repo_id=repo_id)
info = api.space_info(repo_id=repo_id)

print("repo_sha:", getattr(info, "sha", None))
print("runtime_stage:", runtime.stage)
print("runtime_sha:", runtime.raw.get("sha"))
PY
```

Healthy states usually move through:

1. `BUILDING`
2. `APP_STARTING` or `RUNNING_APP_STARTING`
3. `RUNNING`

## Private Space Note

If the Space is private:

1. the normal public URL may show `404` unless you are logged in
2. that does not mean the deploy failed
3. check the runtime state through the Hugging Face UI or the API instead

## Common Problems

### The app loads but generation is blocked

Cause:

- `OPENAI_API_KEY` is missing from Space secrets

Fix:

- add the secret in Space settings
- restart the Space

### The Space shows a Hugging Face runtime error before the app starts

Cause:

- sometimes Hugging Face fails during its own container init phase

Fix:

1. restart the Space from the UI
2. if needed, trigger a clean rebuild by pushing a new commit
3. if the runtime error happens before app logs appear, the issue is likely platform-side, not in `app.py`

### The browser still shows old behavior after a successful deploy

Cause:

- cached frontend session or stale Gradio state

Fix:

1. hard refresh the page
2. open the Space in a new tab
3. if the Space is private, verify you are logged in to the correct Hugging Face account

## Current App Behavior

This app:

- validates user input as marketing-related before prompt generation
- accepts short business or brand descriptions as valid marketing brief seeds
- shows prompts before rendering assets
- can generate image-only, video-only, or both
- stores generated files in temporary runtime storage only

## Safe Deployment Checklist

Before pushing:

1. confirm `README.md` frontmatter still contains `sdk: gradio` and `app_file: app.py`
2. confirm `requirements.txt` is present
3. confirm `.env` is not included in the upload
4. confirm the Space has `OPENAI_API_KEY` configured
5. confirm the latest local smoke test passed
