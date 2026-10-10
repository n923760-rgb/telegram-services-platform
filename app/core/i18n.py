import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "i18n"
CATALOGS = {lang: json.loads((ROOT / f"{lang}.json").read_text()) for lang in ("ar", "en")}


def tr(key: str, lang: str = "ar", **values) -> str:
    return (
        CATALOGS.get(lang, CATALOGS["ar"]).get(key, CATALOGS["ar"].get(key, key)).format(**values)
    )


def translations(key: str, **values) -> dict[str, str]:
    return {lang: tr(key, lang, **values) for lang in CATALOGS}
