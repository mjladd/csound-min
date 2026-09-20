# tools

Scripts used to cut this tree down from upstream Csound, and to prove that
the cut did not change the audio.

## difftest.py

Renders a directory of `.csd` files to headerless float samples and records
one SHA-256 hash per file. Run `record` against a build you trust, then
`compare` against a build you changed.

Each file renders twice during `record`. A file whose two renders differ is
marked `nondeterministic` and is left out of later comparisons, so that
`rand` and clock readings do not raise false alarms.

Record a baseline:

    python3 tools/difftest.py record \
        --csound build/csound --plugin-dir build \
        --suite tests/soak --out baseline.json

Compare a later build:

    python3 tools/difftest.py compare \
        --csound build/csound --plugin-dir build \
        --suite tests/soak --baseline baseline.json

`compare` exits non-zero when any file differs. By default both modes use the
curated file list inside `tests/soak/runtests.py`. Pass `--all` to render
every `.csd` in the directory instead.

## prune.sh and prune_cmake.py

The scripts that produced this tree. They are kept for reference, and to
repeat the prune on a fresh upstream checkout.

`prune_cmake.py` reads a CMake file, treats a fixed list of symbols as
permanently false, and then removes every `if` branch that can never run.
It also unwraps branches that always run. `APPLE`, `LINUX` and `UNIX` stay
variable, so the output still configures on Linux and on macOS.

The parser round-trips every CMake file in this tree byte for byte when the
false-symbol list is empty. That test is the reason to trust it. Run the
prune against an upstream checkout with:

    bash tools/prune.sh /path/to/fresh/csound tools/prune_cmake.py

## tests/difftest-baseline.json

The reference hashes, recorded from the unpruned upstream tree at commit
0a6182700 before anything was deleted. Built on Linux, x86-64, gcc 13.3,
double precision samples, with AVX2 on.

Of the 815 files in the curated list, 736 rendered reproducibly, one was
nondeterministic, and 78 already failed on the unpruned tree for reasons
unrelated to this fork, such as needing a MIDI device or an input file that
is not in the repository.

The pruned tree in this repository reproduces all 736 sample for sample.
Compare against it with:

    python3 tools/difftest.py compare \
        --csound build/csound --plugin-dir build \
        --suite tests/soak --baseline tests/difftest-baseline.json

The hashes depend on the compiler, the CPU and the build options. A different
machine needs its own baseline, recorded with `record` before any change.
