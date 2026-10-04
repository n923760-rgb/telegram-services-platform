from pydantic import ValidationError

from app.ops.costs import reserve_call, settle_call, uncertain_call
from app.services.base import ServiceError


class AI:
    def __init__(self, provider, job_id=None, user_id=None):
        self.provider, self.job_id, self.user_id = provider, job_id, user_id

    async def extract(self, schema, input, prompt="", images=None, language=None, style=None):
        images = images or []
        if self.job_id is None or self.user_id is None:
            raise ServiceError("provider_config")
        # One initial call plus exactly one schema-repair attempt; no autonomous loop.
        for attempt in range(2):
            instruction = prompt + (
                "\nPrevious output failed validation. Return the exact JSON schema, with all required fields and correct types."
                if attempt
                else ""
            )
            effective = (
                f"Translate accurately to {language}, style {style}. Preserve all names, numbers, and meaning."
                if language
                else instruction
            )
            bound = self.provider.upper_bound(schema.model_json_schema(), input, effective, images)
            hold = await reserve_call(self.job_id, self.user_id, bound)
            try:
                if language and not attempt:
                    response = await self.provider.translate(
                        schema.model_json_schema(), input, language, style
                    )
                elif images:
                    response = await self.provider.extract_from_image(
                        schema.model_json_schema(), input, instruction, images
                    )
                else:
                    response = await self.provider.extract_from_text(
                        schema.model_json_schema(),
                        input,
                        effective
                        + (
                            " Return the exact JSON schema after the previous validation failure."
                            if attempt
                            else ""
                        ),
                    )
            except Exception:
                await uncertain_call(hold)
                raise
            # Record billable usage even when the output cannot be parsed or validated.
            await settle_call(
                hold,
                response.usage.cost_sar,
                response.usage.input_tokens,
                response.usage.output_tokens,
                provider=response.usage.provider,
                model=response.usage.model,
                rates=response.usage.rates,
            )
            try:
                return schema.model_validate_json(response.content)
            except (ValidationError, ValueError):
                if attempt:
                    raise ServiceError("provider_invalid") from None
        raise ServiceError("provider_invalid")
