"""Public initial-intake AI decisions; no provider, storage, DB or Telegram access."""

import pytest

from app.ops.service_portfolio import customer_slugs
from app.services.registry import registry
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
    ("text_to_office", {"text": "Source", "target": "word"}, True),
    ("text_to_office", {"text": "keep text unchanged\nSource", "target": "word"}, False),
    ("text_to_office", {"text": "Source", "target": "excel"}, True),
    ("text_to_pdf", {"text": "Source", "mode": "direct"}, False),
    ("text_to_pdf", {"text": "Source", "mode": "smart"}, True),
    ("text_to_pptx", {"text": "Source"}, True),
    ("text_to_word_pdf", {"text": "Source"}, False),
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
