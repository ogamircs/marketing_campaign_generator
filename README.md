# Marketing Campaign Generator

LangGraph-based AI agent for generating marketing creatives from a short brief.

This repo is organized around two Google Colab notebooks that share the same agent workflow:

- expand a short user request into detailed creative prompts
- generate promotional images
- generate short promotional videos
- optionally generate voice-over narration and merge it into the final video
- collect feedback and iterate until the result is approved

## Notebook Options

| Notebook | Stack | Outputs | Requirements |
| --- | --- | --- | --- |
| `langgraph_marketing_agent.ipynb` | Vertex AI with Gemini 2.5 Flash, Imagen 3.0, and Veo 3.1 Fast | Image and video | Google Cloud project with Vertex AI access |
| `langgraph_marketing_agent_opensource.ipynb` | Qwen2.5-7B-Instruct, FLUX.1-dev, Mochi 1, and Kokoro-82M | Image, video, voice-over, and combined video+audio | Google Colab with H100 GPU recommended |

## How It Works

Both notebooks implement the same LangGraph state machine:

1. collect the user's creative brief
2. expand it into structured generation prompts
3. ask what should be generated
4. generate the requested assets
5. collect feedback
6. refine prompts and loop until the user is satisfied

In practice, this makes the repo a notebook-first demo of an interactive creative agent rather than a packaged application or deployable service.

## Current Model Details

### Vertex AI notebook

- `GEMINI_MODEL = "gemini-2.5-flash"`
- `IMAGE_MODEL = "imagen-3.0-generate-001"`
- `VIDEO_MODEL = "veo-3.1-fast-generate-001"`

### Open-source notebook

- `LLM_MODEL = "Qwen/Qwen2.5-7B-Instruct"`
- `IMAGE_MODEL = "black-forest-labs/FLUX.1-dev"`
- `VIDEO_MODEL = "genmo/mochi-1-preview"`
- `TTS_MODEL = "hexgrad/Kokoro-82M"`

The open-source notebook runs locally in Colab, pre-downloads large model weights, and is tuned for high-memory GPUs because Mochi 1 video generation is heavy.

## Running In Google Colab

1. Open the notebook you want to use in Google Colab.
2. Run the install cell.
3. Restart the runtime.
4. Run the remaining cells in order.
5. For the open-source notebook, run the model pre-download cell and expect the first setup to take roughly 15-30 minutes.

### Environment Notes

- Vertex AI notebook:
  - requires a Google Cloud project
  - expects Vertex AI authentication in Colab
  - standard GPU is typically sufficient
- Open-source notebook:
  - does not require API keys
  - works best on an H100 GPU with 80 GB VRAM
  - loads FLUX.1-dev, Mochi 1, and Kokoro directly in the notebook

## Important Prompt Constraint

Video prompts in this project must not include people, humans, faces, hands, or human figures. That rule is enforced in the prompt-expansion and prompt-modification steps so video generation stays focused on products, environments, objects, textures, and abstract motion.

## Repo Layout

- `langgraph_marketing_agent.ipynb`: Vertex AI implementation
- `langgraph_marketing_agent_opensource.ipynb`: open-source implementation with voice-over support
- `img/toronto_coffee_shop.png`: sample generated output

## Sample Output

Generated with the open-source notebook using the prompt `toronto coffee shop`.

![Toronto Coffee Shop](img/toronto_coffee_shop.png)

## Support

☕️ ❤️ If you enjoy this work, [buy me some tokens](https://buymeacoffee.com/amircs).

## License

MIT
