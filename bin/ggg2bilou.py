from dataclasses import dataclass

from parsy import regex, seq, string, success


@dataclass
class Character:
    """Class for glossed characters"""

    char: str
    tag: str = ""
    op: str = ""
    span: int = 0
    gloss: str = ""


def sequence():
    """A generator for sequences."""
    num = 0
    while True:
        yield num
        num += 1


def parse_ur_morph(morph: str) -> tuple[str, list[Character]]:
    """Parse a single segment/morph of a UR and return the corresponding BILOU
    (without glosses)."""
    morphs = sequence()
    next(morphs)
    chars = []
    matrix = 0
    span = 0
    tag = "B"
    op = "S"
    morph_type = "root"
    for i, c in enumerate(morph):
        match c:
            case " ":
                matrix = next(morphs)
                span = matrix
                tag = "B"
                op = "S"
            case "-":
                if i == 0:
                    morph_type = "suffix"
                elif i == len(morph) - 1:
                    morph_type = "prefix"
            case "{":
                op = "D"
            case ">":
                span = next(morphs)
                print(span)
                tag = "B"
                op = "A"
            case "}":
                if chars[-1].op == "A":
                    chars[-1].tag = "L"
                    if len(chars) == 0 or (len(chars) > 1 and chars[-2].span != span):
                        chars[-1].tag = "U"
                span = matrix
                op = "S"
            case _:
                char = Character(c, tag, op, span, "")
                chars.append(char)
                if tag == "B":
                    tag = "I"
    chars[-1].tag = "L"
    return (morph_type, chars)


def parse_ur(ur: str) -> list[Character]:
    """Parse a complete UR, yielding the BILOU representation (without
    glosses)."""
    matrix = sequence()
    ur_chars = []
    last_typ = "prefix"
    morphs = [parse_ur_morph(m) for m in ur.split(" ")]
    for i, (typ, chars) in enumerate(morphs):
        start_span = next(matrix)
        match (last_typ, typ):
            case ("root", "root") | ("root", "prefix"):
                ur_chars.append(Character(" ", "O", "S", -1, gloss=""))
            case ("suffix", "root") | ("suffix", "prefix"):
                ur_chars.append(Character(" ", "O", "S", -1, gloss=""))
        for j, _ in enumerate(chars):
            chars[j].span += start_span
        ur_chars += chars
        last_typ = typ
    return ur_chars


def parse_sr(sr: str):
    """Parse a complete SR, yielding the BILOU representation (without
    glosses)."""
    return []


def parse_gloss(gloss: str) -> list[tuple[str, list[tuple[str, list[int]]]]]:
    """Parse a gloss (sequence of glosses) and return a sequence of (base,
    (process, index)) tuples."""
    feature = regex("[^ {};-]+")
    spans = string(";") >> regex(r"\d+").map(int).sep_by(string(","))
    process_inner = seq(feature, spans) | seq(feature, success([]))
    process = string("{") >> process_inner << string("}")
    morph = seq(feature, process.many())
    prefix = morph << string("-")
    suffix = string("-") >> morph
    root = morph
    glosses = (suffix | prefix | root).sep_by(string(" "))
    return glosses.parse(gloss)


def merged_form_gloss(form: str, gloss: str) -> list[Character]:
    """Given a form and a gloss, return the complete BILOU representation of the
    whole sequence."""
    ur = parse_ur(form)
    gl = parse_gloss(gloss)
    offset = 1
    span_glosses = {}
    for matrix, (ft, prs) in enumerate(gl):
        span_glosses[matrix] = ft
        for pr in prs:
            max_sp = offset
            match pr:
                case (ft, []):
                    span_glosses[matrix + offset] = ft
                    offset += 1
                case (ft, spans):
                    for sp in spans:
                        span_glosses[matrix + sp] = ft
                        max_sp = max(sp, max_sp)
                    offset = max(max_sp + 1, offset + 1)
    for i, _ in enumerate(ur):
        ur[i].gloss = span_glosses[ur[i].span]
    return ur
