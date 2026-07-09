# jupyter-surgical-edit 🏥🔧

**Surgically edit `.ipynb` notebook cell source — without touching outputs, execution counts, or metadata.**

Like a scalpel: you change only what you mean to change, and everything else stays intact.

---

## Why?

Ever needed to:
- Fix a bug in a notebook that already has valuable outputs / plots?
- Update a parameter without rerunning the whole notebook?
- Modify code in a colleague's notebook without losing their run history?

Most editors force you to either (a) reload and lose all outputs, or (b) manually edit the raw JSON and risk corrupting the structure.

`jupyter-surgical-edit` gives you a CLI tool that treats `.ipynb` as a structured document — you target cells by **stable tags**, change only `source`, and leave everything else alone.

---

## Quick Start

### Install

```bash
pip install nbformat
```

### Tag & List

```bash
python nb_edit.py notebook.ipynb tag all
python nb_edit.py notebook.ipynb list
```

Output (truncated):
```
   # type       exec   tag        description
----------------------------------------------------------------------
   0 code       1      cell-0     read data
   1 markdown   -      md-0       QC filtering
   ...
```

### Edit a Cell by Tag (Stable!)

```bash
python nb_edit.py notebook.ipynb set-source-by-tag cell-1 'print("hello world")'
```

### More Commands

| Command | Description |
|---------|-------------|
| `tag all` | Tag all code/md/raw cells (cell-N / md-N / raw-N) |
| `tag code` | Tag only code cells |
| `tag markdown` | Tag only markdown cells |
| `clear-tags` | Remove all tags |
| `list` | List all cells with index, type, tag, description |
| `find "<text>"` | Search cells by content |
| `set-source-by-tag <tag> "<code>"` | **Recommended** — edit by stable tag |
| `set-source <index> "<code>"` | Edit by index (fragile — shifts on insert/delete) |
| `set-source-by-type <type> <nth> "<code>"` | Edit by type + nth occurrence |
| `append "<code>"` | Append a new code cell at the end |
| `insert <index> "<code>"` | Insert a code cell at index |
| `delete <index>` | Delete a cell |

---

## What Changes / What Stays

| Field | Changed? |
|-------|----------|
| `source` (cell code / markdown) | **Yes** — the only thing modified |
| `outputs` (execution results) | **No** — preserved as-is |
| `execution_count` | **No** — kept (may be stale, next run refreshes it) |
| `cell.metadata` (tags, etc.) | **No** — preserved |
| `metadata.kernelspec` | **No** — preserved |
| `metadata.language_info` | **No** — preserved |
| All notebook-level metadata | **No** — preserved |

---

## Programmatic Use (Python API)

### A) Via nbformat (recommended)

```python
from nbformat import read, write, NO_CONVERT

nb = read("notebook.ipynb", NO_CONVERT)
for c in nb.cells:
    if "filter_cells" in c.source:
        c.source = c.source.replace("min_genes=200", "min_genes=500")
write(nb, "notebook.ipynb")
```

### B) Via raw json (no nbformat dependency)

```python
import json

with open("notebook.ipynb", encoding='utf-8') as f:
    nb = json.load(f)

# Find cell by tag and modify
for cell in nb['cells']:
    tags = cell.get('metadata', {}).get('tags', [])
    if 'cell-3' in tags:
        cell['source'] = ["pass\n", "# new code here\n"]

with open("notebook.ipynb", 'w', encoding='utf-8') as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)
```

**Key rules when using JSON mode:**
- `source` must be a **list of strings** (one per line), not a single string
- `execution_count` must be `None` (Python `None`, not string `"null"`)
- New cells need `outputs: []` and `execution_count: None`
- Use `json.dump(..., indent=1)` — the standard nbformat indentation

---

## Tag Persistence

Tags are stored in Jupyter's native `metadata.tags` field. They survive save/reload in VS Code, JupyterLab, and Jupyter Notebook. No external state file needed.

---

## VS Code Compatibility

VS Code's Jupyter extension reads `.ipynb` from disk. After editing with this tool, VS Code auto-detects the change when you switch tabs or focus the file. The kernel state is unaffected — only the file on disk changes.

---

## Common Pitfalls

1. **Always use `NO_CONVERT`** when loading with nbformat — without it, nbformat may silently upgrade your notebook version.
2. **Appended/inserted cells have no outputs** — that's expected, they start empty.
3. **`execution_count` goes stale after editing** — intentionally preserved; next run in Jupyter resets it.
4. **Run `tag all` after insert/delete** — tags shift; refresh them before the next edit.
5. **Markdown cells don't have `outputs`** — the script auto-pads them before saving.
6. **Don't use plain text editors on `.ipynb`** — use this tool to avoid corrupting the JSON structure.

---

## License

MIT
