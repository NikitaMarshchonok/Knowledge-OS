import json
from urllib import request
from urllib.error import HTTPError, URLError

from app.services.llm.base import LLMProvider


class OpenAICompatibleProviderError(Exception):
    pass


class OpenAICompatibleProvider(LLMProvider):
    def __init__(
        self,
        base_url: str,
        model_name: str,
        api_key: str | None = None,
        timeout_seconds: int = 30,
        max_tokens: int = 400,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model_name = model_name
        self._api_key = api_key
        self._timeout_seconds = timeout_seconds
        self._max_tokens = max_tokens

    @property
    def model_name(self) -> str:
        return self._model_name

    def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.0) -> str:
        url = f"{self._base_url}/chat/completions"
        payload = {
            "model": self._model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": self._max_tokens,
        }
        body = json.dumps(payload).encode("utf-8")

        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        req = request.Request(url=url, data=body, headers=headers, method="POST")
        try:
            with request.urlopen(req, timeout=self._timeout_seconds) as response:
                raw = response.read().decode("utf-8")
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise OpenAICompatibleProviderError(
                f"LLM provider HTTP error {exc.code}: {detail or exc.reason}"
            ) from exc
        except URLError as exc:
            raise OpenAICompatibleProviderError(f"LLM provider unreachable: {exc.reason}") from exc

        try:
            parsed = json.loads(raw)
            content = parsed["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
            raise OpenAICompatibleProviderError("LLM provider returned an invalid response payload") from exc

        if not isinstance(content, str) or not content.strip():
            raise OpenAICompatibleProviderError("LLM provider returned an empty answer")

        return content.strip()
