"""Preserve PDF page selection and reject multiline input."""

import unittest

from app.files.pdf_selection import page_selection


class PageSelectionBoundaryTests(unittest.TestCase):
    def test_arabic_digits_and_order(self):
        self.assertEqual(page_selection("٣، ١ - ٢"), [3, 1, 2])

    def test_ordinary_ranges(self):
        self.assertEqual(page_selection("1-3,5"), [1, 2, 3, 5])

    def test_all_line_separators_rejected(self):
        separators = "\r\n\v\f\x1c\x1d\x1e\x85\u2028\u2029"
        for character in separators:
            with self.subTest(character=repr(character)):
                with self.assertRaises(ValueError):
                    page_selection("1" + character)

    def test_invalid_ranges_and_duplicates(self):
        for value in ("1,1", "3-1", "0", "201", "1-201"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    page_selection(value)

    def test_maximum_page_range(self):
        self.assertEqual(page_selection("1-200"), list(range(1, 201)))


if __name__ == "__main__":
    unittest.main()
