# Where the code lives

A reading map for this tree. The goal is to let you find the file that holds
a behavior you care about, without reading 310,000 lines first.

Two terms this document uses throughout. An opcode is one unit generator, the
thing a score calls by name, such as `oscil` or `reverb`. Ksmps is the number
of audio samples that the engine computes in one control step.

## The short version

Four files carry most of the engine. Read them in this order.

1. `Frontends/csound/csound_main.c` (239 lines). The whole command line
   program. It parses nothing and computes nothing. It calls the C API.
2. `Top/main.c`. `csoundCompile` at line 217 is the command line compile
   path. It calls `argdecode`, splits a `.csd` file, compiles the orchestra,
   and sorts the score.
3. `Top/csound_perf.c` (497 lines). The performance loop. `kperf` at line 241
   is the function that produces every sample this program ever writes.
4. `Engine/insert.c` (3,012 lines). Instrument instances. `insert_event` at
   line 895 starts a note. `init0` at line 765 sets up instrument 0.

`Top/csound.c` (2,437 lines) holds the rest of the public API, including
`csoundCompileTree` at line 1571 and `csoundCompileOrc` at line 1575, which
are the entry points an embedding program uses instead of `csoundCompile`.

## The data structure that explains the design

`include/csoundCore.h` line 537 defines `OPDS`, the header that sits at the
front of every opcode instance:

```c
typedef struct opds {
    struct opds * nxti;   /* next opcode in the init-time chain */
    struct opds * nxtp;   /* next opcode in the perf-time chain */
    struct opds * nxtd;   /* next opcode in the deinit chain */
    SUBR    init;         /* run once, when the note starts */
    SUBR    perf;         /* run once per control step */
    SUBR    deinit;
    OPTXT   *optext;
    INSDS   *insdshead;   /* the instrument instance that owns this opcode */
} OPDS;
```

Once you see this, the engine stops being mysterious. An instrument instance
is a linked list of opcodes. Performance walks the list and calls `perf` on
each one. Everything else is bookkeeping around that walk.

`OENTRY` in the same header is the other half. It is the registration record:
an opcode name, the size of its state block, its output and input type
strings, and the three function pointers. `Engine/entry.c` line 78 opens
`opcodlst_1[]`, the table of 1,543 built-in entries. Each opcode file under
`Opcodes/` declares its own `localops[]` table in the same shape.

## The directories

| Directory | Lines | What it holds |
| --- | --- | --- |
| `Engine/` | 38,664 | The orchestra language: preprocessor, lexer, parser, type system, and the code that turns a parse tree into opcode chains. Also the score reader and the scheduler. |
| `OOps/` | 52,556 | The base unit generators, the ones that predate the plugin system. `ugens1.c` through `ugens6.c`, `aops.c` for arithmetic, `str_ops.c` for strings. |
| `Opcodes/` | 125,179 | The opcode library, 249 files. Each file is close to self-contained. This is the largest directory and the easiest one to ignore until you need one specific opcode. |
| `Top/` | 16,847 | The library boundary. The public API, argument parsing, message routing, the performance loop. |
| `InOut/` | 18,401 | Real-time audio and MIDI back ends, sound file reading and writing, and the built-in graph display. |
| `include/` | 10,965 | Public headers. `csound.h` is the API, 127 functions. `csoundCore.h` is the internal one, and it holds the `CSOUND` struct. |
| `H/` | 10,717 | Internal headers, mostly per-opcode state structure definitions. |
| `util/` | 15,681 | Standalone analysis programs: `pvanal`, `hetro`, `lpanal`, `atsa`, `dnoise`, `srconv`. Also built as the `stdutil` plugin, which is what `csound -U <name>` loads. |
| `tests/` | 17,134 | The test suites, plus 1,678 `.csd` files. |

## How one note becomes sound

Follow this path once and the rest of the engine reads more easily.

1. `csound_main.c` calls `csoundCompile`, then `csoundStart`, then loops on
   `csoundPerformKsmps` until it returns non-zero.
2. `Top/main.c` `csoundCompile` at line 217 reads the flags through
   `argdecode`, then calls `read_unified_file4` at line 296 to split a `.csd`
   file into its orchestra and score parts.
3. `Engine/csound_pre.lex` runs the preprocessor, which handles `#include`
   and macros. It is a separate Flex lexer of 1,566 lines.
4. `Engine/csound_orc.lex` and `Engine/csound_orc.y` produce a parse tree.
   `Engine/new_orc_parser.c` `csoundParseOrc` at line 103 drives them.
5. `Engine/csound_orc_semantics.c` resolves types and picks, for each opcode
   call, which `OENTRY` matches the argument types.
6. `Engine/csound_orc_compile.c` turns the tree into `OPTXT` templates, one
   per opcode call, grouped per instrument.
7. `Engine/sread.c` reads the score. `scsortstr` sorts the events by time.
8. `Engine/musmon.c` runs the event loop. `sense_events` at line 1268 finds
   the events that are due.
9. `Engine/insert.c` `insert_event` at line 895 allocates an instance from
   the templates and links its opcodes into the active chain.
10. `Top/csound_perf.c` `kperf` at line 241 walks the active chain and calls
    `perf` on every opcode, ksmps samples at a time.
11. `csound->spout` holds the result. `InOut/` writes it to a file or a
    device.

## What the engine keeps its state in

`include/csoundCore.h` line 1091 opens `struct CSOUND_`. It has 529 fields,
260 of which are function pointers. That one struct is the whole engine
context, and it is also the plugin contract: an opcode compiled separately
reaches the engine only through those function pointers.

The size of this struct explains a lot about the codebase. There are almost
no globals, because everything hangs off `CSOUND`. It also means the field
layout cannot change without breaking every third-party opcode binary.

## Reading the orchestra language

Four Flex lexers and one Bison grammar, 5,659 lines in total, sit in
`Engine/`:

- `csound_pre.lex`, the preprocessor for orchestra text.
- `csound_prs.lex`, the preprocessor for score text.
- `csound_orc.lex` and `csound_orc.y`, the orchestra grammar.
- `csound_sco.lex`, the score lexer.

The generated parser is not in the tree. CMake runs `flex` and `bison` at
build time, so both tools must be installed.

## What this tree does not contain

This is a pruned fork. It targets a Linux and macOS command line build and
nothing else. It does not contain the mobile and web ports, the Java, Python
and Lisp bindings, packaging, the translation catalogs, the `csbeats` score
translator, or the `csdebugger` program. `tools/README.md` records how the
cut was made and how to repeat it.

One honest note on the result. The prune removed 923 files and 16 MB, but
only 12,000 lines of C, because most of what went was project files, build
scripts and interface layouts. The engine you have to understand is the same
size it always was. What changed is that `CMakeLists.txt` went from 1,971
lines to 1,590, the build produces one library and one program, and nothing
in the tree serves a platform you do not use.
