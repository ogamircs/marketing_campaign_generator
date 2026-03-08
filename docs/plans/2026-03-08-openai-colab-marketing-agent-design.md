# OpenAI Colab Marketing Agent Design

## Goal

Create a new Google Colab notebook that preserves the structure and interactive LangGraph flow of `langgraph_marketing_agent.ipynb` while replacing the backend with OpenAI APIs:

- `gpt-5-mini` for prompt expansion and prompt revision
- `gpt-image-1` for poster generation
- `sora-2` by default for video generation, with an easy toggle to `sora-2-pro`

## Scope

The new notebook should be a structural clone of the existing Vertex AI notebook, not a new product variant. It should keep the same:

- top-to-bottom notebook layout
- LangGraph state machine
- interactive prompt and feedback loop
- image and video generation modes
- Colab-first execution model

It should not add voice-over, local-model loading, or provider abstraction layers.

## Architecture

### Notebook shape

Create `langgraph_marketing_agent_openai.ipynb` with the same high-level sections as the Vertex notebook:

1. title and overview
2. dependency install
3. restart note
4. imports
5. OpenAI authentication and client setup
6. agent state schema
7. tool implementations
8. node functions
9. graph construction
10. run cell

### Backend mapping

| Existing notebook role | New backend |
| --- | --- |
| Gemini prompt expansion | `gpt-5-mini` |
| Gemini prompt modification | `gpt-5-mini` |
| Imagen poster generation | `gpt-image-1` |
| Veo video generation | `sora-2` / `sora-2-pro` |

### Prompt format

The original notebook parses string markers. The OpenAI notebook will switch to JSON-shaped text for better reliability:

```json
{
  "image_prompt": "...",
  "video_prompt": "..."
}
```

The prompt instructions will continue to enforce the repo's critical rule that video prompts must not include people, humans, faces, hands, or human figures.

### Colab setup

Authentication should support both:

- `google.colab.userdata.get("OPENAI_API_KEY")`
- standard `OPENAI_API_KEY` environment variable

The notebook should fail early with a clear message if no API key is available.

### Image flow

`gpt-image-1` returns base64-encoded image data. The notebook should:

1. request one image
2. decode the base64 payload
3. save a PNG file locally
4. display it inline in Colab

### Video flow

Sora video generation is asynchronous. The notebook should:

1. submit a video creation request
2. poll until the job completes or fails
3. download the MP4 file
4. display it inline in Colab

Expose simple config defaults for duration and size that match supported API values and are suitable for a Colab demo.

## Error Handling

The notebook should surface clear notebook-friendly errors for:

- missing API key
- prompt parsing failures
- image generation failures
- video generation failures
- unavailable Sora access on the caller's account

Errors should not break the feedback loop silently.

## Documentation Updates

Update `README.md` so the repo documents the new OpenAI-backed Colab notebook alongside the existing Vertex AI and open-source notebooks.

## Validation

Before completion:

- verify the notebook JSON is valid
- verify required model names and notebook sections are present
- verify the README reflects the new notebook

## References

- https://platform.openai.com/docs/guides/images
- https://platform.openai.com/docs/guides/video-generation
