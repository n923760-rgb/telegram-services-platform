from pydantic import Field

from app.builders.schema import Document, StrictModel


class Inputs(StrictModel):
    pdf: str = Field(min_length=1, max_length=12000)


class WordPlan(StrictModel):
    missing_information: bool = False
    document: Document | None = None
