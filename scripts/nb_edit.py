#!/usr/bin/env python3
"""
nb_edit.py — Surgical .ipynb editor: modify only source code,
preserve outputs, execution_count, and metadata.

All operations only touch 'source' — outputs/execution_count/metadata stay.

Commands:
  list                                List all cells (tag + description)
  tag [code|markdown|all]            Tag cells (cell-N / md-N)
  set-source <idx> "<new code>"      Edit by cell index
  set-source-by-tag <tag> "<new code>"  Edit by stable tag (recommended)
  set-source-by-type <type> <nth> "<new code>"  Edit by type + nth cell
  append "<new code>"                Append a new code cell at end
  insert <at_index> "<new code>"     Insert a code cell at position
  delete <idx>                       Delete a cell
  find "<text>"                      Search cell content
"""

import sys, re
from nbformat import read, write, NO_CONVERT

def load(path):
    with open(path, "r", encoding="utf-8") as f:
        return read(f, NO_CONVERT)

def save(nb, path):
    # nbformat split_lines requires all cells to have outputs (including markdown)
    for c in nb.cells:
        if not hasattr(c, 'outputs'):
            c.outputs = []
        if c.cell_type == 'markdown' and not hasattr(c, 'execution_count'):
            c.execution_count = None
    with open(path, "w", encoding="utf-8") as f:
        write(nb, f)


def _get_tags(cell):
    md = cell.metadata
    if isinstance(md, dict):
        tags = md.get("tags", [])
        return tags if isinstance(tags, list) else []
    return []


def _set_tags(cell, tags):
    if not isinstance(cell.metadata, dict):
        cell.metadata = {}
    cell.metadata["tags"] = tags


def _cell_description(cell):
    """Extract a meaningful one-line description from a cell."""
    source = cell.source
    if not source or not source.strip():
        return "(empty)"

    if cell.cell_type == "markdown":
        for line in source.strip().split("\n"):
            line = line.strip()
            if line:
                desc = re.sub(r'^#+\s*', '', line).strip()
                return desc[:80]
        return "(empty)"

    elif cell.cell_type == "code":
        lines = source.split("\n")
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("#") and not stripped.startswith("#!"):
                desc = stripped.lstrip("#").strip()
                if desc:
                    if desc.lower().startswith(("coding", "flake8", "pylint", "type:", "noqa")):
                        continue
                    return desc[:80]
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                preview = stripped[:60]
                return f"[code] {preview}" if len(stripped) <= 60 else f"[code] {preview}..."
        return "(no code)"

    return f"({cell.cell_type})"


def cmd_list(nb):
    cells = nb.cells
    print(f"Total cells: {len(cells)}")
    header = f"{'#':>4} {'type':<10} {'exec':<6} {'tag':<10} {'description'}"
    print(header)
    print("-" * min(140, len(header) + 40))
    for i, c in enumerate(cells):
        tags = _get_tags(c)
        hermes_tags = [t for t in tags if t.startswith(("cell-", "md-", "raw-"))]
        tag_str = hermes_tags[0] if hermes_tags else "-"
        tag_str_col = tag_str[:10]
        ec = c.get("execution_count", None)
        ec_str = str(ec) if ec is not None else "-"
        desc = _cell_description(c)
        print(f"{i:>4} {c.cell_type:<10} {ec_str:<6} {tag_str_col:<10} {desc}")


def cmd_tag(nb, target="code"):
    """Tag cells with cell-N / md-N / raw-N."""
    code_count = 0
    md_count = 0
    raw_count = 0
    for c in nb.cells:
        tags = _get_tags(c)
        tags = [t for t in tags if not re.match(r'^(cell|md|raw)-\d+$', t)]
        t = c.cell_type
        if t == "code":
            if target in ("code", "all"):
                tags.append(f"cell-{code_count}")
            code_count += 1
        elif t == "markdown":
            if target in ("markdown", "all"):
                tags.append(f"md-{md_count}")
            md_count += 1
        elif t == "raw":
            if target in ("all",):
                tags.append(f"raw-{raw_count}")
            raw_count += 1
        _set_tags(c, tags)

    print(f"Tagged: {code_count} code, {md_count} markdown, {raw_count} raw.")
    print("Tags like cell-0 / md-0 are persisted in cell metadata.")


def cmd_clear_tags(nb):
    count = 0
    for c in nb.cells:
        tags = _get_tags(c)
        new_tags = [t for t in tags if not re.match(r'^(cell|md|raw)-\d+$', t)]
        if len(new_tags) != len(tags):
            count += 1
        _set_tags(c, new_tags)
    print(f"Cleared tags from {count} cells.")


def _find_cell_by_tag(nb, tag):
    for i, c in enumerate(nb.cells):
        if tag in _get_tags(c):
            return i, c
    return None, None


def cmd_set_source_by_tag(nb, tag, new_source):
    idx, cell = _find_cell_by_tag(nb, tag)
    if cell is None:
        print(f"Error: no cell with tag '{tag}'. Run 'tag' first.")
        sys.exit(1)
    old_type = cell.cell_type
    cell.source = new_source
    print(f"OK: cell [{idx}] ({old_type}) tag '{tag}' updated.")


def cmd_find(nb, text):
    cells = nb.cells
    matches = []
    for i, c in enumerate(cells):
        if text.lower() in c.source.lower():
            tags = _get_tags(c)
            tag_str = next((t for t in tags if re.match(r'^(cell|md|raw)-\d+$', t)), "-")
            desc = _cell_description(c)
            matches.append((i, c.cell_type, tag_str, desc))
    if not matches:
        print(f"No cells containing '{text}' found.")
        return
    print(f"Found {len(matches)} cells containing '{text}':")
    print(f"{'#':>4} {'type':<10} {'tag':<10} {'description'}")
    print("-" * 100)
    for i, t, ts, d in matches:
        print(f"{i:>4} {t:<10} {ts:<10} {d}")


def cmd_set_source(nb, idx_str, new_source):
    idx = int(idx_str)
    if idx < 0 or idx >= len(nb.cells):
        print(f"Error: index {idx} out of range (0-{len(nb.cells)-1})")
        sys.exit(1)
    old_type = nb.cells[idx].cell_type
    nb.cells[idx].source = new_source
    print(f"OK: cell [{idx}] ({old_type}) source updated. Outputs/metadata preserved.")


def cmd_set_source_by_type(nb, cell_type, nth_str, new_source):
    nth = int(nth_str)
    count = 0
    for i, c in enumerate(nb.cells):
        if c.cell_type == cell_type:
            if count == nth:
                nb.cells[i].source = new_source
                print(f"OK: cell [{i}] ({cell_type} #{nth}) source updated.")
                return
            count += 1
    print(f"Error: {cell_type} cell #{nth} not found (total: {count})")
    sys.exit(1)


def cmd_append(nb, new_source):
    from nbformat import v4 as nbf
    new_cell = nbf.new_code_cell(source=new_source)
    cells = list(nb.cells)
    cells.append(new_cell)
    nb.cells = cells
    print(f"OK: appended code cell at [{len(nb.cells)-1}]")


def cmd_insert(nb, idx_str, new_source):
    from nbformat import v4 as nbf
    idx = int(idx_str)
    new_cell = nbf.new_code_cell(source=new_source)
    cells = list(nb.cells)
    cells.insert(idx, new_cell)
    nb.cells = cells
    print(f"OK: inserted code cell at index [{idx}]")


def cmd_delete(nb, idx_str):
    idx = int(idx_str)
    if idx < 0 or idx >= len(nb.cells):
        print(f"Error: index {idx} out of range (0-{len(nb.cells)-1})")
        sys.exit(1)
    removed = nb.cells.pop(idx)
    print(f"OK: deleted cell [{idx}] ({removed.cell_type})")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    path = sys.argv[1]
    command = sys.argv[2]
    args = sys.argv[3:]

    nb = load(path)

    handlers = {
        "list": cmd_list, "tag": cmd_tag, "clear-tags": cmd_clear_tags,
        "set-source": cmd_set_source, "set-source-by-tag": cmd_set_source_by_tag,
        "set-source-by-type": cmd_set_source_by_type, "append": cmd_append,
        "insert": cmd_insert, "delete": cmd_delete, "find": cmd_find,
    }

    if command not in handlers:
        print(f"Unknown command: {command}\n")
        print(__doc__)
        sys.exit(1)

    if command == "list":
        handlers[command](nb)
    elif command == "tag":
        handlers[command](nb, args[0] if args else "code")
    elif command == "clear-tags":
        handlers[command](nb)
    elif command == "find":
        handlers[command](nb, args[0] if args else "")
    elif command == "set-source-by-tag":
        handlers[command](nb, args[0], args[1] if len(args) > 1 else "")
    elif command in ("set-source", "delete"):
        handlers[command](nb, *args)
    elif command == "set-source-by-type":
        handlers[command](nb, *args)
    elif command in ("append", "insert"):
        handlers[command](nb, *args)

    if command != "list":
        save(nb, path)
        print(f"Saved to {path}")
