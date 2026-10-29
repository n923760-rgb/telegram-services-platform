"""Literal content, safe rendering, grounded AI and independently decoded QR files."""

import base64
import hashlib
from html.parser import HTMLParser
from io import BytesIO
from types import SimpleNamespace
from xml.etree import ElementTree

import cv2
import numpy as np
import pytest
from PIL import Image
from pydantic import ValidationError

from app.builders import publication_page as page
from app.builders.publication_qr import QUIET_ZONE, assets
from app.publications.design import Plan, Profile, compose, plan_schema
from tests.profile_page_fixtures import plan, profile

URL = "https://example.invalid/p/00123?id=00123&lang=ar"


@pytest.fixture(autouse=True)
def database():
    pass


class Document(HTMLParser):
    def __init__(self, content):
        super().__init__()
        self.tags = []
        self.text = []
        self.feed(content.decode())

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))

    def handle_data(self, data):
        self.text.append(data)


def decode(content):
    image = np.array(Image.open(BytesIO(content)).convert("RGB"))
    value, points, _ = cv2.QRCodeDetectorAruco().detectAndDecode(image)
    assert points is not None
    return value


@pytest.mark.parametrize(
    "url", [URL, "https://example.invalid/ملف?id=00123", "https://example.invalid/" + "a" * 275]
)
def test_native_png_and_share_card_decode_the_exact_whole_page_url(url):
    files = page.bundle(profile(), plan(), public_url=url)
    assert set(files) == {"profile.html", "qr.png", "qr.svg", "share-card.png"}
    assert decode(files["qr.png"]) == url
    assert decode(files["share-card.png"]) == url
    svg = ElementTree.fromstring(files["qr.svg"])
    assert svg.find("{http://www.w3.org/2000/svg}title").text == url
    cells = svg.findall("{http://www.w3.org/2000/svg}g/{http://www.w3.org/2000/svg}rect")
    side = int(svg.attrib["viewBox"].split()[-1])
    assert all(
        QUIET_ZONE <= int(c.attrib[a]) < side - QUIET_ZONE for c in cells for a in ("x", "y")
    )


def test_all_source_targets_and_text_survive_and_inline_style_is_hash_bound():
    content = profile()
    output = page.build(content, plan(), public_url=URL)
    doc = Document(output)
    assert next(a for t, a in doc.tags if t == "html") == {"lang": "ar", "dir": "rtl"}
    links = [a["href"] for t, a in doc.tags if t == "a"]
    assert all(a["url"] in links for a in content["actions"])
    assert URL in links
    assert all(
        s in "".join(doc.text)
        for s in [
            content["name"],
            content["role"],
            content["intro"],
            *[x["title"] for x in content["sections"]],
        ]
    )
    style = output.decode().split("<style>")[1].split("</style>")[0]
    digest = base64.b64encode(hashlib.sha256(style.encode()).digest()).decode()
    csp = next(
        a["content"]
        for t, a in doc.tags
        if t == "meta" and a.get("http-equiv") == "Content-Security-Policy"
    )
    assert "sha256-" + digest in csp and "unsafe-inline" not in csp
    assert "default-src 'none'" in csp and not any(t == "script" for t, _ in doc.tags)


def test_embedding_is_optional_and_separate_qr_is_always_delivered():
    files = page.bundle(profile(), plan(), public_url=URL, embedded_qr=False)
    assert decode(files["qr.png"]) == URL
    assert "<details" not in files["profile.html"].decode()
    assert "<img" not in files["profile.html"].decode()
    assert Image.open(BytesIO(files["share-card.png"])).width == 1080
    assert "data:" not in page.build(profile(), plan()).decode().split("<body>")[1]


def test_source_markup_is_text_never_an_executable_attribute_or_tag():
    malicious = '<script>1</script> " onmouseover="alert(2)'
    content = profile(name=malicious, intro=malicious)
    content["actions"][0]["label"] = malicious
    doc = Document(page.build(content, plan()))
    assert not any(t in {"script", "iframe", "object", "form"} for t, _ in doc.tags)
    assert not any(k.startswith("on") for _, a in doc.tags for k in a)
    assert malicious in "".join(doc.text)


@pytest.mark.parametrize(
    "url",
    [
        "javascript:alert(1)",
        "http://example.com/",
        "https://user:pass@example.com/",
        "https://example.com/\n",
        "https://example.com/%0A",
        "https://example.com/\\foo",
        "https://example.com/\u202eevil",
        "https://example.com/" + "x" * 300,
    ],
)
def test_unsafe_action_or_whole_page_destination_rejected(url):
    data = profile()
    data["actions"][0]["url"] = url
    with pytest.raises(ValueError):
        Profile.model_validate(data)
    with pytest.raises(ValueError):
        assets(url)


@pytest.mark.parametrize(
    "changes",
    [
        {"accent": "#ffffff"},
        {"accent": "red;display:none"},
        {"primary": 3},
        {"primary": 1},
        {"title_size": True},
        {"columns": 3},
        {"corner_radius": 100},
        {"action_order": [0, 0, 1]},
        {"section_order": [0]},
        {"tagline": "invented fact"},
    ],
)
def test_unreadable_or_ungrounded_ai_plan_rejected(changes):
    with pytest.raises(ValidationError):
        plan_schema(Profile.model_validate(profile())).model_validate(plan(**changes))


@pytest.mark.parametrize(
    "changes",
    [
        {"name": "\nname"},
        {"role": "\u202eevil"},
        {"intro": "a" + "\n" * 21},
        {"sections": [{"title": "Empty", "body": "", "items": []}]},
        {"actions": []},
        {"name": "a" * 65},
    ],
)
def test_invalid_source_contract_rejected(changes):
    with pytest.raises(ValueError):
        Profile.model_validate(profile(**changes))


async def test_injected_ai_sees_source_goal_and_labels_without_target_urls():
    calls = []

    async def extract(schema, source, prompt):
        calls.append((source, prompt))
        return schema.model_validate(plan(primary=1, action_order=[1, 0, 2], section_order=[1, 0]))

    designed = await compose(
        SimpleNamespace(extract=extract), profile(), "أبرز أعمالي أولا؛ أفضل الأخضر الهادئ"
    )
    assert len(calls) == 1 and "أبرز أعمالي" in calls[0][0]
    assert "wa.me" not in calls[0][0] and "https://" not in calls[0][0]
    output = page.build(profile(), designed).decode()
    assert output.index('href="https://example.invalid/work') < output.index('href="https://wa.me/')
    assert output.index('id="section-1"') < output.index('id="section-0"')


async def test_invalid_ai_response_is_not_silently_replaced_with_native_plan():
    async def extract(*args):
        return SimpleNamespace(model_dump=lambda **kwargs: plan(action_order=[0, 0, 0]))

    with pytest.raises(ValidationError):
        await compose(SimpleNamespace(extract=extract), profile(), "بيانات مصدرية")
    with pytest.raises(ValueError, match="gateway"):
        await compose(None, profile(), "بيانات مصدرية")


def test_bounded_maximum_content_share_card_is_not_clipped():
    data = profile(name="W" * 64, role="د" * 96)
    result = page.share_card(data, plan(), public_url="https://example.invalid/" + "W" * 275)
    image = Image.open(BytesIO(result))
    assert image.width == 1080 and 1100 <= image.height <= 1700


@pytest.mark.parametrize("theme,accent", [("light", "#2f5d50"), ("dark", "#b7dfc6")])
def test_every_surface_text_and_primary_fill_have_readable_contrast(theme, accent):
    from app.publications.design import THEMES, contrast

    presentation = Plan.model_validate(plan(theme=theme, accent=accent))
    for background in ("background", "surface"):
        for foreground in ("ink", "muted"):
            assert contrast(THEMES[theme][background], THEMES[theme][foreground]) >= 4.5
    assert (
        max(contrast(presentation.accent, "#ffffff"), contrast(presentation.accent, "#101815"))
        >= 4.5
    )


@pytest.mark.parametrize("language", ["ar", "en"])
@pytest.mark.parametrize("count", [1, 2, 3, 4, 5, 6])
def test_one_to_six_actions_and_empty_or_full_sections_keep_all_source_content(language, count):
    actions = [
        {"label": f"Action {i}", "url": f"https://example.invalid/action/{i}?id=00123"}
        for i in range(count)
    ]
    data = profile(language=language, actions=actions, sections=[])
    presentation = plan(
        primary=count - 1, action_order=list(reversed(range(count))), section_order=[]
    )
    document = Document(page.build(data, presentation))
    targets = [
        attrs["href"]
        for tag, attrs in document.tags
        if tag == "a" and attrs.get("class", "").startswith("action")
    ]
    assert targets == [a["url"] for a in reversed(actions)]
    assert all(len(a["label"]) > 0 for a in actions)


def test_shared_contract_accepts_arabic_english_catalogs_with_matching_keys():
    from app.core.i18n import CATALOGS

    keys = {key for key in CATALOGS["ar"] if key.startswith("profile_")}
    assert keys == {key for key in CATALOGS["en"] if key.startswith("profile_")}


@pytest.mark.parametrize("flag", [0, 1, "false", None])
def test_embedding_requires_an_explicit_boolean(flag):
    with pytest.raises(ValueError, match="boolean"):
        page.bundle(profile(), plan(), public_url=URL, embedded_qr=flag)
