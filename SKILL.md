---
name: jupyter-surgical-edit
description: "Surgically edit .ipynb notebook cell source code without touching outputs, execution_count, or metadata. Uses nbformat — no Jupyter kernel involved."
version: 1.0.0
author: condaThinker
license: MIT
metadata:
  hermes:
    tags: [jupyter, notebook, nbformat, edit, surgical, tag]
---

# jupyter-surgical-edit

Modify `.ipynb` notebook cell source code while **fully preserving** all outputs, execution counts, cell metadata, and notebook metadata.

Uses `nbformat` with `NO_CONVERT` mode — reads the notebook JSON, replaces only the `source` field of targeted cells, and writes back. No Jupyter kernel, no execution triggered.

## When to Use

- Fix a bug in a notebook that already has valuable plots/outputs
- Update a parameter without rerunning the whole notebook
- Batch-edit code across many notebooks programmatically
- Operate in a CI/CD pipeline that treats notebooks as structured documents

## Prerequisites

```bash
pip install nbformat
```

Run the script from the repo root:
```bash
python scripts/nb_edit.py notebook.ipynb tag all
python scripts/nb_edit.py notebook.ipynb list
python scripts/nb_edit.py notebook.ipynb set-source-by-tag cell-1 'print("hello")'
```

## Core Workflow

### Step 1: Tag + List

```bash
python scripts/nb_edit.py notebook.ipynb tag all
python scripts/nb_edit.py notebook.ipynb list
```

Example output (truncated):
```
   # type       exec   tag        description
----------------------------------------------------------------------
   0 code       1      cell-0     read data
   1 markdown   -      md-0       QC filtering
   ...
```

Tags (`cell-0`, `md-0`, …) are persisted in notebook metadata and survive close/reload.

### Step 2: Edit by Tag (Stable, Never Shifts)

```bash
python scripts/nb_edit.py notebook.ipynb set-source-by-tag cell-1 'sc.pp.filter_cells(adata, min_genes=500)'
```

### Step 3: Refresh Tags After Structural Changes

Inserting/deleting cells shifts indices. After structural changes, re-tag:

```bash
python scripts/nb_edit.py notebook.ipynb tag all
```

## Command Reference

### Tagging

| Command | Description |
|---------|-------------|
| `tag all` | Tag all code/md/raw cells (cell-N / md-N / raw-N) |
| `tag code` | Tag only code cells |
| `tag markdown` | Tag only markdown cells |
| `clear-tags` | Remove all hermetic tags |

### Inspection

| Command | Description |
|---------|-------------|
| `list` | List all cells with index, type, exec count, tag, description |
| `find "<text>"` | Search cell content by substring |

### Editing (none touch outputs/metadata)

| Command | Description |
|---------|-------------|
| `set-source-by-tag <tag> "<code>"` | **Recommended** — edit by stable tag |
| `set-source <index> "<code>"` | Edit by cell index (fragile — shifts on insert/delete) |
| `set-source-by-type <type> <nth> "<code>"` | Edit by type + nth occurrence (e.g. `code 2`) |

### Structural

| Command | Description |
|---------|-------------|
| `append "<code>"` | Append a new code cell at end |
| `insert <index> "<code>"` | Insert a code cell at position |
| `delete <index>` | Delete a cell at index |

## What Changes / What Stays

| Field | Changed? |
|-------|----------|
| `source` (cell code / markdown text) | **Yes** — the only thing modified |
| `outputs` (execution results) | **No** — fully preserved |
| `execution_count` | **No** — preserved (may be stale; next Jupyter run refreshes) |
| `cell.metadata` (tags, etc.) | **No** — preserved |
| `metadata.kernelspec` / `language_info` | **No** — preserved |

## Programmatic Use

### Via nbformat (recommended)

```python
from nbformat import read, write, NO_CONVERT

nb = read("notebook.ipynb", NO_CONVERT)
for c in nb.cells:
    if "filter_cells" in c.source:
        c.source = c.source.replace("min_genes=200", "min_genes=500")
write(nb, "notebook.ipynb")
```

### Via raw json (no nbformat dependency)

```python
import json

with open("notebook.ipynb", encoding='utf-8') as f:
    nb = json.load(f)

for cell in nb['cells']:
    tags = cell.get('metadata', {}).get('tags', [])
    if 'cell-3' in tags:
        cell['source'] = ["pass\n", "# new code here\n"]

with open("notebook.ipynb", 'w', encoding='utf-8') as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)
```

**JSON mode rules:**
- `source` must be `list[str]` (one entry per line), not a single string
- `execution_count` = `None` in Python dict (not string `"null"`)
- New cells need `outputs: []` and `execution_count: None`
- Use `indent=1` (nbformat default)

## Common Pitfalls

1. **Always use `NO_CONVERT`** — without it, nbformat may silently upgrade your notebook version.
2. **New cells have no outputs** — expected; they start empty.
3. **`execution_count` goes stale after editing** — intentionally preserved; rerun in Jupyter refreshes it.
4. **Run `tag all` after insert/delete** — tags shift; refresh before next edit.
5. **Markdown cells lack `outputs`** — the script auto-pads them on save.
6. **Don't use raw text editors on .ipynb** — the JSON structure is fragile.

## Verification Checklist

- [ ] `pip install nbformat` completed
- [ ] `tag all` + `list` shows expected cell structure
- [ ] `set-source-by-tag` edits the correct cell (verify with `list`)
- [ ] After insert/delete, `tag all` refreshes tags
- [ ] Notebook opens fine in JupyterLab / VS Code after edit

## License

MIT — see [LICENSE](LICENSE).
