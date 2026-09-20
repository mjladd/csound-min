# Build

This tree builds one library and one program, on Linux and on macOS. There is
no Windows, mobile, web or bare metal support.

## What you need

Flex and Bison are required, not optional. CMake runs them at build time to
generate the orchestra parser, and the generated files are not in the tree.

On Debian or Ubuntu:

```
sudo apt-get install -y cmake ninja-build flex bison \
    libsndfile1-dev libsamplerate0-dev libcurl4-openssl-dev \
    libasound2-dev libjack-jackd2-dev libpulse-dev portaudio19-dev
```

On macOS with Homebrew:

```
brew install cmake ninja flex bison libsndfile libsamplerate portaudio
```

Homebrew keeps its Flex and Bison out of the default path, because macOS ships
older versions. The top of `CMakeLists.txt` finds the Homebrew copies.

## Build it

```
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release
ninja -C build
```

The build produces 388 targets in about 12 seconds on 16 cores. The two
results that matter are `build/csound`, the program, and
`build/libcsound64.so`, the library. The other files are the analysis
utilities from `src/util/` and the loadable audio and MIDI back ends.

## Run it without installing

The program looks for its plugin back ends in an install directory that does
not exist yet, and prints a warning about it. Point `OPCODE7DIR64` at the
build directory instead:

```
export OPCODE7DIR64=$PWD/build
build/csound -o out.wav tests/soak/oscil.csd
```

To render without touching an audio device, always pass an output file with
`-o`. Many `.csd` files in `tests/` ask for `-odac` in their own
`<CsOptions>` block, and a command line flag overrides that.

## Options worth knowing

The build defaults suit a workstation. These are the options to reach for
first.

| Option | Default | Effect |
| --- | --- | --- |
| `USE_DOUBLE` | ON | Double precision samples. Turning it off builds the single precision library under a different name. |
| `BUILD_UTILITIES` | ON | Builds the standalone analysis programs, such as `pvanal` and `lpanal`. |
| `BUILD_MULTI_CORE` | ON | Builds the parallel performance scheduler. |
| `USE_AVX2` | ON | AVX2 instructions on x86-64. Turn it off for an older machine, or to compare audio against a machine without AVX2. |
| `BUILD_TESTS` | OFF | Builds the C unit tests. |
| `BUILD_PLUGINS` | OFF | Builds the optional opcodes as separate loadable plugins instead of linking them in. |

## Default options in a file

Csound 7 reads default command line options from a file called `.csound7rc`,
not `.csoundrc` as version 6 did. It looks in three places, in this order: the
path in `$CSOUND7RC`, then `$HOME/.csound7rc`, then `.csound7rc` in the current
directory. See `check_options` in `src/Top/main.c` line 48.

The file holds flags, and a line starting with a semicolon is a comment:

```
; suppress displays, colour-coded messages, no heartbeat, 16 bit WAV,
; real-time output through PortAudio, 128 frame software buffer
-d -m135 -H0 -s -W -o dac -+rtaudio=pa -b 128 -B 2048 --expression-opt
```

## Prove that a change did not alter the audio

`src/tools/difftest.py` renders a suite of `.csd` files and records one hash per
file. Record a baseline before you change anything:

```
python3 src/tools/difftest.py record \
    --csound build/csound --plugin-dir build \
    --suite tests/soak --out baseline.json
```

Then compare after the change:

```
python3 src/tools/difftest.py compare \
    --csound build/csound --plugin-dir build \
    --suite tests/soak --baseline baseline.json
```

The recording step renders each file twice and excludes the files that do not
reproduce, so random number opcodes do not raise false alarms. See
[../src/tools/README.md](../src/tools/README.md) for the details.

## If the build fails

Read the first error, not the last. The build is parallel, so the last error
on screen is rarely the first one to happen.

If CMake cannot find `sndfile.h`, you installed the runtime library and not
the development package. On Debian the difference is `libsndfile1` against
`libsndfile1-dev`.

If Bison reports a syntax error in `csound_orc.y`, make sure that your Bison
is version 3 or later. Version 2 cannot build this grammar.
