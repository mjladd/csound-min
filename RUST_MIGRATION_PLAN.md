# Csound to Rust: Assessment and Plan

Date: 2026-09-20. Branch examined: `develop` (Csound 7.0.0 beta).

## 1. What the code looks like today

Measured counts from this checkout.

| Area | Files | Lines of C/C++ |
| --- | --- | --- |
| `Engine/` (parser, compiler, scheduler, score) | 38 | 38,664 |
| `OOps/` (base unit generators) | 42 | 52,556 |
| `Opcodes/` (the opcode library) | 249 | 125,179 |
| `InOut/` (audio, MIDI, file IO) | 39 | 21,527 |
| `Top/` (library entry, argument parsing) | 19 | 16,847 |
| `H/` and `include/` (headers) | 120 | 21,682 |
| `util/` and `util1/` (analysis tools) | 62 | 18,652 |
| `tests/` | 65 | 17,134 |
| Total in the repository | 726 | 322,504 |

Other facts that drive the estimate.

- An opcode is one unit generator that a score can call. The build registers 1,821 distinct opcode names.
- Those names map to about 1,893 separate implementation functions. Almost no opcode shares code with another one.
- The orchestra language front end is 5,659 lines of Flex and Bison input. On top of that sit 13,519 lines of hand written semantics, expression rewriting, and user defined opcode support.
- The preprocessor is a separate Flex lexer of 1,566 lines, and the string preprocessor adds 1,954 more.
- The `CSOUND` struct in `include/csoundCore.h` has 529 fields, of which 260 are function pointers. That struct is the plugin ABI. An ABI is the binary contract that compiled plugins depend on.
- `include/csound.h` exports 127 public functions.
- The core and opcode sources contain 801 `#if` or `#ifdef` directives. `CMakeLists.txt` defines 37 build options.
- `tests/` holds 1,678 `.csd` files, and 835 of them are per opcode examples in `tests/soak/`.

## 2. The GUI goal is already met

The repository contains no GUI for the core product. `Frontends/` is 757 lines of C and holds the
command line program, the `beats` tool, and a debugger. The editors that people associate with
Csound, such as CsoundQt and Cabbage, live in separate repositories.

What this repository does carry, beyond the core, is platform ports and language bindings:
`iOS/` (7.3 MB, mostly Xcode project files and `.xib` layouts), `Android/`, `wasm/`, `Java/`,
`Python/`, `Lisp/`, `Bela/`, `Daisy/`, and `Zynq/`. Removing all of that is a deletion job in C
and CMake. It does not need Rust, and it takes days, not months.

## 3. Cost of a full rewrite

The table assumes one experienced developer who knows Rust, digital signal processing, and this
codebase. Ranges are working time, not calendar time.

| Work item | Estimate |
| --- | --- |
| Orchestra front end: preprocessor, lexer, parser, type system, code generation | 6 to 12 months |
| Runtime: instrument instances, scheduler, k-rate and a-rate loops, buses, function tables | 6 to 12 months |
| Score reader, including the `sread` carry and ramp rules | 1 to 2 months |
| Audio and MIDI back ends, sound file IO | 1 to 3 months |
| 1,821 opcodes, at 2 to 4 finished and tested opcodes per day | 450 to 900 working days |
| Analysis utilities in `util/`, or a decision to drop them | 1 to 2 months |
| Differential test harness and bug fixing against it | 2 to 4 months |

Total: roughly 5 to 8 person-years. One person working ten hours a week needs more than twenty
calendar years. Two funded full time developers need three to four years, and during that time
they produce nothing a user can prefer over the C version.

## 4. Verdict

Do not rewrite Csound in Rust. Three findings decide it.

First, the opcode library is the product. The engine is about 150,000 lines and a rewrite of it is
imaginable. The 1,821 opcodes are not, because each one is a separate algorithm whose exact
behavior is documented only by its own source. Users depend on that exact behavior, because a
score renders audio and a changed rounding rule changes the sound.

Second, upstream is alive. This repository took 2,314 commits in the last twelve months from 35
authors over two years. A fork gives up that work. The gap grows every month, and the fork carries
the whole maintenance load alone.

Third, the stated goal does not need Rust. The core is already command line only. Pruning the
mobile, web, and binding directories reaches the "minimal" goal in one or two weeks of C and CMake
work, at no risk to audio correctness.

Rust still earns a place in this project, in three smaller roles: a safe command line front end, a
plugin toolkit so that new opcodes get written in Rust, and a test harness. Track A below covers
those. Track B is the honest version of the rewrite, kept as a separate project with a narrow
scope, for the case where the goal is the pleasure of building an engine rather than replacing
this one.

## 5. Track A: prune and add Rust at the edges (recommended)

Target: three to five months part time. Keeps the ability to merge from upstream.

### Phase A1: measure and protect (2 to 4 weeks)

- [ ] Build the current tree and record the exact CMake configuration that works on this machine.
- [ ] Write a renderer script that runs one `.csd` file to a `.wav` file with a fixed seed and a fixed sample rate.
- [ ] Run that script over all 835 files in `tests/soak/` and store the output as reference audio.
- [ ] Run it over `tests/regression/` and store that output too.
- [ ] Write the differential test harness. Differential testing means rendering the same input twice, with two builds, and comparing the samples.
- [ ] Set the comparison tolerance per file, and record which files are not reproducible because they use random numbers or wall clock time.
- [ ] Commit the reference hashes, not the audio files, and store the audio outside the repository.
- [ ] Add one command that reports how many files match the reference.

### Phase A2: prune the tree (1 to 2 weeks)

- [ ] Create the branch `prune/cli-only` from `develop`.
- [ ] Delete `iOS/`, `Android/`, `wasm/`, `Bela/`, `Daisy/`, and `Zynq/`.
- [ ] Delete `Java/`, `Python/`, and `Lisp/`.
- [ ] Delete `installer/` and the platform packaging under `platform/`.
- [ ] Remove the matching `add_subdirectory` calls and options from `CMakeLists.txt`.
- [ ] Remove the build options that only served the deleted targets, out of the 37 present.
- [ ] Decide on `po/` (3.3 MB of translations) and on the `USE_GETTEXT` option.
- [ ] Decide on `samples/` (5.5 MB), and move it out of the repository if you keep it.
- [ ] Run the Phase A1 harness. Make sure that the match count did not change.
- [ ] Record the new line count and build time, so that the gain is a number and not a feeling.

### Phase A3: Rust command line front end (2 to 4 weeks)

- [ ] Add a Cargo workspace at the top level, with the C library still built by CMake.
- [ ] Write a `csound-sys` crate that binds the 127 public functions in `include/csound.h`, using `bindgen`.
- [ ] Search crates.io for an existing Csound binding crate before you write this crate by hand.
- [ ] Write a safe `csound` wrapper crate that owns the instance handle and frees it on drop.
- [ ] Write the `csound-cli` binary with `clap`, and reproduce the flags in `Top/argdecode.c` that you actually use.
- [ ] Do not try to reproduce all 200 or more legacy flags. List the ones you drop.
- [ ] Route messages through the Rust side, so that output formatting stops going through C variadic calls.
- [ ] Run the Phase A1 harness through the new binary.

### Phase A4: Rust opcode plugin toolkit (4 to 8 weeks)

- [ ] Read `include/csdl.h` and write down the `csound_opcode_init` contract exactly.
- [ ] Write a `csound-opcode` crate that exposes one Rust trait for the init pass and the performance pass.
- [ ] Provide a macro that builds the `OENTRY` table and the module entry point from the trait implementations.
- [ ] Forbid allocation inside the performance pass, and document that rule in the crate.
- [ ] Port three existing opcodes of different shapes as proof. Pick one a-rate filter, one k-rate control opcode, and one that reads a function table.
- [ ] Compare the Rust ports against the C originals with the Phase A1 harness.
- [ ] Measure the performance of each Rust port against its C original at a block size of 32 and of 512.
- [ ] Write the guide that tells a contributor how to add a new opcode in Rust.

### Phase A5: keep the fork viable (ongoing)

- [ ] Add an upstream remote and a documented merge routine.
- [ ] Merge from upstream once a month, and run the harness after every merge.
- [ ] Record how long each merge takes. If a merge costs more than a day, reconsider the pruning.

## 6. Track B: a new Rust engine with a narrow scope (optional)

Take this track only if the goal is to build an engine, not to replace Csound. Target nine to
eighteen months part time for something a musician can use. Do not promise compatibility.

- [ ] Write down the subset first. Pick about 120 opcodes by counting real use across `tests/` and your own scores.
- [ ] Decide the language question. Either parse a documented subset of the orchestra language, or design a new input format.
- [ ] Do not copy the two stage Flex preprocessor. Use a plain recursive descent parser in Rust.
- [ ] Build the graph and the block loop first, with three opcodes, and get audio out of the speakers.
- [ ] Use `cpal` for audio, `midir` for MIDI, `symphonia` or `hound` for files, and `rustfft` for transforms.
- [ ] Set the sample type once. Csound defaults to double precision through `USE_DOUBLE`, and a single precision engine will not match it.
- [ ] Port opcodes in families, and port the test from `tests/soak/` with each one.
- [ ] State in the README that the output is not sample identical to Csound.
- [ ] Review after six months against one question: can you render a piece you care about?

## 7. Risks to hold in view

- Floating point behavior. The C build enables AVX2, `lrint`, and NaN preservation through options. A Rust port that changes any of them changes the audio.
- Undocumented semantics. Files such as `Engine/sread.c` and `Engine/insert.c` encode rules that no document states. The tests are the only specification.
- Real time constraints. The performance pass runs in the audio callback. Rust helps with memory safety and does not remove the ban on allocation and locking in that path.
- The 260 function pointers in `CSOUND` are the plugin ABI. Every third party opcode binary depends on their layout. Changing the struct breaks those binaries.
- License. Csound is LGPL 2.1 or later. A derived work carries that license, and a Rust rewrite that reads the C source for behavior is a derived work.
