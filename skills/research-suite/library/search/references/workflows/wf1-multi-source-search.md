# Workflow 1: Multi-Source Literature Search

**Purpose:** Search multiple academic databases in parallel, deduplicate, merge, and rank results.

**Prerequisites:** MCP tools available (PubMed, CrossRef, arXiv, and optionally Semantic Scholar / Google Scholar).

**Uses:** [Dedup Engine](../dedup-engine.md) — deduplication and merge preference logic.

## Procedure

1. **Analyze topic** — identify domain, consult [source routing](../search-strategy.md#source-selection).
2. **Select sources by tier** — follow [Source Tiers](../source-tiers.md). Always try T1 first; escalate to T2 only if T1 insufficient; use T3 as last resort with explicit user warning.
3. **Search in parallel** — call all relevant MCP search tools simultaneously:
   - Biomedical → `pubmed_search_articles`
   - Cross-disciplinary → `search_crossref`
   - Preprints → `search_arxiv` / `search_biorxiv` / `search_medrxiv`
   - Exhaustive → add `search_semantic_scholar` / `search_webofscience` / `search_scopus`
4. **Deduplicate** — apply [Dedup Engine](../dedup-engine.md) to the merged result list, preserving every usable identifier (`doi`, `arxiv_id`, `openalex_id`, `pmid`, `pmcid`, and `paper_id`).
5. **Enrich every candidate before ranking** — resolve the public title and complete abstract by the strongest available identifier. Prefer the MCP source's returned abstract when it is non-empty; otherwise use `scripts/abstract_lookup.py`, which tries arXiv, OpenAlex, Crossref, Semantic Scholar, Europe PMC, and PubMed in identifier-aware fallback order. For OpenAlex, reconstruct `abstract_inverted_index` by position; for Crossref, strip JATS/XML while preserving the text. Record `abstract_source` and `source_attempts` for auditability.
6. **Apply the admission gate** — a candidate is eligible for scoring, delivery, notes, or an index entry only when `title` and `abstract` are both normalized and non-empty and `abstract_status` is `verified`. Never invent, paraphrase, or fill a missing abstract. Keep failed lookups in the run diagnostics with the attempted sources and failure reason, but exclude them from the final result set.
7. **Merge and rank verified records** — sort only the admitted records by relevance, date, or citation count per user preference. See [Result Ranking](../search-strategy.md#result-ranking). If the requested count cannot be met after enrichment, report the shortfall and the sources that failed instead of admitting title-only records.
8. **Present results** — use the complete public abstract or a clearly labeled excerpt for display, while retaining the complete abstract in structured output.

## Output Format

```
**Title**: [Paper Title]
**Authors**: [Author list]
**Journal**: [Journal name]
**Year**: [Year]  |  **DOI**: [DOI]  |  **PMID**: [PMID]
**Citations**: [count if available]
**Abstract**: [Complete retrieved abstract; an excerpt may be shown only when the complete value is retained in structured output]
**Abstract source**: [arXiv | OpenAlex | Crossref | Semantic Scholar | Europe PMC | PubMed]
**Abstract status**: `verified`
```

## Error Modes

- **MCP tool unavailable:** report specific failure, continue with remaining tools.
- **Candidate has no public abstract:** record the identifier-level attempts and exclude the candidate from scoring, delivery, notes, and index updates.
- **Title or abstract is incomplete:** do not infer or summarize the missing field; continue to the next source or candidate.
- **No results:** broaden terms per [Query Construction](../search-strategy.md#query-construction), try alternative sources, suggest user refine query.
- **All sources empty:** suggest MeSH strategy (Workflow 3) or manual query refinement.
