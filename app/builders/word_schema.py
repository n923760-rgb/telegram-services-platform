"""Bounded Word-only structure; PDF and other service plans keep their contracts."""

from pydantic import Field, model_validator

from app.builders.schema import Document, Section, StrictModel


class WordTable(StrictModel):
    caption: str = Field(default="", max_length=200)
    columns: list[str] = Field(min_length=1, max_length=6)
    rows: list[list[str]] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def bounded_table(self):
        if len(set(self.columns)) != len(self.columns) or any(
            not c.strip() or len(c) > 80 for c in self.columns
        ):
            raise ValueError("invalid Word columns")
        if any(len(row) != len(self.columns) for row in self.rows):
            raise ValueError("ragged Word table")
        if any(len(cell) > 240 for row in self.rows for cell in row):
            raise ValueError("Word cell too long")
        return self


class WordSection(Section):
    tables: list[WordTable] = Field(default_factory=list, max_length=3)


class WordDocument(Document):
    sections: list[WordSection] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def nonempty(self):
        if not any(s.heading or s.paragraphs or s.bullets or s.tables for s in self.sections):
            raise ValueError("empty Word document")
        if len(self.model_dump_json()) > 100000 or sum(len(s.tables) for s in self.sections) > 10:
            raise ValueError("Word document too large")
        text = [self.title]
        for section in self.sections:
            text.extend([section.heading, *section.paragraphs, *section.bullets])
            for table in section.tables:
                text.extend([table.caption, *table.columns])
                text.extend(cell for row in table.rows for cell in row)
        if any(
            (ord(c) < 32 and c not in "\t\r\n")
            or 0xD800 <= ord(c) <= 0xDFFF
            or ord(c) in {0xFFFE, 0xFFFF}
            for value in text
            for c in value
        ):
            raise ValueError("invalid Word text")
        return self
