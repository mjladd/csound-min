# Development container

The container holds everything the build needs, so you do not install audio
libraries on your own machine. It targets two kinds of work: changing the C
engine, and writing `.csd` files and listening to them.

## What is inside

The image is Ubuntu 24.04 with the build dependencies from
[../docs/BUILD.md](../docs/BUILD.md): CMake, Ninja, Flex, Bison, libsndfile,
libsamplerate, libcurl, and the ALSA, JACK, PulseAudio, PipeWire and
PortAudio development packages. It also carries `gdb`, `ccache`, `python3`
for `src/tools/difftest.py`, and `sox` to inspect and play the rendered audio.

## Start it

Open the folder in VS Code and run **Dev Containers: Reopen in Container**.
VS Code offers two configurations:

- **csound-min**, the default. The container reaches no audio device. You
  render to a file and play the file on the host. This works on every host,
  including macOS, Windows and GitHub Codespaces.
- **csound-min (host audio)**. The container plays through the speakers of
  the host. It needs a Linux host that runs PulseAudio or PipeWire. It fails
  to start on any other host.

The first start builds the image, which takes a few minutes. After that,
`postcreate.sh` configures the build tree and prints the next commands. It
does not compile. Run `ninja -C build` yourself.

## The csd helper

The container puts `.devcontainer/bin/csd` and the `build` directory on your
PATH, and it sets `OPCODE7DIR64` to the build tree. The engine then finds its
loadable back ends without an install.

```
csd build                      # compile everything
csd render tests/soak/oscil.csd
csd play tests/soak/oscil.csd
csd live tests/soak/oscil.csd  # straight to the audio device
csd info build/renders/oscil.wav
csd opcodes oscil              # list the opcodes that match
csd difftest                   # compare the renders against the baseline
```

`csd render` and `csd play` write to `build/renders`. They pass `-o`, which
overrides the `-odac` that most files in `tests/` carry in their own
`<CsOptions>` block. Without that override, a render tries to open an audio
device.

You can also call the program directly:

```
ninja -C build
csound -W -o out.wav tests/soak/oscil.csd
```

## Hear the audio

In the default configuration, render to a file and play it on the host. The
workspace is a bind mount, so the file is already on the host disk.

In the host audio configuration, `csd play` and `csd live` reach the speakers.
The configuration passes `--device=/dev/snd` for ALSA and mounts the
PulseAudio socket of your login session at `/run/user/1000/pulse`. The
container user is uid 1000, which is why the path inside is `1000` whatever
your own uid is.

If playback fails with an authentication error, your sound server asks for a
cookie. Add this line to `runArgs` in `.devcontainer/audio/devcontainer.json`:

```
"--volume=${localEnv:HOME}/.config/pulse/cookie:/home/vscode/.config/pulse/cookie:ro"
```

If the container fails to start, your host runs no PulseAudio or PipeWire
socket. Use the default configuration instead.

## A build tree from outside the container

The workspace is a bind mount, so a `build` directory from a build on the
host is visible inside the container. CMake records absolute paths in
`build/CMakeCache.txt`, and those paths differ between the host and the
container. `postcreate.sh` detects this, prints a message and stops. Run
`rm -rf build` and then `.devcontainer/postcreate.sh` again.
