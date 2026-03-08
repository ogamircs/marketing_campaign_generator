# Gemini And Open-Source Notebook UX Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add wrapped prompt display and safe model-selection menus to the Gemini and open-source notebooks.

**Architecture:** Patch the existing notebook JSON in place, preserving cell order and graph flow. Update the configuration cells to use Colab `@param` menus and add a shared prompt display helper inside each notebook's prompt-expansion code path.

**Tech Stack:** Jupyter notebook JSON, Python notebook cells, Vertex AI model configuration, Hugging Face diffusers/transformers configuration

---

### Task 1: Update the Gemini notebook UX

**Files:**
- Modify: `langgraph_marketing_agent_gemini.ipynb`

**Step 1: Write the failing validation**

Run: `rg -n "Image Prompt Preview|Video Prompt Preview|@param" langgraph_marketing_agent_gemini.ipynb`

Expected: prompt output still uses preview strings and model menus are incomplete.

**Step 2: Implement the Gemini notebook patch**

- add `textwrap` import
- add prompt wrapping helper
- replace preview printing with wrapped full prompt output
- convert `GEMINI_MODEL`, `IMAGE_MODEL`, and `VIDEO_MODEL` to Colab `@param` menu entries

**Step 3: Re-run validation**

Run: `rg -n "format_prompt_for_display|Image Prompt:|Video Prompt:|@param" langgraph_marketing_agent_gemini.ipynb`

Expected: wrapped prompt helper and menu-style configuration exist.

### Task 2: Update the open-source notebook UX

**Files:**
- Modify: `langgraph_marketing_agent_opensource.ipynb`

**Step 1: Write the failing validation**

Run: `rg -n "Image Prompt Preview|Video Prompt Preview|Qwen/Qwen2.5-7B-Instruct|black-forest-labs/FLUX.1-dev" langgraph_marketing_agent_opensource.ipynb`

Expected: prompt output still uses preview strings and the model configuration is hardcoded.

**Step 2: Implement the open-source notebook patch**

- add `textwrap` import
- add prompt wrapping helper
- replace preview printing with wrapped full prompt output
- add safe `@param` menus for `LLM_MODEL`, `IMAGE_MODEL`, `VIDEO_MODEL`, and `TTS_MODEL`

**Step 3: Re-run validation**

Run: `rg -n "format_prompt_for_display|Image Prompt:|Video Prompt:|@param" langgraph_marketing_agent_opensource.ipynb`

Expected: wrapped prompt helper and menu-style configuration exist.

### Task 3: Validate notebook integrity

**Files:**
- Validate: `langgraph_marketing_agent_gemini.ipynb`
- Validate: `langgraph_marketing_agent_opensource.ipynb`

**Step 1: Run JSON validation**

Run:

```bash
python3 -m json.tool langgraph_marketing_agent_gemini.ipynb >/dev/null
python3 -m json.tool langgraph_marketing_agent_opensource.ipynb >/dev/null
```

Expected: both commands exit zero.

**Step 2: Compile notebook Python cells**

Run notebook cell compilation for both notebooks, skipping shell install cells.

Expected: all Python code cells compile cleanly.

Plan complete and saved to `docs/plans/2026-03-08-gemini-opensource-model-menus.md`. Two execution options:

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints
