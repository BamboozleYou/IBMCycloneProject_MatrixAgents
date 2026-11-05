"""Shared base class for all CycloneShield agents."""
from gateway import litellm_router


class BaseAgent:
    def __init__(self, name: str, model: str, system_prompt: str, max_tokens: int = 512):
        self.name = name
        self.model = model
        self.system_prompt = system_prompt
        self.max_tokens = max_tokens

    def call_llm(self, user_message: str) -> str:
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user",   "content": user_message},
        ]
        return litellm_router.complete(self.name, self.model, messages, self.max_tokens)
