from typing import ClassVar

from pydantic import Field, model_validator
from pydantic_core import PydanticCustomError

from app.builders.schema import Document, StrictModel
from app.services.document_fidelity import DOCUMENT_DIAGNOSTICS
from app.services.documents import DocumentInputs


class Inputs(DocumentInputs):
    pass


class PdfPlan(StrictModel):
    diagnostic_categories: ClassVar = DOCUMENT_DIAGNOSTICS
    ambiguous: bool = False
    missing_information: bool = Field(
        default=False,
        description="True only when essential source facts are absent. Short notes and an omitted title are valid source content, not missing information.",
    )
    question: str = Field(
        default="", max_length=1000, description="Required and nonblank when ambiguous is true."
    )
    document: Document | None = Field(
        default=None,
        description="Provide a complete document unless missing_information is true. Never omit the body merely because the source is short.",
    )

    @model_validator(mode="after")
    def valid(self):
        if not self.missing_information and self.document is None:
            raise PydanticCustomError("document_missing_body", "missing document")
        if self.ambiguous and not self.question:
            raise PydanticCustomError("document_missing_question", "missing clarification")
        return self
