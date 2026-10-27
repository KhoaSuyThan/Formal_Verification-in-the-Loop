"""Provider-neutral patch generation for repository tasks."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PatchReply:
    patch: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    cost_usd: float | None = None
    resolved_model: str | None = None


class LiteLLMPatchAgent:
    """Use a configured cloud or local LiteLLM model; no Ollama default."""

    def __init__(self, model: str, *, api_base: str | None = None, temperature: float | None = None,
                 max_tokens: int = 8192, timeout_sec: int = 180):
        if not model:
            raise ValueError("An explicit model is required")
        self.model = model
        self.api_base = api_base
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout_sec = timeout_sec

    def generate_patch(self, prompt: str) -> PatchReply:
        import litellm

        kwargs = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You repair Python repositories. Return only a valid unified git diff. Keep changes within the task's source files. Do not alter tests, contracts, or project configuration unless the issue requires it."},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": self.max_tokens,
            "timeout": self.timeout_sec,
        }
        if self.api_base:
            kwargs["api_base"] = self.api_base
        if self.temperature is not None:
            kwargs["temperature"] = self.temperature
        response = litellm.completion(**kwargs)
        body = response.choices[0].message.content or ""
        if "```" in body:
            import re
            match = re.search(r"```(?:diff|patch)?\s*\n(.*?)```", body, re.S | re.I)
            if match:
                body = match.group(1)
        if "diff --git " in body:
            body = body[body.index("diff --git "):]
        usage = getattr(response, "usage", None)
        cost = None
        try:
            cost = float(litellm.completion_cost(completion_response=response))
        except Exception:
            pass
        return PatchReply(
            patch=body.strip() + "\n",
            prompt_tokens=getattr(usage, "prompt_tokens", None),
            completion_tokens=getattr(usage, "completion_tokens", None),
            cost_usd=cost,
            resolved_model=getattr(response, "model", None),
        )
