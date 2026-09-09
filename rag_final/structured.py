"""Grounding determinista para tablas de permisos Markdown."""

import re


PERMISSION_MEANINGS = {
    "P": "permitido",
    "L": "permitido con límite o alcance",
    "A": "requiere aprobación",
    "N": "no permitido",
}
TABLE_SEPARATOR_PATTERN = re.compile(r"^\s*\|?(?:\s*:?-+:?\s*\|)+\s*$")


def _cells(line):
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def parse_permission_table(text):
    """Interpreta una tabla de una sola fila de permisos, si es válida."""
    lines = text.splitlines()
    separator_index = next(
        (
            index
            for index, line in enumerate(lines)
            if TABLE_SEPARATOR_PATTERN.match(line)
        ),
        None,
    )
    if separator_index is None or separator_index == 0:
        return None

    headers = _cells(lines[separator_index - 1])
    rows = [line for line in lines[separator_index + 1 :] if "|" in line]
    if len(rows) != 1 or len(headers) < 2:
        return None
    values = _cells(rows[0])
    if len(headers) != len(values) or headers[0].strip().lower() != "acción":
        return None
    codes = values[1:]
    if any(code not in PERMISSION_MEANINGS for code in codes):
        return None

    return {
        "action": values[0],
        "roles": dict(zip(headers[1:], codes)),
        "interpretations": {
            role: PERMISSION_MEANINGS[code]
            for role, code in zip(headers[1:], codes)
        },
    }


def format_facts(table):
    lines = [f"Acción: {table['action']}"]
    lines.extend(
        f"{role}: {meaning}" for role, meaning in table["interpretations"].items()
    )
    return "\n".join(lines)


def _format_role_list(roles):
    if len(roles) == 1:
        return roles[0]
    if len(roles) == 2:
        return " y ".join(roles)
    return f"{', '.join(roles[:-1])} y {roles[-1]}"


def deterministic_answer(table):
    """Construye una respuesta sin generación probabilística."""
    groups = {meaning: [] for meaning in PERMISSION_MEANINGS.values()}
    for role, meaning in table["interpretations"].items():
        groups[meaning].append(role)

    sentences = []
    if groups["permitido"]:
        roles = _format_role_list(groups["permitido"])
        verb = "puede" if len(groups["permitido"]) == 1 else "pueden"
        sentences.append(f"{roles} {verb} {table['action'].lower()}.")
    if groups["permitido con límite o alcance"]:
        roles = _format_role_list(groups["permitido con límite o alcance"])
        verb = "puede" if len(groups["permitido con límite o alcance"]) == 1 else "pueden"
        sentences.append(
            f"{roles} {verb} hacerlo con límite o alcance."
        )
    if groups["requiere aprobación"]:
        roles = _format_role_list(groups["requiere aprobación"])
        verb = "requiere" if len(groups["requiere aprobación"]) == 1 else "requieren"
        sentences.append(
            f"{roles} {verb} aprobación."
        )
    if groups["no permitido"]:
        roles = _format_role_list(groups["no permitido"])
        verb = "tiene" if len(groups["no permitido"]) == 1 else "tienen"
        sentences.append(
            f"{roles} no {verb} permiso."
        )
    return " ".join(sentences)
