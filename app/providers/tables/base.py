from abc import ABC, abstractmethod
from typing import Annotated, Literal

from pydantic import Field, StrictInt, StringConstraints, model_validator

from app.builders.schema import StrictModel

Cell = Annotated[str, StringConstraints(strip_whitespace=False, max_length=500)]


class ExtractedTable(StrictModel):
    page: StrictInt = Field(ge=1, le=5)
    rows: list[list[Cell]] = Field(min_length=2, max_length=200)
    accuracy: float = Field(ge=95, le=100, allow_inf_nan=False)
    whitespace: float = Field(ge=0, le=30, allow_inf_nan=False)

    @model_validator(mode="after")
    def rectangular(self):
        width = len(self.rows[0])
        if not 2 <= width <= 12 or any(len(row) != width for row in self.rows):
            raise ValueError("table shape limit")
        for row in self.rows:
            for cell in row:
                if (
                    any(
                        (ord(c) < 32 and c not in "\t\n")
                        or 0xD800 <= ord(c) <= 0xDFFF
                        or ord(c) in {0xFFFE, 0xFFFF}
                        for c in cell
                    )
                    or cell.count("\n") > 10
                ):
                    raise ValueError("invalid table cell")
        return self


class Extraction(StrictModel):
    pages: StrictInt = Field(ge=1, le=5)
    tables: list[ExtractedTable] = Field(min_length=1, max_length=5)

    @model_validator(mode="after")
    def bounded(self):
        if {table.page for table in self.tables} != set(range(1, self.pages + 1)):
            raise ValueError("every page must contain an accepted table")
        if (
            sum(len(row) for table in self.tables for row in table.rows) > 5000
            or sum(len(cell) for table in self.tables for row in table.rows for cell in row) > 50000
        ):
            raise ValueError("extraction size limit")
        if [table.page for table in self.tables] != sorted(table.page for table in self.tables):
            raise ValueError("source page ordering")
        return self


class TableExtractor(ABC):
    @abstractmethod
    async def extract(self, data: bytes, method: Literal["lattice", "stream"]) -> Extraction: ...
