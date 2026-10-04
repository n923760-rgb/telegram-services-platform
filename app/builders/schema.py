from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    StrictFloat,
    StrictInt,
    model_validator,
)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Section(StrictModel):
    heading: str = Field(default="", max_length=500)
    paragraphs: list[str] = Field(default_factory=list, max_length=100)
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


class Table(StrictModel):
    title: str = Field(min_length=1, max_length=200)
    columns: list[str] = Field(min_length=1, max_length=50)
    rows: list[list[Cell]] = Field(min_length=1, max_length=1000)

    @model_validator(mode="after")
    def rectangular(self):
        if len(set(self.columns)) != len(self.columns) or any(not c.strip() for c in self.columns):
            raise ValueError("invalid columns")
        if any(len(row) != len(self.columns) for row in self.rows):
            raise ValueError("ragged table")
        if len(self.model_dump_json()) > 200000:
            raise ValueError("table too large")
        for row in self.rows:
            for cell in row:
                if isinstance(cell, str) and len(cell) > 4000:
                    raise ValueError("cell too long")
                if isinstance(cell, float) and not __import__("math").isfinite(cell):
                    raise ValueError("invalid number")
        return self


class Slide(StrictModel):
    title: str = Field(min_length=1, max_length=150)
    bullets: list[str] = Field(min_length=1, max_length=6)

    @model_validator(mode="after")
    def limit(self):
        if any(len(b) > 180 for b in self.bullets):
            raise ValueError("slide overflow risk")
        return self


class Deck(StrictModel):
    slides: list[Slide] = Field(min_length=1, max_length=30)
