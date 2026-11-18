#!/usr/bin/env python3
"""Resolve a public paper title and abstract from scholarly identifiers.

The resolver follows the public-source strategy used by the academic-search
workflow. It never writes an abstract that was not returned by a source.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections.abc import Callable, Mapping
from typing import Any


ATOM_NS = "http://www.w3.org/2005/Atom"
DEFAULT_USER_AGENT = (
    "nature-academic-search/abstract-lookup "
    "(+https://github.com/wp-a/nature-academic-search)"
)
JsonFetcher = Callable[..., Mapping[str, Any]]
TextFetcher = Callable[..., str]


def clean_text(value: Any) -> str:
    """Return readable text with markup, entities, and repeated whitespace removed."""
    if value is None:
        return ""
    text = html.unescape(str(value))
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def reconstruct_abstract(inverted_index: Mapping[str, Any] | None) -> str:
    """Reconstruct an OpenAlex abstract from its word-to-position index."""
    if not inverted_index:
        return ""

    words: list[tuple[int, str]] = []
    for word, positions in inverted_index.items():
        if not isinstance(positions, list):
            continue
        for position in positions:
            try:
                words.append((int(position), str(word)))
            except (TypeError, ValueError):
                continue
    words.sort(key=lambda item: item[0])
    return " ".join(word for _, word in words).strip()


def is_verified_record(record: Mapping[str, Any]) -> bool:
    """Return whether a record has both a title and a retrieved abstract."""
    return bool(str(record.get("title") or "").strip()) and bool(
        str(record.get("abstract") or "").strip()
    )


def normalize_doi(value: Any) -> str:
    """Normalize a DOI URL or prefix to a bare lowercase DOI."""
    if value is None:
        return ""
    doi = str(value).strip()
    doi = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", doi, flags=re.I)
    doi = re.sub(r"^doi:\s*", "", doi, flags=re.I)
    return doi.rstrip(".,);]").strip().lower()


def normalize_arxiv_id(value: Any) -> str:
    """Normalize an arXiv URL or versioned identifier."""
    if value is None:
        return ""
    raw = str(value).strip()
    match = re.search(r"arxiv\.org/(?:abs|pdf)/([^?#]+)", raw, flags=re.I)
    if match:
        raw = match.group(1)
    raw = raw.removeprefix("arXiv:").removeprefix("arxiv:")
    return re.sub(r"v\d+$", "", raw).strip()


def fetch_json(
    url: str,
    *,
    params: Mapping[str, Any] | None = None,
    headers: Mapping[str, str] | None = None,
    timeout: int = 30,
) -> Mapping[str, Any]:
    """Fetch a JSON object from a public endpoint."""
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": DEFAULT_USER_AGENT,
            **dict(headers or {}),
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("JSON response is not an object")
    return payload


def fetch_text(
    url: str,
    *,
    params: Mapping[str, Any] | None = None,
    headers: Mapping[str, str] | None = None,
    timeout: int = 30,
) -> str:
    """Fetch a text response from a public endpoint."""
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(
        url,
        headers={"User-Agent": DEFAULT_USER_AGENT, **dict(headers or {})},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8")


def parse_openalex(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Extract title, identifier, and reconstructed abstract from OpenAlex."""
    work: Mapping[str, Any] = payload
    results = payload.get("results")
    if isinstance(results, list) and results and isinstance(results[0], Mapping):
        work = results[0]
    openalex_id = str(work.get("id") or work.get("openalex_id") or "").strip()
    if openalex_id:
        openalex_id = openalex_id.rsplit("/", 1)[-1]
    return {
        "title": clean_text(work.get("display_name") or work.get("title")),
        "abstract": reconstruct_abstract(work.get("abstract_inverted_index")),
        "doi": normalize_doi(work.get("doi")),
        "openalex_id": openalex_id,
        "source_url": str(work.get("id") or work.get("doi") or ""),
    }


def parse_crossref(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Extract and clean title and abstract from a Crossref response."""
    message = payload.get("message")
    if not isinstance(message, Mapping):
        message = payload
    titles = message.get("title")
    title = titles[0] if isinstance(titles, list) and titles else message.get("title")
    return {
        "title": clean_text(title),
        "abstract": clean_text(message.get("abstract")),
        "doi": normalize_doi(message.get("DOI") or message.get("doi")),
        "source_url": str(message.get("URL") or ""),
    }


def parse_semantic_scholar(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Extract title and abstract from a Semantic Scholar paper response."""
    external_ids = payload.get("externalIds")
    external_ids = external_ids if isinstance(external_ids, Mapping) else {}
    return {
        "title": clean_text(payload.get("title")),
        "abstract": clean_text(payload.get("abstract")),
        "doi": normalize_doi(external_ids.get("DOI")),
        "semantic_scholar_id": str(payload.get("paperId") or ""),
        "source_url": "",
    }


def _element_text(element: ET.Element | None) -> str:
    return clean_text(" ".join(element.itertext())) if element is not None else ""


def parse_arxiv(xml_text: str) -> dict[str, Any]:
    """Extract title, abstract, and arXiv ID from an Atom response."""
    root = ET.fromstring(xml_text)
    entry = root.find(f"{{{ATOM_NS}}}entry")
    if entry is None:
        return {"title": "", "abstract": "", "arxiv_id": "", "source_url": ""}
    source_url = _element_text(entry.find(f"{{{ATOM_NS}}}id"))
    arxiv_id = normalize_arxiv_id(source_url)
    return {
        "title": _element_text(entry.find(f"{{{ATOM_NS}}}title")),
        "abstract": _element_text(entry.find(f"{{{ATOM_NS}}}summary")),
        "arxiv_id": arxiv_id,
        "source_url": source_url,
    }


def parse_europe_pmc(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Extract title and abstract from an Europe PMC core search response."""
    result_list = payload.get("resultList")
    results = result_list.get("result") if isinstance(result_list, Mapping) else None
    result = results[0] if isinstance(results, list) and results else payload
    if not isinstance(result, Mapping):
        result = {}
    return {
        "title": clean_text(result.get("title")),
        "abstract": clean_text(result.get("abstractText")),
        "doi": normalize_doi(result.get("doi")),
        "pmid": str(result.get("pmid") or ""),
        "pmcid": str(result.get("pmcid") or ""),
        "source_url": "",
    }


def parse_pubmed(xml_text: str) -> dict[str, Any]:
    """Extract a joined structured abstract from PubMed XML."""
    root = ET.fromstring(xml_text)
    article = root.find("PubmedArticle")
    if article is None:
        return {"title": "", "abstract": "", "source_url": ""}
    citation = article.find("MedlineCitation")
    article_data = citation.find("Article") if citation is not None else None
    if article_data is None:
        return {"title": "", "abstract": "", "source_url": ""}
    title = _element_text(article_data.find("ArticleTitle"))
    abstract_parts: list[str] = []
    abstract = article_data.find("Abstract")
    if abstract is not None:
        for part in abstract.findall("AbstractText"):
            text = _element_text(part)
            label = clean_text(part.get("Label"))
            if text:
                abstract_parts.append(f"{label}: {text}" if label else text)
    pmid = _element_text(citation.find("PMID")) if citation is not None else ""
    return {
        "title": title,
        "abstract": " ".join(abstract_parts),
        "pmid": pmid,
        "source_url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "",
    }


def _source_plan(
    *,
    doi: str,
    arxiv_id: str,
    openalex_id: str,
    pmid: str,
    pmcid: str,
    semantic_scholar_id: str,
    mailto: str,
) -> list[tuple[str, str, str, dict[str, Any], Callable[[Any], dict[str, Any]]]]:
    plan: list[tuple[str, str, str, dict[str, Any], Callable[[Any], dict[str, Any]]]] = []
    if arxiv_id:
        plan.append(
            (
                "arxiv",
                "text",
                "https://export.arxiv.org/api/query",
                {"id_list": arxiv_id, "max_results": 1},
                parse_arxiv,
            )
        )
    if openalex_id or doi:
        target = openalex_id or f"doi:{doi}"
        target = target.rsplit("/", 1)[-1] if target.startswith("http") else target
        plan.append(
            (
                "openalex",
                "json",
                f"https://api.openalex.org/works/{urllib.parse.quote(target, safe=':')}",
                {"mailto": mailto} if mailto else {},
                parse_openalex,
            )
        )
    if doi:
        plan.append(
            (
                "crossref",
                "json",
                f"https://api.crossref.org/works/{urllib.parse.quote(doi, safe='')}",
                {},
                parse_crossref,
            )
        )
    if semantic_scholar_id or doi:
        target = semantic_scholar_id or f"DOI:{doi}"
        plan.append(
            (
                "semantic_scholar",
                "json",
                f"https://api.semanticscholar.org/graph/v1/paper/{urllib.parse.quote(target, safe=':')}",
                {"fields": "title,abstract,externalIds,paperId"},
                parse_semantic_scholar,
            )
        )
    if pmid or pmcid:
        epmc_id = pmid or pmcid
        source = "MED" if pmid else "PMC"
        plan.append(
            (
                "europe_pmc",
                "json",
                "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
                {
                    "query": f"EXT_ID:{epmc_id} AND SRC:{source}",
                    "format": "json",
                    "resultType": "core",
                    "pageSize": 1,
                },
                parse_europe_pmc,
            )
        )
        if pmid:
            plan.append(
                (
                    "pubmed",
                    "text",
                    "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
                    {"db": "pubmed", "id": pmid, "retmode": "xml", "rettype": "abstract"},
                    parse_pubmed,
                )
            )
    return plan


def resolve_record(
    *,
    doi: str = "",
    arxiv_id: str = "",
    openalex_id: str = "",
    pmid: str = "",
    pmcid: str = "",
    semantic_scholar_id: str = "",
    mailto: str = "",
    semantic_scholar_api_key: str = "",
    timeout: int = 30,
    fetch_json_fn: JsonFetcher = fetch_json,
    fetch_text_fn: TextFetcher = fetch_text,
) -> dict[str, Any]:
    """Resolve one paper and return metadata, provenance, and validation status."""
    doi = normalize_doi(doi)
    arxiv_id = normalize_arxiv_id(arxiv_id)
    openalex_id = str(openalex_id or "").strip().rsplit("/", 1)[-1]
    pmid = str(pmid or "").strip()
    pmcid = str(pmcid or "").strip()
    semantic_scholar_id = str(semantic_scholar_id or "").strip()
    if not any((doi, arxiv_id, openalex_id, pmid, pmcid, semantic_scholar_id)):
        raise ValueError("At least one scholarly identifier is required")

    result: dict[str, Any] = {
        "title": "",
        "abstract": "",
        "abstract_source": "",
        "abstract_status": "missing",
        "doi": doi,
        "arxiv_id": arxiv_id,
        "openalex_id": openalex_id,
        "pmid": pmid,
        "pmcid": pmcid,
        "semantic_scholar_id": semantic_scholar_id,
        "source_attempts": [],
    }
    headers = {"User-Agent": DEFAULT_USER_AGENT}
    if semantic_scholar_api_key:
        headers["x-api-key"] = semantic_scholar_api_key

    for source, response_type, url, params, parser in _source_plan(
        doi=doi,
        arxiv_id=arxiv_id,
        openalex_id=openalex_id,
        pmid=pmid,
        pmcid=pmcid,
        semantic_scholar_id=semantic_scholar_id,
        mailto=mailto,
    ):
        try:
            if response_type == "json":
                payload = fetch_json_fn(url, params=params, headers=headers, timeout=timeout)
            else:
                request_url = f"{url}?{urllib.parse.urlencode(params)}" if params else url
                payload = fetch_text_fn(request_url, headers=headers, timeout=timeout)
            parsed = parser(payload)
            for key in ("title", "doi", "arxiv_id", "openalex_id", "pmid", "pmcid", "semantic_scholar_id"):
                value = parsed.get(key)
                if value and not result.get(key):
                    result[key] = value
            if parsed.get("title") and not result["title"]:
                result["title"] = parsed["title"]
            if parsed.get("abstract"):
                result["abstract"] = parsed["abstract"]
                result["abstract_source"] = source
                result["source_attempts"].append({"source": source, "status": "verified"})
                break
            result["source_attempts"].append({"source": source, "status": "empty"})
        except (OSError, ValueError, ET.ParseError, urllib.error.URLError) as exc:
            result["source_attempts"].append(
                {"source": source, "status": "error", "error": str(exc)}
            )

    result["abstract_status"] = "verified" if is_verified_record(result) else "missing"
    return result


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Resolve a public title and abstract")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--doi")
    group.add_argument("--arxiv-id")
    group.add_argument("--openalex-id")
    group.add_argument("--pmid")
    group.add_argument("--pmcid")
    group.add_argument("--semantic-scholar-id")
    parser.add_argument("--mailto", default="")
    parser.add_argument("--semantic-scholar-api-key", default="")
    parser.add_argument("--timeout", type=int, default=30)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    result = resolve_record(
        doi=args.doi or "",
        arxiv_id=args.arxiv_id or "",
        openalex_id=args.openalex_id or "",
        pmid=args.pmid or "",
        pmcid=args.pmcid or "",
        semantic_scholar_id=args.semantic_scholar_id or "",
        mailto=args.mailto or os.environ.get("OPENALEX_MAILTO") or os.environ.get("CROSSREF_MAILTO", ""),
        semantic_scholar_api_key=args.semantic_scholar_api_key
        or os.environ.get("SEMANTIC_SCHOLAR_API_KEY", ""),
        timeout=args.timeout,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["abstract_status"] == "verified" else 2


if __name__ == "__main__":
    sys.exit(main())

