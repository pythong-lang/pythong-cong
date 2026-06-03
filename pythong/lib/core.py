"""
pythong core — shared transformation logic for pythong-cong and pythong-traductiong
"""

import tokenize
import io
import re

# ---------------------------------------------------------------------------
# Regex-based name transforms (applied to raw source before/after tokenizing)
#
# These handle suffix/pattern replacements that can't be done token-by-token.
# Order matters: more specific patterns first.
#
# Each entry: (py_pattern, py_repl, cong_pattern, cong_repl)
# ---------------------------------------------------------------------------

REGEX_MAP = [
    # Exception before Error to avoid partial match issues
    (re.compile(r'\bException\b'),      lambda m: "Exceptiong",
     re.compile(r'\bExceptiong\b'),     lambda m: "Exception"),
    # Error suffix: TypeError -> TypeCaguade, bare Error -> Caguade
    (re.compile(r'\b(\w+)?Error\b'),    lambda m: (m.group(1) or "") + "Caguade",
     re.compile(r'\b(\w+)?Caguade\b'),  lambda m: (m.group(1) or "") + "Error"),
]


def _apply_regex_py_to_cong(source: str) -> str:
    for py_pat, py_repl, _, _ in REGEX_MAP:
        source = py_pat.sub(py_repl, source)
    return source


def _apply_regex_cong_to_py(source: str) -> str:
    for _, _, cong_pat, cong_repl in REGEX_MAP:
        source = cong_pat.sub(cong_repl, source)
    return source


# ---------------------------------------------------------------------------
# Keyword map
#
# Format: "python_keyword": ("canonical_cong_form", ["alias1", "alias2", ...])
# The canonical form is what pythong-traductiong outputs.
# All aliases (including the canonical) are accepted by pythong-cong.
# Plain Python keywords are always accepted as-is (passthrough).
#
# NOTE: "return" is NOT in this map — it is handled separately as a
# positional transformation (end-of-logical-line).
#   return <expr>  <->  <expr> cong
#   return         <->  ohcong
# ---------------------------------------------------------------------------

KEYWORD_MAP: dict[str, tuple[str, list[str]]] = {
    # keyword        canonical         aliases
    "False":       ("Fada",           []),
    "None":        ("Keutchi",        []),
    "True":        ("Lesang",         ["Untigre"]),
    "and":         ("égalemeng",        ["andg"]),
    "as":          ("kiéle",          ["asg"]),
    "assert":      ("assertcong",     ["assertg"]),
    "async":       ("trangquille",    []),
    "await":       ("atteng",         []),
    "break":       ("breakcong",      ["breakg"]),
    "class":       ("classcong",      ["classg"]),
    "continue":    ("continuecong",   ["continueg"]),
    "def":         ("tié",            []),
    "del":         ("delcong",        ["delg"]),
    "elif":        ("oumemequang",    []),
    "else":        ("sinong",         []),
    "except":      ("cartong",        ["exceptg"]),
    "finally":     ("finallemong",    ["finallyg"]),
    "for":         ("forcong",        ["forg"]),
    "from":        ("fouillang",      ["fromg"]),
    "global":      ("globalcong",     ["globalg"]),
    "if":          ("quang",          ["ifg"]),
    "import":      ("preng",          ["importg"]),
    "in":          ("dang",           ["ing"]),
    "is":          ("tiéle",          ["isg"]),
    "lambda":      ("gadgi",          ["gadgo"]),
    "nonlocal":    ("parigo",         ["nonlocalg"]),
    "not":         ("nong",           ["notg"]),
    "or":          ("oubieng",        ["org"]),
    "pass":        ("allezva",        ["passg"]),
    "raise":       ("siffle",         ["raiseg"]),
    "try":         ("essayong",         ["tryg"]),
    "while":       ("tangque",        ["whileg"]),
    "with":        ("quangtia",       ["withg"]),
    "yield":       ("engraine",       ["yieldg"]),
    # soft keywords
    "_":           ("_cong",          ["_g"]),
    "case":        ("casecong",       ["caseg"]),
    "match":       ("matchcong",      ["matchg"]),
    "type":        ("typecong",       ["typeg"]),
}

SOFT_KEYWORDS = {"_", "case", "match", "type"}

# Derived lookup tables
CONG_TO_PY: dict[str, str] = {}
PY_TO_CONG: dict[str, str] = {}

for py_kw, (canonical, aliases) in KEYWORD_MAP.items():
    PY_TO_CONG[py_kw] = canonical
    CONG_TO_PY[canonical] = py_kw
    for alias in aliases:
        CONG_TO_PY[alias] = py_kw

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class CongSyntaxError(SyntaxError):
    pass


def _tokenize(source: str) -> list:
    try:
        return list(tokenize.generate_tokens(io.StringIO(source).readline))
    except tokenize.TokenError as e:
        raise CongSyntaxError(f"Tokenization error: {e}") from e


def _detokenize(tokens: list) -> str:
    """
    Reconstruct source from tokens, preserving the *original* whitespace
    between tokens.

    We can't use tokenize.untokenize() with 2-tuples: it throws away all
    position info and re-spaces the code with a heuristic that mangles
    spacing (e.g. "open (", ")kiele", "f :"). Renaming a token only changes
    its .string, never its .start/.end, so the gap between two consecutive
    tokens (next.start_col - prev.end_col) still reflects the source exactly.
    """
    parts: list[str] = []
    prev_row, prev_col = 1, 0

    for tok in tokens:
        if tok.type == tokenize.ENCODING:
            continue

        srow, scol = tok.start
        erow, ecol = tok.end
        s = tok.string

        if srow != prev_row:
            # A newline was already emitted via a NEWLINE/NL/string token;
            # scol is this line's indentation.
            parts.append(" " * scol)
        else:
            gap = scol - prev_col
            if gap < 0:
                gap = 0
            # Safety net: never let two tokens merge into one (e.g. after an
            # insertion where positions coincide, like "return" + expr).
            if gap == 0 and parts:
                last = parts[-1]
                if (last and (last[-1].isalnum() or last[-1] == "_")
                        and s and (s[0].isalnum() or s[0] == "_")):
                    gap = 1
            parts.append(" " * gap)

        parts.append(s)
        prev_row, prev_col = erow, ecol

    return "".join(parts)


def _is_soft_keyword_context(prev_tokens: list) -> bool:
    non_trivial = [t for t in prev_tokens
                   if t.type not in (tokenize.NEWLINE, tokenize.NL,
                                     tokenize.INDENT, tokenize.DEDENT,
                                     tokenize.ENCODING, tokenize.COMMENT)]
    return len(non_trivial) == 0


_SKIP = {tokenize.NEWLINE, tokenize.NL, tokenize.INDENT,
         tokenize.DEDENT, tokenize.ENCODING, tokenize.ENDMARKER,
         tokenize.COMMENT}


def _split_logical_lines(tokens: list) -> list[list[int]]:
    """
    Returns a list of logical lines, each as a list of token indices.
    Tracks bracket depth to handle multiline expressions.
    """
    lines = []
    current = []
    depth = 0

    for i, tok in enumerate(tokens):
        if tok.string in ("(", "[", "{"):
            depth += 1
        elif tok.string in (")", "]", "}"):
            depth -= 1

        current.append(i)

        if tok.type == tokenize.NEWLINE and depth == 0:
            lines.append(current)
            current = []

    if current:
        lines.append(current)

    return lines


# ---------------------------------------------------------------------------
# cong -> py
# ---------------------------------------------------------------------------

def transform_cong_to_py(source: str) -> str:
    source = _apply_regex_cong_to_py(source)
    tokens = _tokenize(source)

    # Pass 1: swap regular keywords
    for i, tok in enumerate(tokens):
        if tok.type == tokenize.NAME and tok.string in CONG_TO_PY:
            py_kw = CONG_TO_PY[tok.string]
            if py_kw in SOFT_KEYWORDS and not _is_soft_keyword_context(tokens[:i]):
                continue
            tokens[i] = tok._replace(string=py_kw)

    # Pass 2: handle cong / ohcong -> return
    result = []
    for line_indices in _split_logical_lines(tokens):
        line = [tokens[i] for i in line_indices]
        content = [t for t in line if t.type not in _SKIP]

        if not content:
            result.extend(line)
            continue

        last = content[-1]

        if last.type == tokenize.NAME and last.string == "ohcong":
            if len(content) != 1:
                raise CongSyntaxError(
                    f"ohcong must be alone on its line (line {last.start[0]})"
                )
            result.extend(t._replace(string="return") if t is last else t for t in line)

        elif last.type == tokenize.NAME and last.string == "cong":
            if len(content) < 2:
                raise CongSyntaxError(
                    f"cong requires a return value — use ohcong for bare return (line {last.start[0]})"
                )
            # Remove cong, prepend return before first content token
            first = content[0]
            expr_end = content[-2].end  # last real token before cong
            new_line = []
            for t in line:
                if t is last:
                    continue  # drop cong
                if t is first:
                    new_line.append(t._replace(string="return"))
                    new_line.append(first)  # original first token
                elif t.type == tokenize.NEWLINE:
                    # Re-base the trailing NEWLINE so dropping "cong" doesn't
                    # leave trailing whitespace before the line break.
                    new_line.append(t._replace(start=expr_end))
                else:
                    new_line.append(t)
            result.extend(new_line)

        else:
            result.extend(line)

    return _detokenize(result)


# ---------------------------------------------------------------------------
# py -> cong
# ---------------------------------------------------------------------------

def transform_py_to_cong(source: str) -> str:
    tokens = _tokenize(source)

    # Pass 1: handle return -> cong / ohcong
    result = []
    for line_indices in _split_logical_lines(tokens):
        line = [tokens[i] for i in line_indices]
        content = [t for t in line if t.type not in _SKIP]

        if not content or content[0].string != "return":
            result.extend(line)
            continue

        return_tok = content[0]

        if len(content) == 1:
            # bare return → ohcong
            result.extend(
                t._replace(string="ohcong") if t is return_tok else t
                for t in line
            )
        else:
            # return <expr> → <expr> cong
            # Drop return token, append cong before the closing NEWLINE.
            # Re-base the first expression token onto return's start column so
            # dropping "return" doesn't inflate the line's leading whitespace.
            first = content[1]
            new_line = []
            skip_return = True
            for t in line:
                if skip_return and t is return_tok:
                    skip_return = False
                    continue
                if t is first:
                    new_line.append(t._replace(start=return_tok.start))
                    continue
                if t.type == tokenize.NEWLINE:
                    new_line.append(t._replace(type=tokenize.NAME, string="cong"))
                    new_line.append(t)
                else:
                    new_line.append(t)
            result.extend(new_line)

    # Pass 2: swap regular keywords
    out = []
    for tok in result:
        if tok.type == tokenize.NAME and tok.string in PY_TO_CONG:
            if tok.string in SOFT_KEYWORDS and not _is_soft_keyword_context(out):
                out.append(tok)
                continue
            out.append(tok._replace(string=PY_TO_CONG[tok.string]))
            continue
        out.append(tok)

    result_src = _detokenize(out)
    return _apply_regex_py_to_cong(result_src)
