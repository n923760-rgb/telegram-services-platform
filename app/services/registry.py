import importlib
import pkgutil
import re
from copy import deepcopy

from sqlalchemy import select

import app.services
from app.core.models import Service
from app.services.base import BaseService
from app.wallet.ledger import halalas


def _input_contract(schema):
    """Ignore only the no-op defaults added to InputField in the title upgrade.

    Preserve unknown keys and every other difference so real changes still need a bump.
    Copy rather than mutate the DB snapshot or a plugin's schema.
    """
    result = deepcopy(schema)

    def normalize(fields):
        for field in fields:
            if field.get("skip_key") == "skip_field":
                field.pop("skip_key")
            if field.get("single_line") is False:
                field.pop("single_line")
            normalize(field.get("fields", []))

    normalize(result.get("fields", []))
    return result


class Registry:
    def __init__(self):
        self.types: dict[str, type[BaseService]] = {}

    def discover(self):
        for info in pkgutil.iter_modules(app.services.__path__):
            if info.ispkg:
                module = importlib.import_module(f"app.services.{info.name}.service")
                cls = module.SERVICE
                if not issubclass(cls, BaseService) or cls.slug != info.name:
                    raise ValueError("invalid service plugin")
                if not re.fullmatch(r"[a-z][a-z0-9_]{0,39}", cls.slug) or not re.fullmatch(
                    r"[A-Za-z0-9_.-]{1,32}", cls.version
                ):
                    raise ValueError("invalid service plugin")
                if cls.slug in self.types:
                    raise ValueError("duplicate service")
                self.types[cls.slug] = cls
        return self

    def get(self, slug, runtime=None):
        service = self.types[slug]()
        service.runtime = runtime
        return service

    async def sync(self, db):
        from sqlalchemy.dialects.postgresql import insert

        from app.core.i18n import CATALOGS

        for slug, cls in self.types.items():
            for field in cls.input_schema.conversation():
                if any(
                    key not in CATALOGS["ar"] or key not in CATALOGS["en"]
                    for key in [
                        field.prompt_key,
                        *field.choice_keys,
                        *([field.skip_key] if not field.required else []),
                    ]
                ):
                    raise ValueError("missing service i18n")
            current = await db.get(Service, slug)
            schema = cls.input_schema.model_dump()
            if (
                current
                and current.version == cls.version
                and _input_contract(current.input_schema) != _input_contract(schema)
            ):
                raise ValueError(
                    f"Bump the plugin version before changing its input contract: {slug}"
                )
            metadata = dict(
                version=cls.version,
                name_ar=cls.name_ar,
                name_en=cls.name_en,
                description_ar=cls.description_ar,
                input_schema=schema,
            )
            statement = insert(Service).values(
                slug=slug,
                price_halala=halalas(cls.price_sar),
                enabled=cls.enabled_by_default,
                **metadata,
            )
            await db.execute(
                statement.on_conflict_do_update(index_elements=[Service.slug], set_=metadata)
            )
        for row in (await db.scalars(select(Service))).all():
            if row.slug not in self.types:
                row.enabled = False
        await db.flush()


registry = Registry().discover()
