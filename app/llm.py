from dataclasses import dataclass
from typing import List, Dict

import os

from dotenv import load_dotenv
from openai import OpenAI


# Load environment variables from a .env file if present
load_dotenv()


@dataclass
class LLMConfig:
    """
    Configuration for the LLM client.

    OPENAI_API_KEY is read from the environment (or .env via python-dotenv).
    You can optionally override the model via OPENAI_MODEL.
    """

    model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


class LLM:
    """
    Thin wrapper around the OpenAI Python SDK for chat-style interactions.
    """

    def __init__(self, config: LLMConfig | None = None) -> None:
        self.config = config or LLMConfig()
        # The OpenAI client will pick up OPENAI_API_KEY from the environment.
        self.client = OpenAI()

    def chat(self, system_prompt: str, messages: List[Dict[str, str]]) -> str:
        """
        Call the OpenAI Chat Completions API and return the assistant's text.
        """
        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=[{"role": "system", "content": system_prompt}, *messages],
            temperature=0.2,
        )
        message = response.choices[0].message
        return message.content or ""


