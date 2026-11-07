"""Prompt templates: Jinja2 files under prompts/<module>/ with a YAML front-matter comment.

{# ---
persona_view: traits_only
output_schema: SurveyAnswer
--- #}
{% block system %}...{% endblock %}
{% block user %}...{% endblock %}
"""

import hashlib
import re
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Any

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined

from delegationlab.llm.types import Message

_FRONT_MATTER = re.compile(r"^\s*\{#-?\s*---\s*\n(.*?)\n\s*---\s*-?#\}", re.DOTALL)


@dataclass(frozen=True)
class TemplateMeta:
    persona_view: str | None
    output_schema: str | None


class TemplateStore:
    def __init__(self, prompts_dir: Path) -> None:
        self.prompts_dir = prompts_dir
        self.env = Environment(
            loader=FileSystemLoader(prompts_dir),
            undefined=StrictUndefined,
            keep_trailing_newline=False,
            autoescape=False,
        )

    def source(self, name: str) -> str:
        return (self.prompts_dir / name).read_text()

    def hash(self, name: str) -> str:
        return hashlib.sha256((self.prompts_dir / name).read_bytes()).hexdigest()

    def meta(self, name: str) -> TemplateMeta:
        match = _FRONT_MATTER.match(self.source(name))
        data = yaml.safe_load(match.group(1)) if match else {}
        return TemplateMeta(data.get("persona_view"), data.get("output_schema"))

    def render(self, name: str, variables: dict[str, Any]) -> list[Message]:
        tmpl = self.env.get_template(name)
        messages = []
        for role in ("system", "user"):
            block = tmpl.blocks.get(role)
            if block is None:
                continue
            text = "".join(block(tmpl.new_context(variables))).strip()
            if text:
                messages.append(Message(role=role, content=text))
        if not any(m.role == "user" for m in messages):
            raise ValueError(f"Template {name} has no non-empty `user` block")
        return messages

    @cached_property
    def all_hashes(self) -> dict[str, str]:
        return {
            str(p.relative_to(self.prompts_dir)): self.hash(str(p.relative_to(self.prompts_dir)))
            for p in sorted(self.prompts_dir.rglob("*.j2"))
        }
