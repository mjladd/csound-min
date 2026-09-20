#!/usr/bin/env python3
"""Remove dead platform branches from a CMake file.

Treats a fixed set of symbols as permanently false (Windows, iOS, Android,
Emscripten, WASI, Haiku, bare metal, vcpkg). Evaluates every if/elseif
condition with three-valued logic, then drops branches that can never be
taken and unwraps branches that are always taken. APPLE, LINUX and UNIX stay
variable, so the result still configures on both macOS and Linux.

Usage: prune_cmake.py FILE [FILE ...]   (edits in place, prints a report)
"""

import re
import sys

FALSE_SYMBOLS = {
    "WIN32", "MSVC", "MSVC_IDE", "MINGW", "CYGWIN", "BORLAND", "WATCOM",
    "IOS", "ANDROID", "EMSCRIPTEN", "WASM", "WASI", "HAIKU",
    "BARE_METAL", "USE_VCPKG", "OSXCROSS_TARGET", "BUILD_WASI_BROWSER",
    "CMAKE_HOST_WIN32", "MSYS",
    # Build options this tree no longer offers, so their blocks are dead too.
    "CUSTOM_MALLOC", "BUILD_BELA", "BUILD_INSTALLER", "USE_STATIC_DEPS",
    "USE_GETTEXT", "BUILD_CSBEATS",
}

# Conditions matched literally (after whitespace squeeze) that are false.
FALSE_COMPARISONS = [
    (r'CMAKE_SYSTEM_NAME_UPPER\s+STREQUAL\s+"WASI"', False),
    (r'CMAKE_SYSTEM_NAME\s+STREQUAL\s+"WASI"', False),
    (r'CMAKE_SYSTEM_NAME\s+STREQUAL\s+"Emscripten"', False),
    (r'CMAKE_SYSTEM_NAME\s+STREQUAL\s+"MinGW"', False),
    (r'CMAKE_SYSTEM_NAME\s+STREQUAL\s+"Windows"', False),
    (r'CMAKE_SYSTEM_NAME\s+MATCHES\s+"Windows"', False),
    (r'VCPKG_TARGET_TRIPLET\s+STREQUAL', False),
]

BLOCK_OPEN = {"if", "foreach", "while", "function", "macro"}
BLOCK_CLOSE = {"endif", "endforeach", "endwhile", "endfunction", "endmacro"}


class Stmt:
    """One CMake statement, with the exact source text it came from."""

    def __init__(self, text, command, args):
        self.text = text
        self.command = command
        self.args = args


def split_statements(src):
    """Split source into statements, joining multi-line argument lists."""
    out = []
    i = 0
    n = len(src)
    while i < n:
        # Find the start of a command name on this logical chunk.
        match = re.compile(r"[ \t]*([A-Za-z_][A-Za-z0-9_]*)[ \t]*\(").match(src, i)
        if not match:
            nl = src.find("\n", i)
            nl = n if nl < 0 else nl + 1
            out.append(Stmt(src[i:nl], None, None))
            i = nl
            continue
        depth = 0
        j = match.end() - 1
        in_string = False
        while j < n:
            c = src[j]
            # A backslash escapes the next character, inside a quoted
            # argument and outside one alike.
            if c == "\\":
                j += 2
                continue
            if in_string:
                if c == '"':
                    in_string = False
            elif c == '"':
                in_string = True
            elif c == "#":
                # Comment runs to the end of the line, parens inside it
                # are not syntax.
                nl_at = src.find("\n", j)
                j = n if nl_at < 0 else nl_at
                continue
            elif c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        end = j + 1
        # Absorb a trailing comment and the newline, so text stays round-trippable.
        nl = src.find("\n", end)
        nl = n if nl < 0 else nl + 1
        text = src[i:nl]
        args = src[match.end():j]
        out.append(Stmt(text, match.group(1).lower(), args))
        i = nl
    return out


def tokenize(cond):
    return re.findall(r'\(|\)|"[^"]*"|\$\{[^}]*\}|[^\s()]+', cond)


def evaluate(cond):
    """Return True, False or None for a CMake condition."""
    squeezed = " ".join(cond.split())
    for pattern, value in FALSE_COMPARISONS:
        if re.fullmatch(pattern + r".*", squeezed):
            return value
    tokens = tokenize(cond)
    if not tokens:
        return None
    pos = [0]

    def peek():
        return tokens[pos[0]] if pos[0] < len(tokens) else None

    def take():
        tok = peek()
        pos[0] += 1
        return tok

    def parse_or():
        value = parse_and()
        while peek() and peek().upper() == "OR":
            take()
            right = parse_and()
            if value is True or right is True:
                value = True
            elif value is False and right is False:
                value = False
            else:
                value = None
        return value

    def parse_and():
        value = parse_not()
        while peek() and peek().upper() == "AND":
            take()
            right = parse_not()
            if value is False or right is False:
                value = False
            elif value is True and right is True:
                value = True
            else:
                value = None
        return value

    def parse_not():
        if peek() and peek().upper() == "NOT":
            take()
            inner = parse_not()
            return None if inner is None else (not inner)
        return parse_atom()

    def parse_atom():
        tok = take()
        if tok == "(":
            value = parse_or()
            if peek() == ")":
                take()
            return value
        if tok is None:
            return None
        # Unary tests: consume their operand and give up on knowing the answer.
        if tok.upper() in {"EXISTS", "DEFINED", "COMMAND", "TARGET", "TEST",
                           "IS_DIRECTORY", "IS_ABSOLUTE", "POLICY"}:
            take()
            return None
        # Binary operators: consume the right operand, answer unknown.
        nxt = peek()
        if nxt and nxt.upper() in {"STREQUAL", "MATCHES", "EQUAL", "LESS",
                                   "GREATER", "LESS_EQUAL", "GREATER_EQUAL",
                                   "VERSION_LESS", "VERSION_GREATER",
                                   "VERSION_EQUAL", "VERSION_LESS_EQUAL",
                                   "VERSION_GREATER_EQUAL", "IN_LIST",
                                   "STRLESS", "STRGREATER"}:
            take()
            take()
            return None
        if tok in FALSE_SYMBOLS:
            return False
        return None

    return parse_or()


def build_tree(stmts, start=0, stop=None):
    """Group statements into a nested list. If-chains become ('if', branches)."""
    stop = len(stmts) if stop is None else stop
    nodes = []
    i = start
    while i < stop:
        stmt = stmts[i]
        if stmt.command == "if":
            end = find_close(stmts, i, stop)
            nodes.append(("if", parse_chain(stmts, i, end), stmts[end]))
            i = end + 1
        elif stmt.command in BLOCK_OPEN:
            end = find_close(stmts, i, stop)
            nodes.append(("block", stmt, build_tree(stmts, i + 1, end), stmts[end]))
            i = end + 1
        else:
            nodes.append(("stmt", stmt))
            i += 1
    return nodes


def find_close(stmts, i, stop):
    opener = stmts[i].command
    closer = "end" + opener
    depth = 0
    j = i
    while j < stop:
        cmd = stmts[j].command
        if cmd == opener:
            depth += 1
        elif cmd == closer:
            depth -= 1
            if depth == 0:
                return j
        j += 1
    raise SystemExit("unbalanced %s at statement %d" % (opener, i))


def parse_chain(stmts, i, end):
    """Split one if/elseif/else chain into [(keyword_stmt, body_nodes), ...]."""
    marks = [i]
    depth = 0
    for j in range(i, end):
        cmd = stmts[j].command
        if cmd in BLOCK_OPEN:
            depth += 1
        elif cmd in BLOCK_CLOSE:
            depth -= 1
        elif depth == 1 and cmd in ("elseif", "else"):
            marks.append(j)
    marks.append(end)
    branches = []
    for k in range(len(marks) - 1):
        head = stmts[marks[k]]
        body = build_tree(stmts, marks[k] + 1, marks[k + 1])
        branches.append((head, body))
    return branches


class Report:
    def __init__(self):
        self.dropped = []
        self.unwrapped = []


def count_lines(nodes):
    total = 0
    for node in nodes:
        if node[0] == "stmt":
            total += node[1].text.count("\n")
        elif node[0] == "if":
            total += 2
            for head, body in node[1]:
                total += head.text.count("\n") + count_lines(body)
        else:
            total += node[1].text.count("\n") + count_lines(node[2]) + 1
    return total


def render(nodes, report):
    out = []
    for node in nodes:
        if node[0] == "stmt":
            out.append(node[1].text)
        elif node[0] == "block":
            out.append(node[1].text)
            out.append(render(node[2], report))
            out.append(node[3].text)
        else:
            out.append(render_chain(node, report))
    return "".join(out)


def render_chain(node, report):
    _, branches, endstmt = node
    kept = []
    for head, body in branches:
        if head.command == "else":
            kept.append((None, head, body))
            continue
        value = evaluate(head.args)
        if value is False:
            report.dropped.append((" ".join(head.args.split())[:70],
                                   count_lines(body)))
            continue
        kept.append((value, head, body))
    # Nothing survives: the whole chain goes.
    if not kept:
        return ""
    # First surviving branch is unconditionally true: keep only its body.
    first_value, first_head, first_body = kept[0]
    if first_value is True or (first_head.command == "else" and len(kept) == 1):
        label = ("else" if first_head.command == "else"
                 else " ".join(first_head.args.split())[:70])
        report.unwrapped.append((label, count_lines(first_body)))
        return render(first_body, report)
    pieces = []
    for index, (_, head, body) in enumerate(kept):
        text = head.text
        if index == 0 and head.command == "elseif":
            text = re.sub(r"\belseif\b", "if", text, count=1)
        pieces.append(text)
        pieces.append(render(body, report))
    pieces.append(endstmt.text)
    return "".join(pieces)


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    for path in sys.argv[1:]:
        src = open(path).read()
        before = src.count("\n")
        stmts = split_statements(src)
        # Round-trip guard: the split must be lossless.
        if "".join(s.text for s in stmts) != src:
            sys.exit("%s: statement split is not lossless, refusing to edit" % path)
        tree = build_tree(stmts)
        report = Report()
        result = render(tree, report)
        open(path, "w").write(result)
        after = result.count("\n")
        print("%s: %d -> %d lines (-%d)" % (path, before, after, before - after))
        for label, lines in report.dropped:
            print("   drop    %-72s %4d lines" % (label, lines))
        for label, lines in report.unwrapped:
            print("   unwrap  %-72s %4d lines" % (label, lines))


if __name__ == "__main__":
    main()
