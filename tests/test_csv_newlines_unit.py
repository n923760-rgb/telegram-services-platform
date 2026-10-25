"""Quoted CSV cell newlines are customer data, independent of record separators."""

import csv
from io import BytesIO, StringIO

import pytest
from openpyxl import load_workbook

from app.builders.csv_review import build
from app.services.base import ServiceError
from app.services.csv_review.schema import Inputs


@pytest.fixture(autouse=True)
def database():
    yield


@pytest.mark.parametrize("record_separator", ["\n", "\r\n", "\r"])
@pytest.mark.parametrize("cell_separator", ["\n", "\r\n", "\r"])
@pytest.mark.parametrize("trim", [False, True])
def test_source_and_data_retain_quoted_newlines_and_only_requested_space_trimming(
    record_separator, cell_separator, trim
):
    value = "  أول 00123" + cell_separator + 'Second "quoted", 0  '
    stream = StringIO(newline="")
    writer = csv.writer(stream, lineterminator=record_separator, quoting=csv.QUOTE_ALL)
    writer.writerows([["ID", "Note"], ["00123", value], ["00017", "=1+1"]])
    source = stream.getvalue()
    parsed = Inputs.parse(
        dict(
            text=source, delimiter="comma", whitespace="trim" if trim else "preserve", language="en"
        )
    )
    assert parsed.text == source
    headers, rows = parsed.records()
    assert rows == [["00123", value], ["00017", "=1+1"]]
    data, counts = build(headers, rows, trim=trim, language="en")
    with BytesIO(data) as output:
        book = load_workbook(output)
        assert book["Source"]["B4"].value == value
        assert book["Data"]["B4"].value == (value.strip(" \t") if trim else value)
        for name in ("Data", "Source"):
            assert book[name]["A4"].value == "00123"
            assert book[name]["B5"].value == "=1+1"
            assert book[name]["B5"].data_type == "s"
        assert counts["rows"] == 2 and counts["changes"] == int(trim)
        book.close()


@pytest.mark.parametrize("separator", ["\n", "\r\n", "\r"])
@pytest.mark.parametrize("lines,accepted", [(11, True), (12, False)])
def test_multiline_limit_counts_each_logical_line_without_mutating_source(
    separator, lines, accepted
):
    value = separator.join(["entry"] * lines)
    source = 'ID,Note\n00123,"' + value + '"\n'
    inputs = dict(text=source, delimiter="comma", whitespace="preserve", language="en")
    if accepted:
        assert Inputs.parse(inputs).records()[1][0][1] == value
    else:
        with pytest.raises(ServiceError, match="input_invalid"):
            Inputs.parse(inputs)


@pytest.mark.parametrize("bad", ["\x00", "\x01", "\ud800", "\uffff"])
def test_control_and_invalid_unicode_rejection_remains_before_processing(bad):
    with pytest.raises(ServiceError, match="input_invalid"):
        Inputs.parse(
            dict(
                text="ID,Note\n00123," + bad,
                delimiter="comma",
                whitespace="preserve",
                language="en",
            )
        )


@pytest.mark.parametrize("separator", ["\n", "\r\n", "\r"])
@pytest.mark.parametrize("position", ["start", "middle", "end"])
def test_quoted_header_line_breaks_cannot_hide_in_outer_whitespace(separator, position):
    header = {
        "start": separator + "Note",
        "middle": "No" + separator + "te",
        "end": "Note" + separator,
    }[position]
    with pytest.raises(ServiceError, match="input_invalid"):
        Inputs.parse(
            dict(
                text='ID,"' + header + '"\n00123,value',
                delimiter="comma",
                whitespace="preserve",
                language="en",
            )
        )
