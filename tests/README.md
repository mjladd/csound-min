# Csound Testing

This folder holds the tests for Csound. The tests show that new code works as
expected and that it reports errors correctly. Each section below describes one
suite and the way you run it.

## tests/commandline

This folder holds csd files that a Python test runner starts. A csd file is a
Csound document that carries the orchestra and the score together. The suite
covers the compiler and the runtime, so you can read it as an integration test.

Each csd file declares its own expectations in a `<CsTest>` block at the top of
the file. The block gives a description, the command line arguments, and the
exit code that the test must produce. The runner discovers every csd file under
the folder. When you add the block, the new file joins the suite. A test
that cannot run on this platform sets `skip` with the reason.

To run the suite:

    cmake --build build --target csdtests

## tests/c

This folder holds unit tests written in C++ with the GoogleTest framework. They
cover the parser, the type system, parts of the API, and a number of opcodes.
They also act as documentation, because they show how each function is called.

These tests link against the static library, so the build needs two options:

    cmake -S . -B build -DBUILD_TESTS=ON -DBUILD_STATIC_LIBRARY=ON
    cmake --build build
    ctest --test-dir build

The default build sets both options to `OFF`, and `ctest` then reports no
tests. GoogleTest must be installed for the configure step to find it.

## tests/regression

A collection of earlier bugs that must stay fixed. The runner is
`tests/regression/test.py`, and the expected exit code for each file lives in
the runner itself.

To run the suite:

    cmake --build build --target regression

## tests/soak

The examples from the Csound manual, about 800 csd files. The suite is large
and it runs for a long time.

`src/tools/difftest.py` is the runner to use. It renders each file and
compares the result against `tests/difftest-baseline.json`. That file records
the status and the checksum of every render at the time of the last recording.
Files that do not render cleanly stay in the baseline with the status they
produce, so a change in behavior still shows up. Read `src/tools/README.md` for
the commands.

`tests/soak/runtests.py` is the older runner. It writes an md5 checksum for
each rendered file and compares the set against `tests/soak/Sample_CheckSums`.
The checksums depend on the machine, so treat a difference as a question rather
than a failure.

To run the older runner:

    cmake --build build --target soak
