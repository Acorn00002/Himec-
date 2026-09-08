"""LLM abstraction layer.

Wraps Google Gemini (the project's chosen provider). Nothing outside this module
imports the `google.genai` SDK directly, so swapping providers later means changing
this module only. Phase 1~8 (deterministic parsing + crosscheck) never calls this;
Phase 9+ (TAG/spec extraction, issue reasoning, report writing) is the first real caller.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

from app.core.config import GEMINI_API_KEY

DEFAULT_MODEL = "gemini-flash-latest"
DEFAULT_VISION_MODEL = "gemini-flash-latest"

SchemaT = TypeVar("SchemaT", bound=BaseModel)

IMAGE_MIME_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
}


class LLMClient:
    def __init__(self, api_key: str = GEMINI_API_KEY, model: str = DEFAULT_MODEL):
        self._api_key = api_key
        self._model = model
        self._client = None

    @property
    def is_configured(self) -> bool:
        return bool(self._api_key)

    def _get_client(self):
        if self._client is None:
            from google import genai

            self._client = genai.Client(api_key=self._api_key)
        return self._client

    def _require_configured(self):
        if not self.is_configured:
            raise RuntimeError("GEMINI_API_KEY is not configured")

    def complete(self, system: str, prompt: str, max_output_tokens: int = 4096) -> str:
        """Free-form text completion."""
        self._require_configured()
        from google.genai import types

        response = self._get_client().models.generate_content(
            model=self._model,
            contents=prompt,
            config=types.GenerateContentConfig(system_instruction=system, max_output_tokens=max_output_tokens),
        )
        return response.text or ""

    def complete_structured(
        self,
        system: str,
        prompt: str,
        schema: type[SchemaT],
        image_path: str | None = None,
        max_output_tokens: int = 8192,
    ) -> SchemaT:
        """Structured extraction: response is validated against `schema` (a pydantic
        model) and returned as an instance of it. If `image_path` is given, the image
        is attached alongside the text prompt (Gemini vision input) — used for
        nameplate photos / scanned drawings that have no deterministic text parser."""
        self._require_configured()
        from google.genai import types

        contents: list = [prompt]
        if image_path:
            suffix = Path(image_path).suffix.lower()
            mime_type = IMAGE_MIME_TYPES.get(suffix, "image/png")
            contents.append(types.Part.from_bytes(data=Path(image_path).read_bytes(), mime_type=mime_type))

        response = self._get_client().models.generate_content(
            model=self._model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system,
                max_output_tokens=max_output_tokens,
                response_mime_type="application/json",
                response_schema=schema,
            ),
        )
        parsed = response.parsed
        if parsed is None:
            # SDK failed to auto-parse (e.g. truncated output) — surface the raw text
            # so the caller sees why, instead of a silent None.
            raise ValueError(f"Gemini response did not match schema {schema.__name__}: {response.text!r}")
        return parsed

    def complete_json(self, system: str, prompt: str, max_output_tokens: int = 8192) -> dict | list:
        self._require_configured()
        from google.genai import types

        response = self._get_client().models.generate_content(
            model=self._model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system,
                max_output_tokens=max_output_tokens,
                response_mime_type="application/json",
            ),
        )
        return json.loads(response.text)


llm_client = LLMClient()
