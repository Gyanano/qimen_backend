"""Abstraction for interacting with a large language model (LLM).

This module wraps calls to the OpenAI API when an API key is configured.  If
no key is present, it falls back to returning a canned response.  Keeping
LLM integration in its own module makes it easy to swap out providers or
add caching.
"""

import os
from typing import Dict, Any

try:
    import openai  # type: ignore
except ImportError:
    openai = None  # type: ignore


def ask_llm(prompt: str, model: str = "gpt-3.5-turbo", max_tokens: int = 512) -> str:
    """Send a prompt to the LLM and return the response text.

    If the environment variable `OPENAI_API_KEY` is not set or the OpenAI
    client library is unavailable, a placeholder response is returned instead.

    Parameters:
        prompt: The full prompt string assembled by `chart_to_prompt`.
        model:  The OpenAI model identifier.
        max_tokens: The maximum number of tokens to generate.

    Returns:
        The text of the assistant's reply.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or openai is None:
        # Fallback: echo the prompt and indicate that this is a placeholder
        return f"[Stubbed LLM response]\nYou asked: {prompt[:200]}..."
    # Configure OpenAI client
    openai.api_key = api_key
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that answers questions with reference to Qimen charts."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=max_tokens,
            temperature=0.7,
        )
        choices = response.get("choices")
        if choices:
            text = choices[0]["message"]["content"].strip()
            return text
        return "[LLM returned no choices]"
    except Exception as exc:
        return f"[LLM error: {exc}]"