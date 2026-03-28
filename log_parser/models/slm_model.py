from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class SLMSettings:
    model_name_or_path: str
    max_new_tokens: int = 64
    device: Optional[str] = None


class SLMModel:
    """Thin wrapper around a local HuggingFace-compatible causal LM."""

    def __init__(self, settings: SLMSettings) -> None:
        self.settings = settings
        self._tokenizer = None
        self._model = None

    def _ensure_loaded(self) -> None:
        if self._tokenizer is not None and self._model is not None:
            return

        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as exc:
            raise RuntimeError(
                "transformers is required for SLMModel. Install with: pip install transformers torch"
            ) from exc

        self._tokenizer = AutoTokenizer.from_pretrained(self.settings.model_name_or_path)
        self._model = AutoModelForCausalLM.from_pretrained(self.settings.model_name_or_path)

    def generate(self, prompt: str) -> str:
        """Generates deterministic output for a given prompt."""
        self._ensure_loaded()
        assert self._tokenizer is not None
        assert self._model is not None

        model_inputs = self._tokenizer(prompt, return_tensors="pt")
        output_ids = self._model.generate(
            **model_inputs,
            max_new_tokens=self.settings.max_new_tokens,
            do_sample=False,
            temperature=0.0,
            top_p=1.0,
            num_beams=1,
            eos_token_id=self._tokenizer.eos_token_id,
            pad_token_id=self._tokenizer.eos_token_id,
        )
        decoded = self._tokenizer.decode(output_ids[0], skip_special_tokens=True)
        if decoded.startswith(prompt):
            decoded = decoded[len(prompt) :]
        return decoded.strip()
