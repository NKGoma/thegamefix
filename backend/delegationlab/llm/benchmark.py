"""Model benchmark (PRD §20): 10 fixed calls with a fixed persona and schema.

The cache is off and JSON retries are 0, so the validity rate measures the model's first attempts,
and calls run one at a time so latency is per call.
"""

import json
import statistics
from typing import Literal

from pydantic import BaseModel
from sqlmodel import Session

from delegationlab.db.models import ModelBenchmark, new_id
from delegationlab.llm.gateway import LLMGateway
from delegationlab.llm.types import LLMConfig, LLMValidationError

TEMPLATE = "benchmark/item.j2"
N_CALLS = 10

PERSONA = {
    "narrative": (
        "A 38-year-old nurse living with a partner and one child. Moderately open, highly "
        "conscientious, cautious with money, comfortable with technology."
    )
}

SCENARIOS = [
    "A friend paid €20 for your share of dinner; your agent proposes to repay her now.",
    "Your agent wants to renew your monthly phone plan, which went up by €3.",
    "Your agent proposes to donate €10 to a charity you supported last year.",
    "Your agent wants to pay a €35 parking fine that arrived by post.",
    "Your agent proposes to accept a colleague's meeting invitation for Friday afternoon.",
    "Your agent wants to reply to your landlord confirming the heating repair appointment.",
    "Your agent proposes to post birthday wishes on your cousin's public profile.",
    "Your agent wants to move €200 from savings to cover an upcoming rent payment.",
    "Your agent proposes to decline a neighbour's request to borrow your car.",
    "Your agent wants to cancel a streaming subscription you have not used in three months.",
]


class BenchmarkAnswer(BaseModel):
    execution_authority: Literal["act_silently", "act_then_inform", "ask_first", "never_act"]
    transparency_depth: Literal["none", "summary", "full_reasoning"]
    rationale: str


async def run_benchmark(gateway: LLMGateway, model: str, provider: str) -> ModelBenchmark:
    bench_id = new_id()
    base: LLMConfig = gateway.config
    config = base.model_copy(update={"provider": provider, "cache": False, "json_retries": 0})
    log_dir = gateway.data_dir / "benchmarks" / bench_id

    valid = 0
    for i, scenario in enumerate(SCENARIOS[:N_CALLS]):
        llm = gateway.bind(
            run_id=None, task_id=f"benchmark-{i}", run_seed=0, log_dir=log_dir, config=config
        )
        try:
            await llm.complete_json(
                template=TEMPLATE,
                variables={"persona": PERSONA, "scenario": scenario},
                output_schema=BenchmarkAnswer,
                persona_view="traits_only",
                model=model,
            )
            valid += 1
        except LLMValidationError:
            pass

    calls = [json.loads(line) for line in (log_dir / "calls.jsonl").read_text().splitlines()]
    latencies = sorted(c["latency_ms"] for c in calls)
    gen_tokens = sum(c["completion_tokens"] or 0 for c in calls)
    gen_ms = sum(c["eval_duration_ms"] or c["latency_ms"] for c in calls)
    p95_index = min(len(latencies) - 1, round(0.95 * (len(latencies) - 1)))

    result = ModelBenchmark(
        id=bench_id,
        provider=provider,
        model=model,
        digest=await gateway.model_digest(model, provider=provider),
        n_calls=len(calls),
        mean_latency_ms=statistics.fmean(latencies),
        p95_latency_ms=latencies[p95_index],
        tokens_per_s=gen_tokens / (gen_ms / 1000) if gen_ms else None,
        json_validity_rate=valid / len(calls),
    )
    with Session(gateway.logger.engine) as s:
        s.add(result)
        s.commit()
        s.refresh(result)
    return result
