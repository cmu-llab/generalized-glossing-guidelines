#!/usr/bin/env python3

import argparse
import glob

from parsy import ParseError, regex, seq, string
import yaml
from yaml.parser import ParserError


class StructureError(Exception):
    pass


class AlignmentError(Exception):
    pass


###############################################################################
# The document schema
###############################################################################

schema = {
    "obj_lang": str,
    "meta_lang": list,
    "segs": {
        "start": float,
        "end": float,
        "speaker": int,
        "ur": str,
        "sr": str,
        "gl": str,
        "tr": str,
    },
}

###############################################################################
# Grammars for parsing URs and SRs
###############################################################################

# Type signature for form_seg: str
form_seg = regex("[^{}>= -]+").map(lambda x: ("seg", x))

# Type signature for form_proc: tuple[str, str]
ur_proc = (
    string("{") + regex("[^}>]*") + string(">") + regex("[^}>]*") + string("}")
).map(lambda x: ("proc", x))
sr_proc = (string("{") + regex("[^}]+") + string("}")).map(lambda x: ("proc", x))

# Type signature for ur_morph: tuple[str, list[FormSeg | FormProc]]
ur_morph_core = (ur_proc | form_seg).at_least(1)
ur_prefix = seq(ur_morph_core, string("-")).combine(lambda x, _: ("prefix", x))
ur_suffix = seq(string("-"), ur_morph_core).combine(lambda _, x: ("suffix", x))
ur_proclitic = seq(ur_morph_core, string("=")).combine(lambda x, _: ("proclitic", x))
ur_enclitic = seq(string("="), ur_morph_core).combine(lambda _, x: ("enclitic", x))
ur_root = ur_morph_core.map(lambda x: ("root", x))
ur_morph = ur_suffix | ur_enclitic | ur_prefix | ur_proclitic | ur_root

# Type signature for sr_morph: tuple[str, list[FormSeg | FormProc]]
sr_morph_core = (sr_proc | form_seg).at_least(1)
sr_prefix = seq(sr_morph_core, string("-")).combine(lambda x, _: ("prefix", x))
sr_suffix = seq(string("-"), sr_morph_core).combine(lambda _, x: ("suffix", x))
sr_proclitic = seq(sr_morph_core, string("=")).combine(lambda x, _: ("proclitic", x))
sr_enclitic = seq(string("="), sr_morph_core).combine(lambda _, x: ("enclitic", x))
sr_root = sr_morph_core.map(lambda x: ("root", x))
sr_morph = sr_suffix | sr_enclitic | sr_prefix | sr_proclitic | sr_root

# Type signature for form: list[FormMorph]
ur_form = ur_morph.sep_by(string(" "))
sr_form = sr_morph.sep_by(string(" "))

###############################################################################
# Grammar for parsing glosses
###############################################################################

# Type signature for gloss_seg: tuple[str, str]
gloss_seg = regex("[^ {}=-]+")

# Type signature for gloss_proc: tuple[str, list[int]]
gloss_proc_qualified = seq(
    string("{").result("") + regex("[0-9A-Z.]+") + string(";").result(""),
    regex(r"\d").map(int).sep_by(string(","), min=1),
    string("}"),
).combine(lambda x, idxs, _: (x, idxs))
gloss_proc_unqualified = (
    string("{").result("") + regex("[0-9A-Z.]+") + string("}").result("")
).map(lambda x: (x, [-1]))
gloss_proc = gloss_proc_qualified | gloss_proc_unqualified

# Type signature for gloss_morph: tuple[str, tuple[str, list[tuple[str, list[int]]]]]]
gloss_morph_core = seq(gloss_seg, gloss_proc.many()).map(tuple)
gloss_morph_prefix = seq(gloss_morph_core, string("-")).combine(
    lambda x, _: ("prefix", x)
)
gloss_morph_proclitic = seq(gloss_morph_core, string("=")).combine(
    lambda x, _: ("proclitic", x)
)
gloss_morph_suffix = seq(string("-"), gloss_morph_core).combine(
    lambda _, x: ("suffix", x)
)
gloss_morph_enclitic = seq(string("="), gloss_morph_core).combine(
    lambda _, x: ("enclitic", x)
)
gloss_morph_root = gloss_morph_core.map(lambda x: ("root", x))
gloss_morph = (
    gloss_morph_suffix
    | gloss_morph_enclitic
    | gloss_morph_prefix
    | gloss_morph_proclitic
    | gloss_morph_root
)

# Type signature for gloss: list[GlossMorph]
gloss = gloss_morph.sep_by(string(" "))


###############################################################################
# Validation functions
###############################################################################


def validate_fields(doc: dict) -> None:
    """Raises an exception if the fields in the GGF file do not match those in
    the schema"""

    def helper(obj, sch):
        for key, value in obj.items():
            if key not in sch:
                raise StructureError(f"Field '{key}' does not exist in schema.")
            elif isinstance(value, dict):
                helper(value, sch[key])
            elif not isinstance(sch[key], dict) and not isinstance(value, sch[key]):
                raise StructureError(f"Value '{value}' is not of type '{sch[key]}'.")

    helper(doc, schema)


def validate_procs(
    u: tuple[str, list[tuple[str, str]]],
    s: tuple[str, list[tuple[str, str]]],
    g: tuple[str, list[tuple[str, list[int]]]],
) -> None:
    """Raises an exception if the number of processes indicated in the UR, SR,
    and gloss of a token are not equal."""
    _, g_procs = g
    num_gloss_procs = 0
    for _, idxs in g_procs:
        num_gloss_procs += len(idxs)

    def num_form_procs(form: tuple[str, list[tuple[str, str]]]) -> int:
        return sum([1 for (t, _) in form if t == "proc"])

    try:
        assert num_form_procs(u) == num_form_procs(s) == num_gloss_procs
    except AssertionError as e:
        raise AlignmentError(
            "Number of processeses do not agree."
            + f"UR: {num_form_procs(u)}, "
            + f"SR: {num_form_procs(s)}, "
            + f"GL: {num_gloss_procs}."
        ) from e


def validate_segs(doc) -> None:
    """Raises an exception if number of tokens, types of corresponding tokens,
    or number of processes do not agree among the UR, SR, and gloss"""
    for seg_id, seg in enumerate(doc["segs"]):
        try:
            ur = ur_form.parse(seg["ur"])
        except ParseError as e:
            raise StructureError(f"Error parsing UR in Segment {seg_id}.") from e
        try:
            sr = sr_form.parse(seg["sr"])
        except ParseError as e:
            raise StructureError(f"Error parsing SR in Segment {seg_id}.") from e
        try:
            gl = gloss.parse(seg["gl"])
        except ParseError as e:
            raise StructureError(f"Error parsing gloss in Segment {seg_id}.") from e
        if len(ur) == len(sr) == len(gl):
            igt = zip(ur, sr, gl)
            for token_id, (u, s, g) in enumerate(igt):
                (u_type, u), (s_type, s), (g_type, g) = (u, s, g)
                if u_type == s_type == g_type:
                    pass
                else:
                    raise AlignmentError(
                        f"Types of tokens in Segment {seg_id} do not align."
                    )
                try:
                    validate_procs(u, s, g)
                except AlignmentError as e:
                    raise AlignmentError(
                        "Number of processes in "
                        + f"Segment {seg_id}, Token {token_id} "
                        + "do not agree."
                    ) from e
        else:
            raise AlignmentError(f"Number of tokens in Segment {seg_id} do not agree.")


def validate(fn, verbose) -> None:
    """Raises an exception if the GGF file is invalid."""
    print(f"Validating {fn}...")
    try:
        with open(fn) as f:
            if verbose:
                print("Valid YAML?...")
            # Try to load the GGF file with the standard YAML SafeLoder.
            try:
                doc = yaml.load(f, Loader=yaml.SafeLoader)
            # In the event that the YAML parser is unable to parse the file,
            # propogate an exception up the chain.
            except ParserError as exc:
                raise ParserError("Invalid YAML.") from exc
            if verbose:
                print("Valid YAML fields?...")
            # Check the conformance of the files fields to the schema.
            try:
                validate_fields(doc)
            # If the file does not conform, propogate the error up the chain.
            except StructureError as exc:
                raise StructureError from exc
            if verbose:
                print("Valid forms and gloses?...")
            # Validate the ur, sr, and gl fields using the grammars defined
            # above. This needs to be changed so that we don't stop with the
            # first parse error.
            try:
                validate_segs(doc)
            except AlignmentError as exc:
                raise AlignmentError("Invalid alignment of tokens.") from exc
            print("Valid.")
    except ParseError as exc:
        print(exc)
    except StructureError as exc:
        print(exc)
    except AlignmentError as exc:
        print(exc)


def main(args) -> None:
    if args.batch:
        for fn in glob.glob("*.yml"):
            validate(fn, args.verbose)
    elif args.input:
        validate(args.input, args.verbose)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", help="Input file (xleipzig YAML)")
    parser.add_argument(
        "-b",
        "--batch",
        action="store_true",
        help="Validate all .yml " + "files in the currect directory",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose mode")
    args = parser.parse_args()
    main(args)
