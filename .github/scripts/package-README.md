# csound-min @VERSION@ for @OS@ on @ARCH@

This archive holds the Csound engine and the command line program from
https://github.com/mjladd/csound-min, built from source. It is a personal
learning fork of Csound 7.0.0 beta. For a supported install, take a release
from https://github.com/csound/csound/releases instead.

## What you need on the machine

The program loads the audio and MIDI libraries at run time, so install them
first.

On Debian or Ubuntu:

```
sudo apt-get install -y libsndfile1 libsamplerate0 libcurl4 \
    libasound2t64 libjack-jackd2-0 libpulse0 libportaudio2
```

On an older Debian or Ubuntu, the ALSA package is `libasound2`.

On macOS with Homebrew:

```
brew install libsndfile libsamplerate portaudio
```

## Run it from this directory

```
. ./env.sh
csound -W -o out.wav your.csd
```

`env.sh` puts `bin` on your PATH and sets `OPCODE7DIR64`, the variable that
tells the engine where its loadable back ends are. Source it again in every
new shell, or install the files as below.

## Install it

The archive matches the layout of `/usr/local`, so copy it there:

```
sudo cp -a bin lib include share /usr/local/     # Linux
sudo cp -a bin Frameworks include share /usr/local/   # macOS
```

After that, `csound` works in any shell with no variable set, because the
program looks for its back ends under `/usr/local` by default.

## First render

```
cat > sine.csd <<'CSD'
<CsoundSynthesizer>
<CsInstruments>
sr = 44100
ksmps = 32
nchnls = 2
0dbfs = 1
instr 1
  asig oscili 0.6, 440
  outs asig, asig
endin
</CsInstruments>
<CsScore>
i 1 0 2
e
</CsScore>
</CsoundSynthesizer>
CSD
csound -W -o sine.wav sine.csd
```

To play through the speakers instead of writing a file, pass `-odac`.

## What is in here

- `bin/csound`, the program, and the analysis utilities such as `pvanal`.
- The library, and the loadable audio and MIDI back ends.
- `include/csound`, the C headers, and the pkg-config and CMake files that
  let another program build against the library.
- `share/samples`, the HRTF data that the `hrtf` opcodes read.

The build has AVX2 turned off, so the program runs on older processors. A
build for your own machine can be faster. See `docs/BUILD.md` in the
repository.

Csound is free software under the GNU Lesser General Public License, version
2.1 or later. The full text is in `COPYING`.
