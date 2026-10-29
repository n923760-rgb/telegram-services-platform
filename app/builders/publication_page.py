"""Original responsive profile composition, literal sources and native share assets."""

import base64
import hashlib
from html import escape
from io import BytesIO
from pathlib import Path

import arabic_reshaper
from bidi.algorithm import get_display
from PIL import Image, ImageDraw, ImageFont, features

from app.builders.publication_qr import assets
from app.core.i18n import tr
from app.publications.design import THEMES, Plan, Profile, contrast, https_url, plan_schema

STYLE = """
*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding:24px}
body{margin:0;background:var(--bg);color:var(--ink);font-family:"DejaVu Sans","Noto Sans Arabic",system-ui,sans-serif;line-height:1.8}
a{color:inherit;text-decoration:none}a:focus-visible,summary:focus-visible{outline:3px solid var(--accent);outline-offset:6px}
a,summary{-webkit-tap-highlight-color:transparent}button,input,summary{font:inherit}
.skip{position:absolute;inset-inline-start:20px;top:-100px;background:var(--paper);padding:12px;z-index:5}.skip:focus{top:10px}
.shell{max-width:1184px;margin:auto;padding:0 36px}.masthead{min-height:104px;display:flex;align-items:center;justify-content:space-between;gap:20px;border-bottom:1px solid var(--line)}
.brand{display:flex;gap:12px;align-items:center;min-width:0;font-weight:700;overflow-wrap:anywhere}.sig{width:30px;height:30px;flex-shrink:0;color:var(--accent)}
.edition{font-size:11px;letter-spacing:.12em;color:var(--muted);white-space:nowrap}
.hero{padding:76px 0 60px;display:grid;grid-template-columns:minmax(0,1.2fr) minmax(0,.8fr);gap:52px;align-items:center}
.identity{min-width:0}.eyebrow{display:flex;gap:12px;align-items:center;color:var(--accent);font-size:12px;letter-spacing:.04em;margin:0 0 20px}
.eyebrow:before{content:"";width:32px;height:1px;background:currentColor;flex-shrink:0}
h1{font-size:clamp(36px,5.2vw,var(--title-size));line-height:1.24;font-weight:700;letter-spacing:-.045em;margin:0 0 24px;overflow-wrap:anywhere;text-wrap:balance}
[dir=rtl] h1{letter-spacing:0;line-height:1.5}.intro{font-size:17px;max-width:56ch;color:var(--muted);white-space:pre-line;overflow-wrap:anywhere;margin:0}
.identity-mark{position:relative;min-height:290px;border:1px solid var(--line);border-radius:var(--radius);background:var(--paper);display:grid;place-items:center;overflow:hidden;isolation:isolate}
.monogram{font-size:120px;line-height:1;font-weight:700;color:var(--accent);z-index:1}.identity-mark:before{content:"";position:absolute;width:190px;height:190px;border:1px solid var(--line);border-radius:50%;transform:translate(50%,-50%);inset-inline-end:0;top:0}
.identity-mark:after{content:"";position:absolute;width:160px;height:110px;border-inline-start:1px solid var(--accent);border-bottom:1px solid var(--accent);inset-inline-start:28px;bottom:28px;border-end-start-radius:44px}
.mark-note{position:absolute;bottom:22px;inset-inline-end:24px;font-size:10px;letter-spacing:.16em;color:var(--muted)}
.hero[data-header=panel] .identity{background:var(--paper);padding:32px;border-radius:var(--radius)}
.hero[data-header=outline]{border:1px solid var(--line);border-radius:var(--radius);padding:40px;margin:44px 0}
.hero[data-alignment=center]{grid-template-columns:1fr;text-align:center;gap:32px}.hero[data-alignment=center] .eyebrow{justify-content:center}
.hero[data-alignment=center] .intro{margin-inline:auto}.hero[data-alignment=center] .identity-mark{min-height:160px;max-width:620px;width:100%;margin:auto}.hero[data-alignment=center] .monogram{font-size:88px}
.actions{display:grid;grid-template-columns:minmax(0,1.1fr) minmax(0,1fr);gap:16px;margin-bottom:60px}
.action{min-height:64px;border:1px solid var(--line);border-radius:var(--radius);display:flex;align-items:center;justify-content:space-between;gap:16px;padding:18px 22px;background:var(--paper);transition:transform .16s ease-out,background-color .16s ease-out;font-size:15px;overflow-wrap:anywhere}
.action bdi{min-width:0}.action:hover{transform:translateY(-2px)}.action:active{transform:translateY(1px)}
.action.primary{background:var(--accent);border-color:var(--accent);color:var(--button-ink);grid-row:span 2;min-height:144px;font-size:21px;font-weight:700}
.actions[data-count="1"]{grid-template-columns:1fr}.actions[data-count="1"] .primary,.actions[data-count="2"] .primary{grid-row:auto;min-height:96px}
.actions[data-count="4"] .primary,.actions[data-count="5"] .primary,.actions[data-count="6"] .primary{grid-column:1/-1;grid-row:auto;min-height:96px}
.actions[data-count="4"] .action:last-child,.actions[data-count="6"] .action:last-child{grid-column:1/-1}
[dir=rtl] .mark-note{letter-spacing:0}
.arrow{font-size:24px;line-height:1;flex-shrink:0}[dir=rtl] .arrow{transform:scaleX(-1)}
.content-grid{display:grid;grid-template-columns:repeat(var(--columns),minmax(0,1fr));gap:24px;padding:0 0 56px}
.section{padding:28px 0;border-top:1px solid var(--line);min-width:0}.section-no{font-size:11px;letter-spacing:.1em;color:var(--accent)}
h2{font-size:24px;line-height:1.6;margin:12px 0 16px;font-weight:600;overflow-wrap:anywhere}
.section p{margin:0;color:var(--muted);white-space:pre-line;overflow-wrap:anywhere}.section ul{list-style:none;margin:18px 0 0;padding:0}.section li{border-top:1px solid var(--line);padding:12px 0;display:flex;align-items:baseline;gap:12px;overflow-wrap:anywhere}.section li:before{content:"";width:5px;height:5px;background:var(--accent);flex-shrink:0}
.sharing{border-top:1px solid var(--line);padding:26px 0}.sharing summary{cursor:pointer;min-height:48px;display:flex;align-items:center;justify-content:space-between;gap:20px;font-size:14px;list-style:none}.sharing summary::-webkit-details-marker{display:none}.sharing summary:after{content:"+";font-size:25px;color:var(--accent)}.sharing[open] summary:after{content:"−"}
.share-body{display:grid;grid-template-columns:180px minmax(0,1fr);gap:30px;padding:24px 0;align-items:center}.qr-box{background:white;padding:12px;width:180px;height:180px;display:grid;place-items:center;border-radius:12px}.qr-box img{width:156px;height:156px;image-rendering:pixelated}.share-copy{min-width:0;color:var(--muted);font-size:14px}.share-copy p{margin:0 0 14px}.public-url{direction:ltr;unicode-bidi:isolate;display:block;overflow-wrap:anywhere;margin-bottom:18px;text-decoration:underline}
.downloads{display:flex;flex-wrap:wrap;gap:12px}.downloads a{display:inline-flex;align-items:center;justify-content:center;min-height:48px;border:1px solid var(--line);padding:10px 18px;border-radius:var(--radius);background:var(--paper);color:var(--ink)}
footer{border-top:1px solid var(--line);padding:24px 0 40px;display:flex;align-items:center;justify-content:space-between;gap:20px;font-size:11px;color:var(--muted)}footer span{overflow-wrap:anywhere}
@media(max-width:700px){.shell{padding:0 22px}.masthead{min-height:80px}.edition{font-size:9px}.hero{grid-template-columns:1fr;padding:40px 0 32px;gap:28px}.identity-mark{min-height:160px}.monogram{font-size:84px}.hero[data-header=outline]{padding:24px;margin:28px 0}.hero[data-header=panel] .identity{padding:24px}.actions{grid-template-columns:1fr;margin-bottom:36px;gap:12px}.action.primary{grid-row:auto;min-height:72px;font-size:18px}.action{min-height:60px}.content-grid{grid-template-columns:1fr;gap:4px;padding-bottom:30px}h2{font-size:22px}.intro{font-size:16px}.section{padding:24px 0}.share-body{grid-template-columns:1fr;gap:20px}.qr-box{margin-inline:auto}footer{align-items:flex-start}.brand{font-size:13px}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}.action{transition:none}.action:hover,.action:active{transform:none}}
""".strip()

SIGNATURE = '<svg class="sig" viewBox="0 0 32 32" aria-hidden="true"><path d="M5 20V9h11M27 12v11H16M10 22l12-12" fill="none" stroke="currentColor" stroke-width="1.5"/><circle cx="16" cy="16" r="3" fill="currentColor"/></svg>'


def data_url(mime, content):
    return f"data:{mime};base64," + base64.b64encode(content).decode()


def build(profile, plan, *, public_url=None, embedded_qr=True):
    """Return a self-contained page; no publication or network side effects."""
    if type(embedded_qr) is not bool:
        raise ValueError("embedding choice must be boolean")
    profile = Profile.model_validate(profile)
    plan = plan_schema(profile).model_validate(
        plan.model_dump(mode="json") if isinstance(plan, Plan) else plan
    )
    if public_url is not None:
        https_url(public_url)
    colors = THEMES[plan.theme]
    button_ink = "#ffffff" if contrast(plan.accent, "#ffffff") >= 4.5 else "#101815"
    variables = {
        "bg": colors["background"],
        "paper": colors["surface"],
        "ink": colors["ink"],
        "muted": colors["muted"],
        "line": colors["line"],
        "accent": plan.accent,
        "button-ink": button_ink,
        "title-size": f"{plan.title_size}px",
        "radius": f"{plan.corner_radius}px",
        "columns": str(plan.columns),
    }
    style = ":root{" + ";".join(f"--{k}:{v}" for k, v in variables.items()) + "}\n" + STYLE
    style_hash = base64.b64encode(hashlib.sha256(style.encode()).digest()).decode()
    csp = f"default-src 'none'; style-src 'sha256-{style_hash}'; img-src data:; base-uri 'none'; form-action 'none'; object-src 'none'"
    ar = profile.language == "ar"
    labels = tuple(
        escape(tr(key, profile.language))
        for key in (
            "profile_skip",
            "profile_page",
            "profile_share",
            "profile_share_hint",
            "profile_download_png",
            "profile_download_svg",
            "profile_footer",
        )
    )
    identity_label = escape(tr("profile_identity", profile.language))
    contacts_label = escape(tr("profile_contact_links", profile.language))

    out = [
        f'<!doctype html><html lang="{profile.language}" dir="{"rtl" if ar else "ltr"}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
        f'<meta http-equiv="Content-Security-Policy" content="{escape(csp, quote=True)}">',
        f'<meta name="referrer" content="no-referrer"><title>{escape(profile.name)}</title><style>{style}</style></head><body>',
        f'<a class="skip" href="#main">{labels[0]}</a><div class="shell"><header class="masthead"><div class="brand">{SIGNATURE}<bdi>{escape(profile.name)}</bdi></div><span class="edition">{labels[1]}</span></header>',
        f'<main id="main"><section class="hero" data-header="{plan.hero}" data-alignment="{plan.alignment}" aria-labelledby="identity-title"><div class="identity">',
        f'<p class="eyebrow"><bdi>{escape(profile.role)}</bdi></p><h1 id="identity-title"><bdi>{escape(profile.name)}</bdi></h1><p class="intro" dir="auto">{escape(profile.intro)}</p></div>',
        f'<div class="identity-mark" aria-hidden="true"><span class="monogram">{escape(next((c for c in profile.name if c.isalpha()), "•"))}</span><span class="mark-note">01 / {identity_label}</span></div></section>',
        f'<nav class="actions" data-count="{len(profile.actions)}" aria-label="{contacts_label}">',
    ]
    for index in plan.action_order:
        action = profile.actions[index]
        primary = " primary" if index == plan.primary else ""
        out.append(
            f'<a class="action{primary}" href="{escape(action.url, quote=True)}" rel="noopener noreferrer"><bdi>{escape(action.label)}</bdi><span class="arrow" aria-hidden="true">↗</span></a>'
        )
    out.append('</nav><div class="content-grid">')
    for position, index in enumerate(plan.section_order, 1):
        section = profile.sections[index]
        out.extend(
            [
                f'<section class="section" aria-labelledby="section-{index}"><span class="section-no" aria-hidden="true">{position:02d}</span>',
                f'<h2 id="section-{index}" dir="auto">{escape(section.title)}</h2>',
            ]
        )
        if section.body:
            out.append(f'<p dir="auto">{escape(section.body)}</p>')
        if section.items:
            out.append(
                "<ul>"
                + "".join(f"<li><bdi>{escape(item)}</bdi></li>" for item in section.items)
                + "</ul>"
            )
        out.append("</section>")
    out.append("</div>")
    if embedded_qr and public_url is not None:
        qr = assets(public_url)
        out.extend(
            [
                f'<details class="sharing"><summary>{labels[2]}</summary><div class="share-body"><div class="qr-box"><img src="{data_url("image/png", qr["qr.png"])}" width="156" height="156" alt="QR"></div>',
                f'<div class="share-copy"><p>{labels[3]}</p><a class="public-url" href="{escape(public_url, quote=True)}" rel="noopener noreferrer">{escape(public_url)}</a><div class="downloads">',
            ]
        )
        for filename, mime, label in (
            ("qr.png", "image/png", labels[4]),
            ("qr.svg", "image/svg+xml", labels[5]),
        ):
            out.append(
                f'<a href="{data_url(mime, qr[filename])}" download="{filename}">{label}</a>'
            )
        out.append("</div></div></div></details>")
    out.append(
        f"</main><footer><span><bdi>{escape(profile.name)}</bdi></span><span>{labels[6]}</span></footer></div></body></html>"
    )
    return "".join(out).encode()


def share_card(profile, plan, *, public_url, embedded_qr=True):
    """A portrait share design; wrapping expands the canvas instead of clipping."""
    if type(embedded_qr) is not bool:
        raise ValueError("embedding choice must be boolean")
    profile = Profile.model_validate(profile)
    plan = plan_schema(profile).model_validate(
        plan.model_dump(mode="json") if isinstance(plan, Plan) else plan
    )
    https_url(public_url)
    colors = THEMES[plan.theme]
    regular_paths = (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    )
    measure = ImageDraw.Draw(Image.new("RGB", (1, 1)))

    def font(size, bold=False):
        candidates = (
            tuple(p.replace("Sans.ttf", "Sans-Bold.ttf") for p in regular_paths)
            if bold
            else regular_paths
        )
        path = next((p for p in candidates if Path(p).is_file()), None)
        if path is None:
            raise RuntimeError("DejaVu fonts required for share-card rendering")
        return ImageFont.truetype(path, size=size)

    def visual(value):
        return (
            value if features.check_feature("raqm") else get_display(arabic_reshaper.reshape(value))
        )

    def wrap(value, current):
        result, line = [], ""
        for word in value.split():
            trial = (line + " " + word).strip()
            if measure.textlength(visual(trial), font=current) <= 840:
                line = trial
                continue
            if line:
                result.append(line)
                line = ""
            chunk = ""
            for char in word:
                if chunk and measure.textlength(visual(chunk + char), font=current) > 840:
                    result.append(chunk)
                    chunk = ""
                chunk += char
            line = chunk
        if line:
            result.append(line)
        return result

    def layout(value, size, *, bold=False, limit=3, minimum=18):
        for chosen in range(size, minimum - 1, -2):
            current = font(chosen, bold)
            rows = wrap(value, current)
            if len(rows) <= limit:
                return current, rows, chosen * 1.65
        raise ValueError("share-card text exceeds layout")

    name = layout(profile.name, 72, bold=True, limit=2)
    role = layout(profile.role, 30, limit=3)
    address = layout(public_url, 18, limit=5, minimum=12)
    role_top = 215 + len(name[1]) * name[2] + 28
    qr_top = max(560, role_top + len(role[1]) * role[2] + 64)
    qr = None
    if embedded_qr:
        from app.builders.publication_qr import QUIET_ZONE, matrix

        modules = matrix(public_url)
        side = len(modules) + QUIET_ZONE * 2
        qr = Image.open(BytesIO(assets(public_url)["qr.png"]))
        qr = qr.resize((side * max(1, 504 // side),) * 2, Image.Resampling.NEAREST)
    label_top = qr_top + (qr.height + 48 if qr is not None else 100)
    url_top = label_top + 60
    height = max(1100, int(url_top + len(address[1]) * address[2] + 96))
    image = Image.new("RGB", (1080, height), colors["background"])
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((48, 48, 1032, height - 48), radius=32, fill=colors["surface"])
    draw.line((96, 160, 984, 160), fill=colors["line"], width=2)
    draw.line((96, 92, 128, 92), fill=plan.accent, width=3)
    draw.line((96, 92, 96, 124), fill=plan.accent, width=3)

    def paint(block, top, color):
        current, rows, step = block
        for row in rows:
            draw.text((540, top), visual(row), fill=color, font=current, anchor="mt")
            top += step

    paint(name, 215, colors["ink"])
    paint(role, role_top, colors["muted"])
    if qr is not None:
        image.paste(qr, ((1080 - qr.width) // 2, int(qr_top)))
    label = tr("profile_scan_page" if embedded_qr else "profile_link", profile.language)
    paint(layout(label, 26, limit=1), label_top, colors["muted"])
    paint(address, url_top, colors["ink"])
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def bundle(profile, plan, *, public_url, embedded_qr=True):
    """Always include separate QR files; embedding is an independent customer choice."""
    result = assets(public_url)
    result["profile.html"] = build(profile, plan, public_url=public_url, embedded_qr=embedded_qr)
    result["share-card.png"] = share_card(
        profile, plan, public_url=public_url, embedded_qr=embedded_qr
    )
    return result
