"""Carga Markdown y genera chunks conscientes de su estructura."""

import os
from pathlib import Path
import re


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PRIVATE_DOCS_DIR = PROJECT_ROOT.parent / "saas-distribucion-peru" / "docs"
DEMO_DOCS_DIR = PROJECT_ROOT / "demo_corpus"
MAX_CHUNK_CHARS = 1800

HEADING_PATTERN = re.compile(r"^\s{0,3}#{1,6}\s+.+$")
LIST_PATTERN = re.compile(r"^\s*(?:[-*+]\s+|\d+[.)]\s+).+$")
TABLE_SEPARATOR_PATTERN = re.compile(r"^\s*\|?(?:\s*:?-+:?\s*\|)+\s*$")


def resolve_docs_dir():
    """Resuelve el corpus configurado, privado compatible o demo público."""
    configured_dir = os.getenv("RAG_DOCS_DIR", "").strip()
    if configured_dir:
        path = Path(configured_dir).expanduser()
        return path if path.is_absolute() else PROJECT_ROOT / path
    if PRIVATE_DOCS_DIR.is_dir():
        return PRIVATE_DOCS_DIR
    return DEMO_DOCS_DIR


def is_table_start(lines, index):
    """Devuelve si dos líneas consecutivas inician una tabla Markdown."""
    return (
        index + 1 < len(lines)
        and "|" in lines[index]
        and TABLE_SEPARATOR_PATTERN.match(lines[index + 1]) is not None
    )


def is_table_row(line):
    return "|" in line and line.strip().startswith("|")


def _heading_level(line):
    match = re.match(r"^\s*(#{1,6})\s+", line)
    return len(match.group(1)) if match else None


def _is_special_start(lines, index):
    line = lines[index]
    return (
        HEADING_PATTERN.match(line) is not None
        or LIST_PATTERN.match(line) is not None
        or is_table_start(lines, index)
    )


def parse_markdown_units(text):
    """Agrupa el documento en encabezados, párrafos, listas y tablas."""
    lines = text.splitlines()
    units = []
    heading_context = []
    heading_context_used = False
    index = 0

    while index < len(lines):
        line = lines[index]
        if not line.strip():
            index += 1
            continue

        if HEADING_PATTERN.match(line):
            level = _heading_level(line)
            heading_context = [
                (heading_level, heading)
                for heading_level, heading in heading_context
                if heading_level < level
            ]
            heading_context.append((level, line.strip()))
            heading_context_used = False
            index += 1
            continue

        if is_table_start(lines, index):
            block = [lines[index], lines[index + 1]]
            index += 2
            while index < len(lines) and is_table_row(lines[index]):
                block.append(lines[index])
                index += 1
            structure = "tabla"
        elif LIST_PATTERN.match(line):
            block = [line]
            index += 1
            while index < len(lines) and LIST_PATTERN.match(lines[index]):
                block.append(lines[index])
                index += 1
            structure = "lista"
        else:
            block = [line]
            index += 1
            while (
                index < len(lines)
                and lines[index].strip()
                and not _is_special_start(lines, index)
            ):
                block.append(lines[index])
                index += 1
            structure = "parrafo"

        if heading_context:
            block = [heading for _, heading in heading_context] + block
            structure = f"encabezado + {structure}"
            heading_context_used = True
        units.append({"text": "\n".join(block), "estructura": structure})

    if heading_context and not heading_context_used:
        units.append(
            {
                "text": "\n".join(heading for _, heading in heading_context),
                "estructura": "encabezado",
            }
        )
    return units


def _split_table_unit(unit):
    """Crea un chunk por fila, repitiendo encabezado y separador."""
    lines = unit["text"].splitlines()
    separator_index = next(
        index
        for index, line in enumerate(lines)
        if TABLE_SEPARATOR_PATTERN.match(line)
    )
    if separator_index == 0:
        return []

    context = lines[: separator_index - 1]
    header = lines[separator_index - 1]
    separator = lines[separator_index]
    return [
        {
            "text": "\n".join(context + [header, separator, row]),
            "estructura": "tabla - fila",
        }
        for row in lines[separator_index + 1 :]
        if is_table_row(row)
    ]


def _split_text_unit(unit):
    text = unit["text"]
    if len(text) <= MAX_CHUNK_CHARS:
        return [unit]

    lines = text.splitlines()
    context = []
    body_lines = lines
    while body_lines and HEADING_PATTERN.match(body_lines[0]):
        context.append(body_lines.pop(0))
    body = "\n".join(body_lines)

    pieces = []
    words = body.split()
    current = []
    current_length = 0
    for word in words:
        added_length = len(word) + (1 if current else 0)
        if current and current_length + added_length > MAX_CHUNK_CHARS:
            pieces.append(
                {
                    "text": "\n".join(context + [" ".join(current)]),
                    "estructura": unit["estructura"],
                }
            )
            current = []
            current_length = 0
        current.append(word)
        current_length += len(word) + (1 if len(current) > 1 else 0)
    if current:
        pieces.append(
            {
                "text": "\n".join(context + [" ".join(current)]),
                "estructura": unit["estructura"],
            }
        )
    return pieces


def load_chunks(docs_dir=None):
    """Carga todos los Markdown y conserva metadata estable por chunk."""
    docs_dir = resolve_docs_dir() if docs_dir is None else Path(docs_dir)
    chunks = []
    for path in sorted(Path(docs_dir).rglob("*.md")):
        source = path.relative_to(docs_dir).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        for unit in parse_markdown_units(text):
            pieces = _split_table_unit(unit) if unit["estructura"].endswith("tabla") else _split_text_unit(unit)
            for piece in pieces:
                chunks.append(
                    {
                        "chunk_id": len(chunks),
                        "source": source,
                        "estructura": piece["estructura"],
                        "text": piece["text"],
                    }
                )
    return chunks
