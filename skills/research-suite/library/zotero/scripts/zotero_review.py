#!/usr/bin/env python3
"""Search Zotero metadata and read Markdown from linked ZIP attachments."""

from __future__ import annotations

import argparse
import difflib
import html
import json
import os
import re
import sys
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any


BASE_URL = os.environ.get("ZOTERO_LOCAL_BASE_URL", "http://127.0.0.1:23119").rstrip("/")
LOCAL_USER = "/api/users/0"
API_PAGE_LIMIT = 100
MAX_MARKDOWN_BYTES = 20 * 1024 * 1024
MAX_OUTPUT_CHARS = 12_000
MAX_HEADING_TITLE_CHARS = 160
MAX_HEADINGS_PER_PAGE = 100
MAX_SEARCH_RESULTS_PER_PAGE = 100
MAX_CANDIDATES_PER_PAGE = 100
NON_LITERATURE_TYPES = {"attachment", "note", "annotation"}
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


class ZoteroError(Exception):
    pass


def http_get(path: str) -> tuple[bytes, dict[str, str]]:
    request = urllib.request.Request(
        BASE_URL + path,
        headers={
            "Accept": "application/json",
            "Zotero-API-Version": "3",
        },
        method="GET",
    )
    try:
        with OPENER.open(request, timeout=20) as response:
            return response.read(), dict(response.headers.items())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise ZoteroError(f"Zotero API returned HTTP {exc.code}: {detail[:500]}") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise ZoteroError(
            f"Cannot reach Zotero at {BASE_URL}. Check that Zotero is running and its local API is enabled. {exc}"
        ) from exc


def api_json(path: str) -> tuple[Any, dict[str, str]]:
    body, headers = http_get(path)
    try:
        return json.loads(body.decode("utf-8")), headers
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ZoteroError(f"Zotero returned invalid JSON for {path}") from exc


def normalized_headers(headers: dict[str, str]) -> dict[str, str]:
    return {key.lower(): value for key, value in headers.items()}


def collect_pages(fetch_page, page_size: int = API_PAGE_LIMIT) -> tuple[list[Any], int | None]:
    if page_size < 1:
        raise ValueError("page_size must be positive")

    rows: list[Any] = []
    total: int | None = None
    start = 0
    while True:
        page, headers = fetch_page(start, page_size)
        if not isinstance(page, list):
            raise ZoteroError("Zotero returned an unexpected paginated response.")
        rows.extend(page)

        raw_total = normalized_headers(headers).get("total-results")
        if raw_total and raw_total.isdigit():
            total = int(raw_total)

        start += len(page)
        if not page or (total is not None and start >= total) or len(page) < page_size:
            break
    return rows, total


def item_data(item: dict[str, Any]) -> dict[str, Any]:
    data = item.get("data", item)
    return data if isinstance(data, dict) else {}


def creators_for_item(data: dict[str, Any]) -> list[str]:
    creators: list[str] = []
    for creator in data.get("creators") or []:
        if creator.get("name"):
            creators.append(str(creator["name"]))
            continue
        name = " ".join(
            part for part in (creator.get("firstName"), creator.get("lastName")) if part
        )
        if name:
            creators.append(name)
    return creators


def summarize_item(item: dict[str, Any]) -> dict[str, Any]:
    data = item_data(item)
    match = re.search(r"\d{4}", str(data.get("date") or ""))
    return {
        "key": item.get("key") or data.get("key"),
        "itemType": data.get("itemType"),
        "title": data.get("title"),
        "creators": creators_for_item(data),
        "year": match.group(0) if match else None,
        "DOI": data.get("DOI") or None,
        "abstractNote": data.get("abstractNote") or "",
    }


def normalize_title(value: str) -> str:
    text = html.unescape(value)
    text = re.sub(r"\\[A-Za-z]+", "", text)
    text = re.sub(r"[$*_~{}^]", "", text).replace(chr(96), "")
    text = unicodedata.normalize("NFKD", text.casefold())
    return "".join(char for char in text if char.isalnum() and not unicodedata.combining(char))


def markdown_title(markdown: str) -> str | None:
    for line in markdown.splitlines()[:80]:
        match = re.match(r"^\s{0,3}#\s+(.+?)\s*#*\s*$", line)
        if match:
            return match.group(1).strip()
    return None


def markdown_dois(markdown: str) -> set[str]:
    metadata_headings = {
        "articleinfo",
        "articleinformation",
        "bibliographicinformation",
        "citation",
        "citationinformation",
        "documentmetadata",
        "metadata",
        "publicationinformation",
    }
    metadata_lines: list[str] = []
    in_metadata_section = False
    saw_heading = False
    for line in markdown.splitlines()[:80]:
        heading = re.match(r"^\s{0,3}(#{1,6})\s+(.+?)\s*#*\s*$", line)
        if heading:
            normalized_heading = normalize_title(heading.group(2))
            if len(heading.group(1)) >= 2 and normalized_heading in metadata_headings:
                in_metadata_section = True
                saw_heading = True
                continue
            if saw_heading:
                break
            saw_heading = True
            continue
        if in_metadata_section or re.match(
            r"^\s*(?:[-*]\s*)?(?:doi|digital object identifier)\s*[:=]",
            line,
            re.IGNORECASE,
        ):
            metadata_lines.append(line)

    matches = re.findall(
        r"(?i)\b10\.\d{4,9}/[^\s<>\"']+", "\n".join(metadata_lines)
    )
    dois = set()
    for value in matches:
        value = re.sub(r"(?i)^https?://(?:dx\.)?doi\.org/", "", value)
        dois.add(value.rstrip(".,;:!?)]}").casefold())
    return dois


def check_document_identity(
    expected_title: str | None, expected_doi: str | None, markdown: str
) -> dict[str, Any]:
    document_title = markdown_title(markdown)
    expected_normalized = normalize_title(expected_title or "")
    document_normalized = normalize_title(document_title or "")
    similarity = (
        difflib.SequenceMatcher(None, expected_normalized, document_normalized).ratio()
        if expected_normalized and document_normalized
        else None
    )

    expected_doi = str(expected_doi or "").strip()
    document_dois = markdown_dois(markdown)
    if expected_doi:
        expected_doi = re.sub(r"(?i)^https?://(?:dx\.)?doi\.org/", "", expected_doi)
        expected_doi = expected_doi.rstrip(".,;:!?)]}").casefold()
        doi_match: bool | None = expected_doi in document_dois
    else:
        doi_match = None

    doi_conflict = bool(expected_doi and document_dois and expected_doi not in document_dois)
    if (similarity is not None and similarity < 0.75) or doi_conflict:
        status = "mismatch"
    elif doi_match or (similarity is not None and similarity >= 0.90):
        status = "matched"
    elif document_title or document_dois:
        status = "uncertain"
    else:
        status = "unverified"

    return {
        "status": status,
        "markdownTitle": document_title,
        "titleSimilarity": round(similarity, 3) if similarity is not None else None,
        "doiMatch": doi_match,
    }


def markdown_headings(markdown: str) -> list[dict[str, Any]]:
    headings = []
    for line_number, line in enumerate(markdown.splitlines(), start=1):
        match = re.match(r"^\s{0,3}(#{1,6})\s+(.+?)\s*#*\s*$", line)
        if match:
            headings.append(
                {"line": line_number, "level": len(match.group(1)), "title": match.group(2)}
            )
    return headings


def page_markdown(
    markdown: str,
    start_line: int,
    max_lines: int,
    start_column: int = 1,
    max_chars: int = MAX_OUTPUT_CHARS,
) -> dict[str, Any]:
    if start_line < 1:
        raise ZoteroError("start-line must be at least 1.")
    if max_lines < 1:
        raise ZoteroError("max-lines must be at least 1.")
    if start_column < 1:
        raise ZoteroError("start-column must be at least 1.")
    if max_chars < 1:
        raise ZoteroError("max output characters must be at least 1.")

    max_chars = min(max_chars, MAX_OUTPUT_CHARS)
    lines = markdown.splitlines()
    total_lines = len(lines)
    start_index = start_line - 1
    if start_index > total_lines:
        raise ZoteroError(f"start-line {start_line} is beyond the document's {total_lines} lines.")
    if start_index < total_lines and start_column > len(lines[start_index]) + 1:
        raise ZoteroError(
            f"start-column {start_column} is beyond line {start_line}'s {len(lines[start_index])} characters."
        )

    line_limit = min(total_lines, start_index + max_lines)
    line_index = start_index
    column_index = start_column - 1
    last_line: int | None = None
    next_start_line: int | None = None
    next_start_column: int | None = None
    chunks: list[str] = []
    used_chars = 0

    while line_index < line_limit:
        separator = "\n" if last_line is not None else ""
        available = max_chars - used_chars - len(separator)
        if available <= 0:
            next_start_line = line_index + 1
            next_start_column = column_index + 1
            break

        remaining = lines[line_index][column_index:]
        if len(remaining) > available:
            chunk = remaining[:available]
            chunks.append(separator + chunk)
            used_chars += len(separator) + len(chunk)
            last_line = line_index + 1
            next_start_line = line_index + 1
            next_start_column = column_index + len(chunk) + 1
            break

        chunks.append(separator + remaining)
        used_chars += len(separator) + len(remaining)
        last_line = line_index + 1
        line_index += 1
        column_index = 0

    if next_start_line is None and line_index < total_lines:
        next_start_line = line_index + 1
        next_start_column = 1

    text = "".join(chunks)
    if next_start_line is None and markdown.endswith("\n") and text and len(text) < max_chars:
        text += "\n"

    return {
        "startLine": start_line if start_index < total_lines else total_lines + 1,
        "endLine": last_line or min(start_index + 1, total_lines),
        "totalLines": total_lines,
        "hasMore": next_start_line is not None,
        "nextStartLine": next_start_line,
        "nextStartColumn": next_start_column,
        "text": text,
    }


def page_headings(
    headings: list[dict[str, Any]],
    start_heading: int,
    max_chars: int = MAX_OUTPUT_CHARS,
) -> dict[str, Any]:
    if start_heading < 1:
        raise ZoteroError("heading-start must be at least 1.")
    if max_chars < 1:
        raise ZoteroError("max output characters must be at least 1.")

    max_chars = min(max_chars, MAX_OUTPUT_CHARS)
    if start_heading > len(headings) + 1:
        raise ZoteroError(
            f"heading-start {start_heading} is beyond the {len(headings)} document headings."
        )

    lines: list[str] = []
    used_chars = 0
    index = start_heading - 1
    while index < len(headings) and len(lines) < MAX_HEADINGS_PER_PAGE:
        heading = headings[index]
        title = str(heading["title"])
        clipped = len(title) > MAX_HEADING_TITLE_CHARS
        if clipped:
            title = title[: MAX_HEADING_TITLE_CHARS - 3] + "..."
        rendered = f"{heading['line']:>5} {'#' * heading['level']} {title}"
        if clipped:
            rendered += f" [title clipped; read --start-line {heading['line']} ]"

        separator = "\n" if lines else ""
        if used_chars + len(separator) + len(rendered) > max_chars:
            break
        lines.append(rendered)
        used_chars += len(separator) + len(rendered)
        index += 1

    return {
        "startHeading": start_heading,
        "endHeading": index,
        "totalHeadings": len(headings),
        "hasMore": index < len(headings),
        "nextHeading": index + 1 if index < len(headings) else None,
        "text": "\n".join(lines),
    }


def page_candidates(
    candidates: list[dict[str, Any]],
    start_candidate: int,
    max_chars: int = MAX_OUTPUT_CHARS - 512,
) -> dict[str, Any]:
    if start_candidate < 1:
        raise ZoteroError("candidate-start must be at least 1.")
    if max_chars < 1:
        raise ZoteroError("max output characters must be at least 1.")
    if start_candidate > len(candidates) + 1:
        raise ZoteroError(
            f"candidate-start {start_candidate} is beyond the {len(candidates)} candidates."
        )

    max_chars = min(max_chars, MAX_OUTPUT_CHARS - 512)
    lines: list[str] = []
    used_chars = 0
    index = start_candidate - 1
    while index < len(candidates) and len(lines) < MAX_CANDIDATES_PER_PAGE:
        candidate = candidates[index]
        attachment_key = str(candidate["attachmentKey"])
        entry = str(candidate["entry"])
        if len(attachment_key) > 120:
            attachment_key = attachment_key[:117] + "..."
        if len(entry) > 360:
            entry = entry[:357] + "..."
        rendered = f"{index + 1:>5} {attachment_key}:{entry}"
        separator = "\n" if lines else ""
        if used_chars + len(separator) + len(rendered) > max_chars:
            break
        lines.append(rendered)
        used_chars += len(separator) + len(rendered)
        index += 1

    return {
        "startCandidate": start_candidate,
        "endCandidate": index,
        "totalCandidates": len(candidates),
        "hasMore": index < len(candidates),
        "nextCandidate": index + 1 if index < len(candidates) else None,
        "text": "\n".join(lines),
    }


def format_attachment_failures(
    failures: list[str], max_chars: int = MAX_OUTPUT_CHARS - 512
) -> str:
    if max_chars < 1:
        raise ZoteroError("max output characters must be at least 1.")
    max_chars = min(max_chars, MAX_OUTPUT_CHARS - 512)
    content_limit = max(0, max_chars - 80)
    lines: list[str] = []
    used_chars = 0

    for index, failure in enumerate(failures):
        rendered = str(failure)
        if len(rendered) > 360:
            rendered = rendered[:357] + "..."
        separator = "\n" if lines else ""
        if used_chars + len(separator) + len(rendered) > content_limit:
            omitted = len(failures) - index
            marker = f"... {omitted} additional attachment errors omitted."
            if lines:
                lines.append(marker)
            else:
                return marker[:max_chars]
            break
        lines.append(rendered)
        used_chars += len(separator) + len(rendered)

    return "\n".join(lines) or "No attachment errors were reported."


def candidate_selection_error(
    reason: str, candidates: list[dict[str, Any]], candidate_start: int
) -> ZoteroError:
    page = page_candidates(candidates, candidate_start)
    detail = (
        f"Candidates {page['startCandidate']}-{page['endCandidate']} "
        f"of {page['totalCandidates']}:\n{page['text']}"
    )
    if page["hasMore"]:
        detail += f"\nContinue with --candidate-start {page['nextCandidate']}."
    return ZoteroError(f"{reason} Choose with --candidate-number N or --attachment-key KEY --entry PATH.\n{detail}")


def select_candidate(
    candidates: list[dict[str, Any]],
    attachment_key: str | None = None,
    entry_name: str | None = None,
    candidate_number: int | None = None,
    candidate_start: int = 1,
) -> dict[str, Any]:
    if not candidates:
        raise ZoteroError("No Markdown candidates are available.")
    if candidate_number is not None:
        if attachment_key or entry_name:
            raise ZoteroError(
                "Use --candidate-number or the --attachment-key/--entry pair, not both."
            )
        if candidate_number < 1 or candidate_number > len(candidates):
            raise candidate_selection_error(
                f"Candidate number {candidate_number} is out of range.",
                candidates,
                candidate_start,
            )
        return candidates[candidate_number - 1]
    if bool(attachment_key) != bool(entry_name):
        raise ZoteroError("Specify both --attachment-key and --entry to choose a Markdown file.")

    if attachment_key and entry_name:
        matches = [
            candidate
            for candidate in candidates
            if candidate["attachmentKey"].casefold() == attachment_key.casefold()
            and candidate["entry"].casefold() == entry_name.casefold()
        ]
        if len(matches) != 1:
            raise candidate_selection_error(
                "That ZIP/Markdown selection was not unique or not found.",
                candidates,
                candidate_start,
            )
        return matches[0]

    best_rank = max(candidate["rank"] for candidate in candidates)
    best = [candidate for candidate in candidates if candidate["rank"] == best_rank]
    if best_rank == 0 or len(best) != 1:
        raise candidate_selection_error(
            "Multiple Markdown candidates are linked to this item.",
            candidates,
            candidate_start,
        )
    return best[0]


def search_items(
    query_text: str, max_results: int, start_result: int = 1
) -> dict[str, Any]:
    if max_results < 1 or max_results > MAX_SEARCH_RESULTS_PER_PAGE:
        raise ZoteroError(
            f"max-results must be between 1 and {MAX_SEARCH_RESULTS_PER_PAGE}."
        )
    if start_result < 1:
        raise ZoteroError("start-result must be at least 1.")

    items: list[dict[str, Any]] = []
    total: int | None = None
    start = 0
    skipped = 0

    while True:
        params = urllib.parse.urlencode(
            {
                "q": query_text,
                "include": "data",
                "limit": API_PAGE_LIMIT,
                "start": start,
            }
        )
        page, headers = api_json(f"{LOCAL_USER}/items/top?{params}")
        if not isinstance(page, list):
            raise ZoteroError("Zotero search returned an unexpected response.")

        raw_total = normalized_headers(headers).get("total-results")
        if raw_total and raw_total.isdigit():
            total = int(raw_total)

        for item in page:
            if (
                not isinstance(item, dict)
                or item_data(item).get("itemType") in NON_LITERATURE_TYPES
            ):
                continue
            if skipped < start_result - 1:
                skipped += 1
                continue
            items.append(item)
            if len(items) > max_results:
                break
        start += len(page)

        if len(items) > max_results:
            break
        if (
            not page
            or (total is not None and start >= total)
            or len(page) < API_PAGE_LIMIT
        ):
            break

    returned_items = items[:max_results]
    truncated = len(items) > max_results
    return {
        "query": query_text,
        "totalSearchHits": total,
        "startResult": start_result,
        "returned": len(returned_items),
        "truncated": truncated,
        "nextResult": start_result + len(returned_items) if truncated else None,
        "items": [summarize_item(item) for item in returned_items],
    }


def bounded_search_result(
    result: dict[str, Any],
    abstract_start: int = 0,
    max_chars: int = MAX_OUTPUT_CHARS - 1,
) -> dict[str, Any]:
    if abstract_start < 0:
        raise ZoteroError("abstract-start must be at least 0.")
    if max_chars < 1:
        raise ZoteroError("max output characters must be at least 1.")
    max_chars = min(max_chars, MAX_OUTPUT_CHARS - 1)

    start_result = int(result.get("startResult") or 1)
    source_items = result.get("items") or []
    source_has_more = bool(result.get("truncated"))
    source_next_result = result.get("nextResult")

    def make_page(
        items: list[dict[str, Any]],
        has_more: bool,
        next_result: int | None,
        next_abstract_start: int | None = None,
        next_abstract_key: str | None = None,
    ) -> dict[str, Any]:
        page = {
            "query": result.get("query", ""),
            "totalSearchHits": result.get("totalSearchHits"),
            "startResult": start_result,
            "returned": len(items),
            "truncated": has_more,
            "items": items,
        }
        if has_more:
            page["nextResult"] = next_result
        if next_abstract_start is not None:
            page["nextAbstractStart"] = next_abstract_start
            page["nextAbstractKey"] = next_abstract_key
        return page

    def render(page: dict[str, Any]) -> str:
        return json.dumps(page, ensure_ascii=False, indent=2)

    output_items: list[dict[str, Any]] = []
    for item_index, source_item in enumerate(source_items):
        item = dict(source_item)
        abstract = str(item.get("abstractNote") or "")
        offset = abstract_start if item_index == 0 else 0
        if offset > len(abstract):
            raise ZoteroError(
                f"abstract-start {offset} is beyond the first result's {len(abstract)} characters."
            )
        item["abstractNote"] = abstract[offset:]
        if offset:
            item["abstractStart"] = offset

        proposed_items = output_items + [item]
        proposed_page = make_page(
            proposed_items,
            source_has_more,
            source_next_result,
        )
        if len(render(proposed_page)) <= max_chars:
            output_items.append(item)
            continue

        if output_items:
            next_result = start_result + len(output_items)
            return make_page(output_items, True, next_result)

        low = 0
        high = len(item["abstractNote"])
        best_page: dict[str, Any] | None = None
        while low <= high:
            shown_chars = (low + high) // 2
            partial_item = dict(item)
            partial_item["abstractNote"] = abstract[offset : offset + shown_chars]
            next_abstract_start = offset + shown_chars
            abstract_is_truncated = next_abstract_start < len(abstract)
            if abstract_is_truncated:
                partial_item["abstractTruncated"] = True
            partial_page = make_page(
                [partial_item],
                True,
                start_result,
                next_abstract_start if abstract_is_truncated else None,
                str(item.get("key") or "") if abstract_is_truncated else None,
            )
            if len(render(partial_page)) <= max_chars:
                best_page = partial_page
                low = shown_chars + 1
            else:
                high = shown_chars - 1

        if best_page is None:
            raise ZoteroError(
                "A Zotero result's metadata exceeds the output limit even without its abstract."
            )
        if best_page.get("nextAbstractStart") == offset:
            raise ZoteroError(
                "Search metadata leaves no room for abstract text. Retry with a shorter query."
            )
        return best_page

    return make_page(output_items, source_has_more, source_next_result)


def attachment_filename(data: dict[str, Any]) -> str:
    return str(data.get("filename") or data.get("title") or data.get("key") or "attachment")


def is_zip_attachment(data: dict[str, Any]) -> bool:
    filename = attachment_filename(data).casefold()
    content_type = str(data.get("contentType") or "").casefold()
    title = str(data.get("title") or "").casefold()
    return (
        content_type in {"application/zip", "application/x-zip-compressed"}
        or filename.endswith(".zip")
        or title.endswith(".zip")
    )


def local_file_path(file_url: str) -> Path:
    parsed = urllib.parse.urlsplit(file_url.strip().strip('"'))
    if parsed.scheme.casefold() != "file":
        raise ZoteroError(f"Zotero returned a non-local attachment URL: {file_url}")

    path = urllib.parse.unquote(parsed.path)
    if os.name == "nt":
        if parsed.netloc:
            path = "\\\\" + parsed.netloc + path.replace("/", "\\")
        else:
            if re.match(r"^/[A-Za-z]:/", path):
                path = path[1:]
            path = path.replace("/", "\\")
    return Path(path)


def attachment_file_path(attachment_key: str) -> Path:
    encoded_key = urllib.parse.quote(attachment_key, safe="")
    body, _ = http_get(
        f"{LOCAL_USER}/items/{encoded_key}/file/view/url"
    )
    file_url = body.decode("utf-8", errors="replace").strip()
    if file_url.startswith('"') and file_url.endswith('"'):
        try:
            file_url = json.loads(file_url)
        except json.JSONDecodeError:
            file_url = file_url[1:-1]
    path = local_file_path(file_url)
    if not path.is_file():
        raise ZoteroError(f"Linked ZIP file is not available at {path}")
    return path


def normalized_name(value: str) -> str:
    return re.sub(r"[\W_]+", "", value.casefold())


def read_linked_markdown(
    item_key: str,
    attachment_key: str | None = None,
    entry_name: str | None = None,
    candidate_number: int | None = None,
    candidate_start: int = 1,
) -> tuple[dict[str, Any], dict[str, Any], str]:
    if bool(attachment_key) != bool(entry_name):
        raise ZoteroError("Specify both --attachment-key and --entry to choose a Markdown file.")

    encoded_key = urllib.parse.quote(item_key, safe="")
    item, _ = api_json(f"{LOCAL_USER}/items/{encoded_key}")
    if not isinstance(item, dict):
        raise ZoteroError(f"Zotero item {item_key} was not found.")
    parent_data = item_data(item)
    if parent_data.get("itemType") == "attachment":
        raise ZoteroError("Pass the parent literature item key, not an attachment key.")

    def fetch_child_page(start: int, limit: int) -> tuple[Any, dict[str, str]]:
        params = urllib.parse.urlencode({"start": start, "limit": limit})
        return api_json(f"{LOCAL_USER}/items/{encoded_key}/children?{params}")

    children, _ = collect_pages(fetch_child_page)

    zip_attachments = [
        child
        for child in children
        if isinstance(child, dict)
        and item_data(child).get("itemType") == "attachment"
        and is_zip_attachment(item_data(child))
    ]
    if attachment_key:
        zip_attachments = [
            child
            for child in zip_attachments
            if str(child.get("key") or item_data(child).get("key") or "").casefold()
            == attachment_key.casefold()
        ]
    if not zip_attachments:
        suffix = f" with attachment key {attachment_key}" if attachment_key else ""
        raise ZoteroError(
            f"No linked ZIP attachment was found for Zotero item {item_key}{suffix}."
        )

    title_name = normalized_name(str(parent_data.get("title") or ""))
    candidates: list[dict[str, Any]] = []
    failures: list[str] = []

    for attachment in zip_attachments:
        data = item_data(attachment)
        current_attachment_key = str(attachment.get("key") or data.get("key") or "")
        display_name = attachment_filename(data)
        if not current_attachment_key:
            failures.append(f"{display_name}: missing attachment key")
            continue
        try:
            zip_path = attachment_file_path(current_attachment_key)
            with zipfile.ZipFile(zip_path) as archive:
                markdown_entries = [
                    entry
                    for entry in archive.infolist()
                    if not entry.is_dir() and entry.filename.casefold().endswith(".md")
                ]
                for entry in markdown_entries:
                    basename = PurePosixPath(entry.filename).name.casefold()
                    stem = normalized_name(PurePosixPath(entry.filename).stem)
                    if basename == "full.md":
                        rank = 3
                    elif title_name and stem == title_name:
                        rank = 2
                    elif len(markdown_entries) == 1:
                        rank = 1
                    else:
                        rank = 0
                    candidates.append(
                        {
                            "rank": rank,
                            "attachmentKey": current_attachment_key,
                            "attachment": display_name,
                            "entry": entry.filename,
                            "zipPath": zip_path,
                            "fileSize": entry.file_size,
                        }
                    )
                if not markdown_entries:
                    failures.append(f"{display_name}: no Markdown entry")
        except (OSError, zipfile.BadZipFile, RuntimeError, ZoteroError) as exc:
            failures.append(f"{display_name}: {exc}")

    if not candidates:
        detail = (
            format_attachment_failures(failures)
            if failures
            else "no Markdown entry was found"
        )
        raise ZoteroError(f"No readable Markdown was found for Zotero item {item_key}: {detail}")

    selected = select_candidate(
        candidates,
        attachment_key,
        entry_name,
        candidate_number=candidate_number,
        candidate_start=candidate_start,
    )
    if selected["fileSize"] > MAX_MARKDOWN_BYTES:
        raise ZoteroError(
            f"Markdown entry {display_field(selected['entry'], max_chars=240)} is larger than "
            f"{MAX_MARKDOWN_BYTES // (1024 * 1024)} MiB."
        )

    try:
        with zipfile.ZipFile(selected["zipPath"]) as archive:
            raw = archive.read(selected["entry"])
    except (OSError, zipfile.BadZipFile, RuntimeError) as exc:
        raise ZoteroError(
            "Could not read "
            f"{display_field(selected['entry'], max_chars=240)} from its ZIP: "
            f"{display_field(exc, max_chars=500)}"
        ) from exc

    try:
        markdown = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ZoteroError(
            f"Markdown entry {display_field(selected['entry'], max_chars=240)} "
            "is not valid UTF-8; refusing to silently alter text."
        ) from exc
    selected["identity"] = check_document_identity(
        str(parent_data.get("title") or ""),
        str(parent_data.get("DOI") or ""),
        markdown,
    )
    return item, selected, markdown


def command_search(args: argparse.Namespace) -> None:
    result = search_items(args.query, args.max_results, start_result=args.start_result)
    page = bounded_search_result(result, abstract_start=args.abstract_start)
    print(json.dumps(page, ensure_ascii=False, indent=2))


def display_field(value: Any, max_chars: int = 240) -> str:
    text = str(value or "")
    return text if len(text) <= max_chars else text[: max_chars - 3] + "..."


def command_markdown(args: argparse.Namespace) -> None:
    item, source, markdown = read_linked_markdown(
        args.item_key,
        attachment_key=args.attachment_key,
        entry_name=args.entry,
        candidate_number=args.candidate_number,
        candidate_start=args.candidate_start,
    )
    data = item_data(item)
    identity = source["identity"]
    header = [
        f"Zotero item: {display_field(item.get('key') or args.item_key)}",
        f"Title: {display_field(data.get('title'))}",
        f"DOI: {display_field(data.get('DOI'))}",
        "ZIP attachment: "
        f"{display_field(source['attachmentKey'])} | {display_field(source['attachment'])}",
        f"Markdown entry: {display_field(source['entry'])}",
        f"Identity check: {identity['status']}",
    ]
    if identity["markdownTitle"]:
        header.append(f"Markdown title: {display_field(identity['markdownTitle'])}")
    if identity["titleSimilarity"] is not None:
        header.append(f"Title similarity: {identity['titleSimilarity']:.3f}")
    if identity["doiMatch"] is not None:
        header.append(
            "Expected DOI in document metadata: "
            f"{'yes' if identity['doiMatch'] else 'no'}"
        )
    if identity["status"] == "mismatch":
        header.append("WARNING: Do not use this Markdown as evidence until its source is resolved.")
    header_text = "\n".join(header) + "\n\n"
    body_budget = max(1, MAX_OUTPUT_CHARS - len(header_text) - 384)

    if args.headings:
        page = page_headings(
            markdown_headings(markdown),
            start_heading=args.heading_start,
            max_chars=body_budget,
        )
        body = (
            f"Markdown headings {page['startHeading']}-{page['endHeading']} "
            f"of {page['totalHeadings']}.\n"
        )
        if page["text"]:
            body += "\n" + page["text"] + "\n"
        elif not page["totalHeadings"]:
            body += "No Markdown headings were found.\n"
        if page["hasMore"]:
            body += f"Continue with --heading-start {page['nextHeading']}.\n"
    else:
        page = page_markdown(
            markdown,
            args.start_line,
            args.max_lines,
            start_column=args.start_column,
            max_chars=body_budget,
        )
        body = (
            f"Markdown lines {page['startLine']}-{page['endLine']} "
            f"of {page['totalLines']}.\n"
        )
        if page["hasMore"]:
            body += (
                f"Continue with --start-line {page['nextStartLine']} "
                f"--start-column {page['nextStartColumn']}.\n"
            )
        if page["text"]:
            body += "\n" + page["text"] + "\n"

    sys.stdout.write(header_text + body)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Search Zotero metadata and inspect Markdown in linked ZIP attachments."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    search_parser = subparsers.add_parser(
        "search", help="Search top-level items by title, abstract, and other Zotero fields."
    )
    search_parser.add_argument("query", help="Topic, phrase, or search term.")
    search_parser.add_argument("--max-results", type=int, default=40)
    search_parser.add_argument("--start-result", type=int, default=1)
    search_parser.add_argument("--abstract-start", type=int, default=0)
    search_parser.set_defaults(func=command_search)

    markdown_parser = subparsers.add_parser(
        "markdown", help="Read the selected Markdown from ZIP attachments linked to an item."
    )
    markdown_parser.add_argument("item_key", help="Zotero parent item key.")
    markdown_parser.add_argument("--attachment-key", help="Choose a linked ZIP attachment.")
    markdown_parser.add_argument("--entry", help="Choose the exact Markdown path inside the ZIP.")
    markdown_parser.add_argument(
        "--candidate-number",
        type=int,
        help="Choose an entry by its number in an ambiguity listing.",
    )
    markdown_parser.add_argument("--candidate-start", type=int, default=1)
    markdown_parser.add_argument("--headings", action="store_true", help="List Markdown headings and line numbers.")
    markdown_parser.add_argument("--start-line", type=int, default=1)
    markdown_parser.add_argument("--start-column", type=int, default=1)
    markdown_parser.add_argument("--heading-start", type=int, default=1)
    markdown_parser.add_argument("--max-lines", type=int, default=120)
    markdown_parser.set_defaults(func=command_markdown)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "search":
        if not 1 <= args.max_results <= MAX_SEARCH_RESULTS_PER_PAGE:
            parser.error(
                f"--max-results must be between 1 and {MAX_SEARCH_RESULTS_PER_PAGE}"
            )
        if args.start_result < 1:
            parser.error("--start-result must be at least 1")
        if args.abstract_start < 0:
            parser.error("--abstract-start must be at least 0")
    elif args.command == "markdown":
        if bool(args.attachment_key) != bool(args.entry):
            parser.error("--attachment-key and --entry must be specified together")
        if args.candidate_number is not None and args.candidate_number < 1:
            parser.error("--candidate-number must be at least 1")
        if args.candidate_start < 1:
            parser.error("--candidate-start must be at least 1")
        if args.candidate_number is not None and (args.attachment_key or args.entry):
            parser.error("--candidate-number cannot be combined with --attachment-key or --entry")
        if args.start_line < 1:
            parser.error("--start-line must be at least 1")
        if args.start_column < 1:
            parser.error("--start-column must be at least 1")
        if args.heading_start < 1:
            parser.error("--heading-start must be at least 1")
        if args.max_lines < 1:
            parser.error("--max-lines must be at least 1")
    try:
        args.func(args)
    except ZoteroError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
