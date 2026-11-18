# Knowledge Agent Tool Contract

## Source MCP: `zotero_kb`

The source MCP is read-only and exposes exactly five tools:

| Tool | Input | Output purpose |
| --- | --- | --- |
| `kb_status` | none | Paper count, source directory, last sync |
| `kb_list` | optional metadata query and limit | Candidate paper metadata |
| `kb_search` | query and limit | Matching snippets with lines and files |
| `kb_read` | paper selector | Full Markdown and frontmatter |
| `kb_figures` | paper selector | Figure labels, captions, and asset paths |

## Writer MCP: `kb_writer`

The writer is not available to the read-only research agent. It exposes:

- `write_markdown(project_root, content, relative_path?, kind?, title?, overwrite?)`
- `append_markdown(project_root, relative_path, content)`
- `create_index(project_root, title, entries, relative_path?, overwrite?)`

All resolved targets must be below `<project_root>/文本/`. The writer rejects absolute targets outside that directory, traversal, `01-library`, Zotero storage, missing frontmatter for new Markdown, and default overwrites.

## Evidence package

```json
{
  "query": "user question",
  "evidence_status": "kb-grounded",
  "sources": [
    {
      "title": "Paper title",
      "zotero_key": "ABC123",
      "file": "01-library/.../paper.md",
      "location": "line 120 or heading",
      "quote": "Short exact excerpt",
      "supports": "Claim supported by the excerpt"
    }
  ],
  "gaps": []
}
```
