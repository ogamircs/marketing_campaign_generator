# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a LangGraph-based AI agent for generating marketing content (images, videos, and voice-overs). The project provides two notebook implementations:

- **langgraph_marketing_agent.ipynb** - Uses Google Cloud Vertex AI (Gemini, Imagen 3.0, Veo 3.1)
- **langgraph_marketing_agent_opensource.ipynb** - Uses 100% open-source models (Qwen2.5-7B, FLUX.1-dev, CogVideoX-5b, Kokoro TTS)

## Architecture

### Agent State Flow

Both implementations follow the same LangGraph state machine:

```
START → get_user_input → expand_prompt → ask_generation_mode
                                                ↓
                                        generate_content
                                                ↓
                                        collect_feedback
                                           ↙        ↘
                                    [satisfied]   [feedback]
                                         ↓              ↓
                                        END        modify_prompt → (loop back to generate_content)
```

### Key Components

1. **AgentState (TypedDict)** - Central state schema containing:
   - User input and feedback
   - Expanded prompts (image, video, voiceover script)
   - Generation mode selection
   - Generated outputs (image, video paths, audio)
   - Iteration control

2. **Tool Functions**:
   - `expand_prompt()` - Uses LLM to transform brief input into detailed generation prompts
   - `generate_poster()` - Image generation (Imagen 3.0 or FLUX.1-dev)
   - `generate_video()` - Video generation (Veo 3.1 or CogVideoX-5b)
   - `generate_voiceover()` - TTS for narration (Kokoro, open-source only)
   - `combine_video_audio()` - Merges video with voice-over (MoviePy)
   - `modify_prompt()` - Refines prompts based on user feedback

3. **Node Functions** - Wrap tools for LangGraph integration with user I/O

### Model Configuration

**Google Cloud Version:**
- `IMAGE_MODEL = "imagen-3.0-generate-001"`
- `VIDEO_MODEL = "veo-3.1-fast-generate-001"`
- `GEMINI_MODEL = "gemini-2.0-flash"`

**Open-Source Version:**
- `LLM_MODEL = "Qwen/Qwen2.5-7B-Instruct"` (4-bit quantized)
- `IMAGE_MODEL = "black-forest-labs/FLUX.1-dev"`
- `VIDEO_MODEL = "Lightricks/LTX-Video"` (fast real-time generation)
- `TTS_MODEL = "hexgrad/Kokoro-82M"`

## Running the Notebooks

Both notebooks are designed for Google Colab:

1. Install dependencies (first cell)
2. **Restart runtime** after installation
3. Run remaining cells sequentially
4. For open-source version: Run the model pre-download cell before starting the agent (15-30 min first run)

**GPU Requirements:**
- Google Cloud version: Standard GPU
- Open-source version: A100 GPU (40GB VRAM) recommended

## Critical Video Prompt Constraints

Video generation prompts must **never include people, humans, faces, hands, or any human figures**. This constraint is enforced in both `expand_prompt()` and `modify_prompt()` system prompts. Focus only on products, environments, objects, and abstract visuals.
