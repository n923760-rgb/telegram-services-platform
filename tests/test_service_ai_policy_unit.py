"""Public initial-intake AI decisions; no provider, storage, DB or Telegram access."""

from collections import Counter
from types import SimpleNamespace

import pytest

from app.bot.catalog import view
from app.core.i18n import tr
from app.ops.service_portfolio import customer_slugs
from app.services.base import ai_policy
from app.services.registry import Registry, registry
from tests.csv_review_fixtures import inputs as csv_inputs
from tests.cv_fixtures import inputs as cv_inputs
from tests.minutes_fixtures import inputs as minutes_inputs

FILE = "1/" + "a" * 32 + "/source.pdf"
IMAGE = "1/" + "b" * 32 + "/source.png"
CASES = [
    ("csv_review", csv_inputs(), False),
    ("cv_formatting", cv_inputs(), True),
    ("document_image_enhancement", {"image": IMAGE}, True),
    ("image_to_text", {"images": [IMAGE]}, True),
    ("images_to_pdf", {"images": [IMAGE], "orientation": "auto"}, False),
    ("meeting_minutes", minutes_inputs(), True),
    ("pdf_tables_excel", {"pdf": FILE, "mode": "direct", "language": "ar"}, False),
    ("pdf_tables_excel", {"pdf": FILE, "mode": "labels", "language": "ar"}, True),
    ("pdf_to_word", {"pdf": FILE}, True),
    ("pdf_tools", {"files": [FILE], "operation": "extract", "pages": "1"}, False),
    ("text_editing", {"text": "Source", "mode": "proofread"}, True),
    ("text_summary", {"text": "Source", "language": "ar", "length": "short"}, True),
    ("text_to_office", {"text": "Source", "target": "word", "mode": "smart"}, True),
    ("text_to_office", {"text": "Source", "target": "word", "mode": "direct"}, False),
    ("text_to_office", {"text": "Source", "target": "excel"}, True),
    ("text_to_pdf", {"text": "Source", "mode": "direct"}, False),
    ("text_to_pdf", {"text": "Source", "mode": "smart"}, True),
    ("text_to_pptx", {"text": "Source"}, True),
    ("text_to_word_pdf", {"text": "Source"}, False),
    ("text_to_word_pdf", {"text": "Source", "mode": "smart"}, True),
    ("text_translation", {"text": "Source", "language": "ar", "style": "formal"}, True),
]


@pytest.fixture(autouse=True)
def database():
    # Pure policy checks must not inherit the lifecycle fixture's public Echo override.
    yield


@pytest.mark.parametrize("slug,inputs,expected", CASES)
def test_public_service_ai_policy_is_explicit_and_pure(slug, inputs, expected):
    plugin = registry.types[slug]
    plugin.input_schema.validate_inputs(inputs)
    assert plugin.needs_ai(inputs) is expected


def test_policy_cases_cover_exactly_the_customer_portfolio_not_private_services():
    assert {case[0] for case in CASES} == set(customer_slugs())
    assert len(customer_slugs()) == 16


def test_declared_policies_cover_real_initial_request_decisions_without_invoking_plugins(
    monkeypatch,
):
    policies = {slug: ai_policy(registry.types[slug]) for slug in customer_slugs()}
    assert Counter(policies.values()) == {"required": 9, "conditional": 4, "none": 3}
    for slug, _inputs, expected in CASES:
        if policies[slug] != "conditional":
            assert expected == (policies[slug] == "required")

    def forbidden(*args):
        raise AssertionError("Presentation must not execute customer validation")

    for plugin in registry.types.values():
        monkeypatch.setattr(plugin, "needs_ai", forbidden)
    assert {slug: ai_policy(registry.types[slug]) for slug in customer_slugs()} == policies


@pytest.mark.parametrize("required,optional", [(True, True), (1, False), (False, None), (False, 1)])
def test_invalid_or_conflicting_ai_metadata_is_rejected(monkeypatch, required, optional):
    plugin = registry.types["echo"]
    monkeypatch.setattr(plugin, "requires_ai", required)
    monkeypatch.setattr(plugin, "optional_ai", optional)
    with pytest.raises(ValueError, match="invalid service AI metadata"):
        Registry().discover()


@pytest.mark.parametrize("slug", ["csv_review", "text_to_word_pdf", "cv_formatting"])
@pytest.mark.parametrize("lang", ["ar", "en"])
def test_paused_catalog_warns_for_optional_ai_but_keeps_direct_paths_listed(slug, lang):
    row = SimpleNamespace(slug=slug, name_ar=slug, name_en=slug)
    category = registry.types[slug].category
    paused, items = view([row], lang, category=category, ai_available=False)
    available, normal_items = view([row], lang, category=category, ai_available=True)
    assert items == normal_items
    assert (tr("catalog_ai_notice", lang) in paused) == (ai_policy(registry.types[slug]) != "none")
    assert tr("catalog_ai_notice", lang) not in available
