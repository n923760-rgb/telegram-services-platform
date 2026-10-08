from datetime import date
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    StrictFloat,
    StrictInt,
    StringConstraints,
    model_validator,
)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Section(StrictModel):
    heading: str = Field(default="", max_length=500)
    paragraphs: list[Annotated[str, StringConstraints(strip_whitespace=False)]] = Field(
        default_factory=list, max_length=100
    )
    bullets: list[str] = Field(default_factory=list, max_length=100)

    @model_validator(mode="after")
    def bounded(self):
        if any(len(x) > 12000 for x in self.paragraphs + self.bullets):
            raise ValueError("text too long")
        return self


class Document(StrictModel):
    title: str = Field(min_length=1, max_length=500)
    sections: list[Section] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def nonempty(self):
        if not any(s.heading or s.paragraphs or s.bullets for s in self.sections):
            raise ValueError("empty document")
        if len(self.model_dump_json()) > 100000:
            raise ValueError("document too large")
        return self


Cell = str | StrictInt | StrictFloat | StrictBool | None


class ColumnFormat(StrictModel):
    # Meaning, not executable Excel format strings supplied by the model.
    kind: Literal["text", "number", "date", "percent", "boolean"]


class Table(StrictModel):
    title: str = Field(min_length=1, max_length=200)
    columns: list[str] = Field(min_length=1, max_length=50)
    rows: list[list[Cell]] = Field(min_length=1, max_length=1000)
    column_formats: list[ColumnFormat] = Field(default_factory=list, max_length=50)

    @model_validator(mode="after")
    def rectangular(self):
        if len(set(self.columns)) != len(self.columns) or any(
            not c.strip() or len(c) > 200 for c in self.columns
        ):
            raise ValueError("invalid columns")
        if any(len(row) != len(self.columns) for row in self.rows):
            raise ValueError("ragged table")
        if self.column_formats and len(self.column_formats) != len(self.columns):
            raise ValueError("column formats must match columns")
        if len(self.model_dump_json()) > 200000:
            raise ValueError("table too large")
        for row in self.rows:
            for index, cell in enumerate(row):
                if isinstance(cell, str) and len(cell) > 4000:
                    raise ValueError("cell too long")
                if isinstance(cell, float) and not __import__("math").isfinite(cell):
                    raise ValueError("invalid number")
                if type(cell) in (int, float) and abs(cell) >= 10**15:
                    raise ValueError("Excel numeric precision exceeded; preserve as text")
                if (
                    isinstance(cell, float)
                    and len(Decimal(str(cell)).normalize().as_tuple().digits) > 15
                ):
                    raise ValueError("Excel numeric precision exceeded; preserve as text")
                if not self.column_formats or cell is None:
                    continue
                kind = self.column_formats[index].kind
                if kind == "text" and not isinstance(cell, str):
                    raise ValueError("text column requires strings")
                if kind in ("number", "percent") and type(cell) not in (int, float):
                    raise ValueError("numeric column requires numbers")
                if kind == "boolean" and not isinstance(cell, bool):
                    raise ValueError("boolean column requires booleans")
                if kind == "date":
                    if not isinstance(cell, str) or len(cell) != 10:
                        raise ValueError("date column requires Gregorian ISO dates")
                    parsed = date.fromisoformat(cell)
                    if parsed.isoformat() != cell or parsed.year < 1900:
                        raise ValueError("date outside supported Excel range")
        return self


class SlideTable(StrictModel):
    columns: list[str] = Field(min_length=1, max_length=4)
    rows: list[list[str]] = Field(min_length=1, max_length=6)

    @model_validator(mode="after")
    def bounded(self):
        if len(set(self.columns)) != len(self.columns) or any(
            not c.strip() or len(c) > 50 for c in self.columns
        ):
            raise ValueError("invalid slide table headers")
        if any(len(row) != len(self.columns) for row in self.rows):
            raise ValueError("ragged slide table")
        if any(len(cell) > 80 for row in self.rows for cell in row):
            raise ValueError("slide table cell too long")
        return self


class Slide(StrictModel):
    title: str = Field(min_length=1, max_length=150)
    bullets: list[str] = Field(default_factory=list, max_length=6)
    table: SlideTable | None = None

    @model_validator(mode="after")
    def limit(self):
        if any(len(b) > 180 for b in self.bullets):
            raise ValueError("slide overflow risk")
        if bool(self.bullets) == (self.table is not None) or any(
            not b.strip() for b in self.bullets
        ):
            raise ValueError("slide requires either nonempty bullets or a table")
        return self


class Deck(StrictModel):
    slides: list[Slide] = Field(min_length=1, max_length=30)

    @model_validator(mode="after")
    def readable(self):
        from app.builders.pptx_layout import plan_slide

        if len(self.model_dump_json()) > 100000:
            raise ValueError("deck too large")
        for index, slide in enumerate(self.slides):
            texts = [slide.title, *slide.bullets]
            if slide.table is not None:
                texts.extend(slide.table.columns)
                texts.extend(cell for row in slide.table.rows for cell in row)
            if any(
                (ord(c) < 32 and c not in "\t\n")
                or 0xD800 <= ord(c) <= 0xDFFF
                or ord(c) in {0xFFFE, 0xFFFF}
                for text in texts
                for c in text
            ):
                raise ValueError("invalid slide text")
            plan_slide(slide, cover_candidate=index == 0 and len(self.slides) > 1)
        return self
