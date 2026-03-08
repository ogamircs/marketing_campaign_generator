# OpenAI Colab Marketing Agent Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a new Colab notebook that mirrors the existing Vertex AI marketing agent notebook while using OpenAI APIs for prompt generation, image generation, and Sora video generation.

**Architecture:** Clone the existing notebook's section order and LangGraph flow, then replace the provider-specific setup and tool cells with OpenAI-backed implementations. Keep the UX interactive and notebook-first, with local PNG/MP4 outputs for Colab display.

**Tech Stack:** Jupyter notebook JSON, OpenAI Python SDK, LangGraph, LangChain Core, Google Colab userdata, IPython display

---

### Task 1: Create the notebook skeleton from the existing Vertex notebook

**Files:**
- Create: `langgraph_marketing_agent_openai.ipynb`
- Reference: `langgraph_marketing_agent.ipynb`

**Step 1: Write the failing validation**

Run:

```bash
test -f langgraph_marketing_agent_openai.ipynb
```

Expected: command exits non-zero because the notebook does not exist yet.

**Step 2: Create the initial notebook clone**

Copy the existing notebook structure, preserving markdown sections, cell order, and the LangGraph node layout.

**Step 3: Validate the notebook now exists**

Run:

```bash
test -f langgraph_marketing_agent_openai.ipynb
```

Expected: command exits zero.

**Step 4: Commit**

```bash
git add langgraph_marketing_agent_openai.ipynb docs/plans/2026-03-08-openai-colab-marketing-agent-design.md docs/plans/2026-03-08-openai-colab-marketing-agent.md
git commit -m "feat: scaffold OpenAI Colab marketing notebook"
```

### Task 2: Replace the provider setup and tool implementations

**Files:**
- Modify: `langgraph_marketing_agent_openai.ipynb`

**Step 1: Write the failing validation**

Run:

```bash
rg -n "gpt-5-mini|gpt-image-1|sora-2|OpenAI" langgraph_marketing_agent_openai.ipynb
```

Expected: missing or incomplete OpenAI-specific matches before the replacement is done.

**Step 2: Implement the provider swap**

Update the notebook cells so they:

- install the OpenAI SDK and notebook dependencies
- load the API key from Colab userdata or environment
- initialize `OpenAI()`
- replace Gemini prompt expansion with `gpt-5-mini`
- replace Imagen generation with `gpt-image-1`
- replace Veo generation with Sora async create/poll/download
- preserve the no-humans rule in video prompt instructions

**Step 3: Re-run the validation**

Run:

```bash
rg -n "gpt-5-mini|gpt-image-1|sora-2|OpenAI|videos.create|images.generate" langgraph_marketing_agent_openai.ipynb
```

Expected: all required OpenAI integration markers are present.

**Step 4: Commit**

```bash
git add langgraph_marketing_agent_openai.ipynb
git commit -m "feat: replace notebook backend with OpenAI models"
```

### Task 3: Make the notebook Colab-friendly and update repo docs

**Files:**
- Modify: `langgraph_marketing_agent_openai.ipynb`
- Modify: `README.md`

**Step 1: Write the failing validation**

Run:

```bash
rg -n "OPENAI_API_KEY|google.colab.userdata|restart the runtime|OpenAI" README.md langgraph_marketing_agent_openai.ipynb
```

Expected: the README does not yet document the new notebook fully.

**Step 2: Add Colab UX details**

Ensure the notebook and README clearly document:

- dependency installation
- runtime restart
- API key setup
- Sora access caveat
- what outputs the notebook generates

**Step 3: Re-run the validation**

Run:

```bash
rg -n "OPENAI_API_KEY|google.colab.userdata|sora-2|langgraph_marketing_agent_openai.ipynb" README.md langgraph_marketing_agent_openai.ipynb
```

Expected: the required Colab and OpenAI usage notes are present.

**Step 4: Commit**

```bash
git add README.md langgraph_marketing_agent_openai.ipynb
git commit -m "docs: document OpenAI Colab notebook"
```

### Task 4: Validate notebook integrity and behavior assumptions

**Files:**
- Validate: `langgraph_marketing_agent_openai.ipynb`
- Validate: `README.md`

**Step 1: Run JSON validation**

Run:

```bash
python3 -m json.tool langgraph_marketing_agent_openai.ipynb >/dev/null
```

Expected: command exits zero.

**Step 2: Check notebook structure**

Run:

```bash
jq -r '.cells[] | .cell_type' langgraph_marketing_agent_openai.ipynb | head
```

Expected: valid markdown/code cell sequence.

**Step 3: Check key sections and strings**

Run:

```bash
rg -n "Marketing Campaign Creatives Generation Agent|gpt-5-mini|gpt-image-1|sora-2|StateGraph|OPENAI_API_KEY" langgraph_marketing_agent_openai.ipynb README.md
```

Expected: required sections and model identifiers are present.

**Step 4: Commit**

```bash
git add langgraph_marketing_agent_openai.ipynb README.md
git commit -m "chore: validate OpenAI Colab notebook"
```

Plan complete and saved to `docs/plans/2026-03-08-openai-colab-marketing-agent.md`. Two execution options:

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints
