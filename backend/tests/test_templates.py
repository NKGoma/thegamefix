from pathlib import Path

import pytest
from jinja2 import UndefinedError

from delegationlab.llm.templates import TemplateStore

VARS = {"persona": {"narrative": "a careful nurse"}, "question": "pay Lena?"}


def test_front_matter(prompts_dir: Path) -> None:
    meta = TemplateStore(prompts_dir).meta("test/item.j2")
    assert meta.persona_view == "traits_only"
    assert meta.output_schema == "Answer"


def test_render_splits_system_and_user(prompts_dir: Path) -> None:
    messages = TemplateStore(prompts_dir).render("test/item.j2", VARS)
    assert [(m.role, m.content) for m in messages] == [
        ("system", "You are a careful nurse."),
        ("user", "Question: pay Lena?"),
    ]


def test_undefined_variable_raises(prompts_dir: Path) -> None:
    with pytest.raises(UndefinedError):
        TemplateStore(prompts_dir).render("test/item.j2", {"question": "x"})


def test_hash_is_stable_and_tracks_content(prompts_dir: Path) -> None:
    store = TemplateStore(prompts_dir)
    h = store.hash("test/item.j2")
    assert h == store.hash("test/item.j2") and len(h) == 64
    (prompts_dir / "test" / "item.j2").write_text("{% block user %}changed{% endblock %}")
    assert store.hash("test/item.j2") != h


def test_repo_benchmark_template_renders() -> None:
    from delegationlab.llm.benchmark import PERSONA, SCENARIOS, TEMPLATE
    from delegationlab.settings import Settings

    store = TemplateStore(Settings().prompts_dir)
    assert store.meta(TEMPLATE).output_schema == "BenchmarkAnswer"
    messages = store.render(TEMPLATE, {"persona": PERSONA, "scenario": SCENARIOS[0]})
    assert messages[-1].role == "user"
