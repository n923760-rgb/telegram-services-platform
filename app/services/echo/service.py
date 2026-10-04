from decimal import Decimal

from app.core.i18n import tr
from app.services.base import BaseService, InputField, InputSchema, Result
from app.services.echo.schema import EchoInput


class Echo(BaseService):
    slug = "echo"
    name_ar = tr("echo_name")
    name_en = tr("echo_name", "en")
    description_ar = tr("echo_description")
    price_sar = Decimal("1.00")
    input_schema = InputSchema(fields=[InputField(name="text", prompt_key="input_text")])

    async def run(self, inputs):
        value = EchoInput.model_validate(inputs)
        return Result(text=value.text)


SERVICE = Echo
