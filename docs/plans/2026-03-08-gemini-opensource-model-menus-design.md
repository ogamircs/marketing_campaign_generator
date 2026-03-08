# Gemini And Open-Source Notebook UX Design

## Goal

Extend the Gemini and open-source Colab notebooks so they match the improved OpenAI notebook UX in two ways:

- wrapped full prompt display in the `EXPANDED PROMPTS` section
- menu-style model selection in the configuration cell

## Scope

This change applies to:

- `langgraph_marketing_agent_gemini.ipynb`
- `langgraph_marketing_agent_opensource.ipynb`

It does not change the LangGraph flow or generation loop.

## Gemini Notebook

Add Colab `@param` menus for the provider models already used by the Vertex notebook:

- `GEMINI_MODEL`
- `IMAGE_MODEL`
- `VIDEO_MODEL`

Use current official Vertex model identifiers and keep the existing initialization flow unchanged.

Also add a small prompt formatting helper so the expanded image and video prompts print as wrapped full text rather than single-line previews.

## Open-Source Notebook

Add the same wrapped prompt display pattern.

Add configuration menus only where the current code path can already support them without a major refactor:

- `LLM_MODEL`
- `IMAGE_MODEL`
- `VIDEO_MODEL`
- `TTS_MODEL`

The open-source notebook should keep the same pipeline classes and execution order. The menu values should stay within model families the current loader code can already handle safely.

## Validation

Before completion:

- validate both notebook JSON files
- compile all Python code cells in both notebooks except shell install cells
- confirm the new config menus and wrapped prompt helper exist in both notebooks
