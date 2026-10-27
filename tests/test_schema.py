
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


BASE_DIR = Path(__file__).resolve().parent.parent
SCHEMA_FILE = BASE_DIR / "schema.json"
BOOKS_FILE = BASE_DIR / "output" / "books.json"


class TestBookSchema(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with SCHEMA_FILE.open(encoding="utf-8") as file:
            cls.schema = json.load(file)

        cls.validator = Draft202012Validator(
            cls.schema,
            format_checker=FormatChecker(),
        )

    def test_schema_definition_is_valid(self):
        Draft202012Validator.check_schema(self.schema)

    def test_saved_book_records_match_schema(self):
        self.assertTrue(
            BOOKS_FILE.exists(),
            "Run the scraper first to generate output/books.json.",
        )

        with BOOKS_FILE.open(encoding="utf-8") as file:
            records = json.load(file)

        self.assertGreater(len(records), 0)

        errors = [
            error
            for record in records
            for error in self.validator.iter_errors(record)
        ]

        self.assertEqual(
            errors,
            [],
            "Some saved book records do not match schema.json.",
        )


if __name__ == "__main__":
    unittest.main()
