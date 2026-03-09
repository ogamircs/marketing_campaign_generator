---
title: Campaign Studio
emoji: 🎬
colorFrom: yellow
colorTo: red
sdk: gradio
sdk_version: 5.50.0
app_file: app.py
pinned: false
---

# Campaign Studio

Campaign Studio is a Gradio-based Hugging Face Space for the OpenAI marketing agent in this repository. It turns a short marketing brief into structured image and video prompts, lets the user review and refine those prompts, and then generates the final assets from the approved creative direction.

## Features

- marketing-only input guardrails for briefs and refinement feedback
- two-step flow: prompt generation first, asset generation second
- prompt review panels for image and video directions
- OpenAI image generation and Sora video generation
- status log updates during long-running video jobs
- image and video previews plus downloadable video output

## Required Secret

Set this Hugging Face Space secret before running the app:

- `OPENAI_API_KEY`

The Space will still load without the key, but generation actions will show a clear configuration error until the secret is added.

## Local Run

From this folder:

```bash
uv venv --python 3.11 .venv
uv pip install --python .venv/bin/python -r requirements.txt
.venv/bin/python app.py
```

## Deploying This Folder

This folder is intended to be self-contained for Space deployment. The simplest workflow is:

1. create a new Hugging Face Space with the Gradio SDK
2. copy the contents of this folder into that Space repo
3. add `OPENAI_API_KEY` as a Space secret
4. push the Space repo

## Notes

- The app targets the OpenAI-backed workflow only.
- Generated files are stored in temporary runtime storage for the active Space session.
- No history gallery or persistent asset storage is included in this version.
- The UI theme avoids low-contrast Gradio defaults for better readability on light surfaces.
