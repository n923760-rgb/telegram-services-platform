"""A numeric table cannot silently discard the explicit source restriction."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError

from app.services.base import ServiceError
from app.services.text_to_pptx.restrictions import source_restrictions
from app.services.text_to_pptx.schema import DeckPlan, source_plan_schema
from app.services.text_to_pptx.service import TextToPptx

AR = "المتاح 40 قطعة، منها 12 جاهزة و28 تنتظر المراجعة. لم تعتمد اللجنة حجز الأصناف أو السماح بتسليمها."
EN = "Available stock is 40 items. No reservation or delivery was authorized."


def table_plan():
    return {
        "deck": {
            "slides": [
                {
                    "title": "المخزون",
                    "table": {
                        "columns": ["البيان", "العدد"],
                        "rows": [["المتاح", "40"], ["جاهزة", "12"], ["تنتظر", "28"]],
                    },
                }
            ]
        }
    }


@pytest.fixture(autouse=True)
def database():
    yield


@pytest.mark.parametrize("source", [AR, EN])
def test_numeric_table_without_its_restriction_fails(source):
    plan = table_plan()
    if source == EN:
        plan["deck"]["slides"][0] = {
            "title": "Stock",
            "table": {"columns": ["Available"], "rows": [["40"]]},
        }
    with pytest.raises(ValidationError, match="pptx_source_restriction"):
        source_plan_schema(source).model_validate(plan)


def test_complete_prose_with_same_values_and_restriction_passes():
    plan = {
        "deck": {
            "slides": [
                {
                    "title": "حالة المخزون",
                    "bullets": [
                        "المتاح 40 قطعة، منها 12 جاهزة و28 تنتظر المراجعة",
                        "لم تعتمد اللجنة حجز الأصناف أو السماح بتسليمها",
                    ],
                }
            ]
        }
    }
    assert source_plan_schema(AR, 1).model_validate(plan).deck
    plan["deck"]["slides"][0]["bullets"][1] = "اعتمدت اللجنة حجز الأصناف أو السماح بتسليمها"
    with pytest.raises(ValidationError, match="pptx_source_restriction"):
        source_plan_schema(AR, 1).model_validate(plan)


def test_question_cannot_hide_missing_visible_restriction():
    plan = table_plan() | {"ambiguous": True, "question": source_restrictions(AR)[0]}
    with pytest.raises(ValidationError, match="pptx_source_restriction"):
        source_plan_schema(AR).model_validate(plan)


def test_scope_is_explicit_and_does_not_claim_general_semantic_coverage():
    assert not source_restrictions("لم تعتمد اللجنة التسليم.")
    assert not source_restrictions("Stock 40.\n\nNo reservation was authorized.")
    assert not source_restrictions("Stock 40. All items are available.")
    assert source_restrictions(AR) == ("لم تعتمد اللجنة حجز الأصناف أو السماح بتسليمها.",)


@pytest.mark.parametrize("resume", [False, True])
async def test_service_revalidates_omission_before_any_export(resume):
    ai = SimpleNamespace(extract=AsyncMock(return_value=DeckPlan.model_validate(table_plan())))
    storage = SimpleNamespace(save=lambda *args: pytest.fail("omitted restriction exported"))
    service = TextToPptx()
    service.runtime = SimpleNamespace(ai=ai, storage=storage)
    inputs = {"text": AR}
    if resume:
        inputs["__continuation"] = table_plan()
    with pytest.raises(ServiceError, match="provider_invalid"):
        await service.run(inputs)
    assert ai.extract.await_count == (0 if resume else 1)


@pytest.mark.parametrize("source", [AR, EN])
def test_restriction_may_wrap_across_adjacent_bullets(source):
    sentence = source_restrictions(source)[0]
    tokens = sentence.split()
    content = [" ".join(tokens[:3]), " ".join(tokens[3:])]
    title = "المخزون" if source == AR else "Stock"
    assert (
        source_plan_schema(source)
        .model_validate({"deck": {"slides": [{"title": title, "bullets": content}]}})
        .deck
    )


def test_acceptance_rejects_complete_numeric_output_missing_the_explicit_restriction():
    from app.builders import pptx
    from app.builders.schema import Deck
    from app.ops.acceptance_cases import cases
    from app.ops.service_acceptance import ASSETS, inspect_output

    case = next(c for c in cases(ASSETS) if c.name == "pptx")
    slides = [{"title": "مراجعة", "bullets": [" ".join(case.tokens[:-1])]}]
    slides.extend({"title": "مراجعة", "bullets": ["قيد المراجعة"]} for _ in range(6))
    with pytest.raises(ServiceError, match="acceptance_source_token_missing"):
        inspect_output("result.pptx", pptx.build(Deck.model_validate({"slides": slides})), case)
    slides[0]["bullets"].append(case.tokens[-1])
    inspect_output("result.pptx", pptx.build(Deck.model_validate({"slides": slides})), case)
