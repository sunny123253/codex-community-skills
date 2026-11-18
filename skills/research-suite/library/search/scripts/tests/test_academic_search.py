from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import academic_search


class _Response:
    def __init__(self, payload: dict) -> None:
        self.payload = json.dumps(payload).encode("utf-8")

    def __enter__(self) -> "_Response":
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def read(self) -> bytes:
        return self.payload


class AcademicSearchTests(unittest.TestCase):
    def test_openalex_search_returns_complete_abstract_and_source(self) -> None:
        payload = {
            "results": [
                {
                    "id": "https://openalex.org/W1",
                    "title": "A paper",
                    "abstract_inverted_index": {
                        "A": [0],
                        "complete": [1],
                        "public": [2],
                        "abstract": [3],
                    },
                    "authorships": [],
                    "doi": "https://doi.org/10.1234/example",
                    "publication_year": 2026,
                    "publication_date": "2026-09-27",
                    "cited_by_count": 0,
                    "primary_location": {"source": {"display_name": "Journal"}},
                    "relevance_score": 1.0,
                }
            ]
        }

        with patch.object(
            academic_search.urllib.request,
            "urlopen",
            return_value=_Response(payload),
        ):
            results = academic_search.search("topic", limit=1, require_abstract=True)

        self.assertEqual(results[0]["abstract"], "A complete public abstract")
        self.assertEqual(results[0]["abstract_source"], "openalex")

    def test_openalex_search_require_abstract_filters_empty_records(self) -> None:
        payload = {
            "results": [
                {
                    "id": "https://openalex.org/W1",
                    "title": "Has abstract",
                    "abstract_inverted_index": {"Text": [0]},
                    "authorships": [],
                    "publication_year": 2026,
                    "publication_date": "2026-09-27",
                    "cited_by_count": 0,
                    "primary_location": {"source": {"display_name": "Journal"}},
                    "relevance_score": 1.0,
                },
                {
                    "id": "https://openalex.org/W2",
                    "title": "Metadata only",
                    "abstract_inverted_index": None,
                    "authorships": [],
                    "publication_year": 2026,
                    "publication_date": "2026-09-26",
                    "cited_by_count": 0,
                    "primary_location": {"source": {"display_name": "Journal"}},
                    "relevance_score": 0.9,
                },
            ]
        }

        with patch.object(
            academic_search.urllib.request,
            "urlopen",
            return_value=_Response(payload),
        ):
            results = academic_search.search("topic", limit=2, require_abstract=True)

        self.assertEqual([item["title"] for item in results], ["Has abstract"])
