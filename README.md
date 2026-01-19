# Marketing Campaign Generator

LangGraph-based AI agent for generating marketing content including promotional images, videos, and voice-overs.

## Features

- Takes short user inputs and expands them into detailed generation prompts
- Generates promotional images using state-of-the-art models
- Generates promotional videos (6-8 seconds)
- Generates voice-over narration (open-source version)
- Iterative feedback loop for refining outputs

## Notebooks

| Notebook | Models | Requirements |
|----------|--------|--------------|
| `langgraph_marketing_agent.ipynb` | Google Cloud (Gemini, Imagen 3.0, Veo 3.1) | Google Cloud project with Vertex AI |
| `langgraph_marketing_agent_opensource.ipynb` | Open-source (Qwen2.5-7B, FLUX.1-dev, CogVideoX-5b, Kokoro) | A100 GPU (40GB VRAM) |

## Running in Google Colab

1. Open the desired notebook in [Google Colab](https://colab.research.google.com/)
2. Run the first cell to install dependencies
3. **Restart the runtime** (Runtime → Restart runtime)
4. Run all remaining cells sequentially
5. For the open-source version: Allow 15-30 minutes for initial model downloads

### GPU Requirements

- **Google Cloud version**: Standard GPU is sufficient
- **Open-source version**: Requires A100 GPU (40GB VRAM) - select via Runtime → Change runtime type → A100

## Usage

Once running, the agent will:
1. Ask for a description of the promotional material you need
2. Expand your input into detailed prompts
3. Ask what to generate (image, video, or both)
4. Generate the content
5. Collect feedback and iterate until you're satisfied

## License

MIT
