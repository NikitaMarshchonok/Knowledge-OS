from typing import Protocol


class LLMProvider(Protocol):
    @property
    def model_name(self) -> str: ...

    def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.0) -> str: ...
