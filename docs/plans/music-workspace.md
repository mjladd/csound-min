# Plan: a container for Csound music projects

Status: proposal, 2026-09-22.

## Goal

A person who writes Csound music keeps their pieces, samples and analysis
files in their own Git repository. They open that repository in a dev
container and render audio with csound-min. They never clone or build the
engine.

The dev container in this repository stays as it is. It remains the place to
change the engine.

## The design in short

This repository publishes a second container image, the workspace image. It
holds the released csound-min, the `csd` helper and the tools to play and
inspect audio. It holds no compiler and no engine source.

A template repository shows the layout of a music project. Its
`devcontainer.json` names the workspace image by version, so a project opens
in seconds and renders with a known engine.

Csound finds files through environment variables. The template sets them to
folders in the project, so a piece names a sample as `"kick.wav"` and not by
a full path.

| Variable | Csound reads it for | Template folder |
| --- | --- | --- |
| `SSDIR` | sound files that opcodes such as `diskin2` read | `samples/` |
| `SADIR` | analysis files, for example `pvanal` output | `analysis/` |
| `INCDIR` | files that `#include` names | `include/` |

The template does not set `SFDIR`, the output folder. If `SFDIR` is set,
csound writes a relative `-o` path into that folder, and the `csd` helper
already chooses the output path.

## Part 1: work in csound-min

Do the steps in this order. Each step ends with a test.

### 1. Make the csd helper work outside this repository

The helper finds the build tree and the render folder relative to its own
location in `.devcontainer/bin`. In the workspace image it is in
`/usr/local/bin`, so that rule fails.

1. Give the helper two modes, engine mode and workspace mode. If the helper
   runs from a csound-min checkout, it uses engine mode. If
   `CSOUND_BUILD_DIR` is set, it also uses engine mode. In all other cases,
   it uses workspace mode.
2. In workspace mode, run `/usr/local/bin/csound` and write renders to
   `renders/` in the top folder of the current Git repository. If there is no
   Git repository, write to `renders/` in the current folder.
3. In workspace mode, make `csd build` and `csd difftest` stop with a message
   that they need a csound-min checkout.
4. Add `csd analyze`. If the project has the script `analysis/make.sh`, the
   command runs it.

Test: in engine mode, `csd render tests/soak/oscil.csd` writes to
`build/renders` as before. In an empty folder, the same command with a copied
`.csd` file writes to `./renders`.

### 2. Add the workspace image

Add `container/workspace/Dockerfile`. Base it on
`mcr.microsoft.com/devcontainers/base:ubuntu-24.04`, the same base as the
engine container.

1. Install the runtime libraries that the release README lists, and `sox`,
   `alsa-utils`, `pulseaudio-utils` and `python3`.
2. Install `libasound2-plugins`. The engine container lacks it, and without
   it ALSA cannot use the `pulse` device that `/etc/asound.conf` names.
3. Copy the same `/etc/asound.conf` and `/etc/pulse/client.conf` as the
   engine container.
4. Copy the release archive from the build context and install it into
   `/usr/local`, then run `ldconfig`. Do not download it. The release workflow
   builds the archive in the same run.
5. Copy `.devcontainer/bin/csd` to `/usr/local/bin/csd`.
6. Add labels for the source repository and the csound-min version.

Also add `libasound2-plugins` to `.devcontainer/Dockerfile`. This fixes
`csd difftest` for test files that open audio input.

Test: build the image from a local `package.sh` archive. In the image,
`csound --version` prints the release version, and `csd render` of a copied
test file writes a file with a peak level above zero.

### 3. Build Linux archives for ARM

The release has a Linux x86_64 archive only. On a Mac with Apple silicon,
Docker runs ARM containers, and the image then has no csound.

1. Add a `linux-arm64` job to `.github/workflows/release.yml`. Run it on the
   `ubuntu-24.04-arm` runner, in the `ubuntu:22.04` container, with the same
   steps as the `linux` job.
2. Attach its archive to the release.
3. Change the install step in `.devcontainer/Dockerfile` to pick the archive
   for the processor and to pin one checksum for each archive.

Test: the release has an `aarch64` archive, and `verify-package.sh` passes on
it.

### 4. Publish the image

1. Add an `image` job to `release.yml` that needs the two Linux jobs. It
   downloads their archives, builds the image for `linux/amd64` and
   `linux/arm64`, and pushes it to
   `ghcr.io/mjladd/csound-min-workspace`.
2. Tag the image with the release version without the `v`, for example
   `7.0.0-min.3`, and with `latest`.
3. Give the workflow `packages: write`.
4. Before the image job pushes, run a render of `tests/soak/oscil.csd` in the
   image and check it with `.github/scripts/check-audio.py`.
5. Make the package public on its GitHub package page. The repository
   must be public too, because a public image of a private repository is
   confusing to users.

Test: on a machine without a GitHub login,
`docker pull ghcr.io/mjladd/csound-min-workspace:7.0.0-min.3` works.

### 5. Make the template repository

Create `mjladd/csound-min-template` and mark it as a template on the GitHub
page of the repository.

```
.devcontainer/
  devcontainer.json          default: render to a file
  audio/devcontainer.json    host audio, as in csound-min
.gitattributes               Git LFS rules for samples/
.gitignore                   renders/
pieces/hello.csd             a first piece that reads a sample
samples/README.md            where samples go, and how LFS stores them
analysis/make.sh             makes every analysis file from samples/
include/                     shared instrument code for #include
README.md                    the steps in part 2
```

The `devcontainer.json`:

```jsonc
{
  "name": "csound project",
  "image": "ghcr.io/mjladd/csound-min-workspace:7.0.0-min.3",
  "remoteEnv": {
    "SSDIR": "${containerWorkspaceFolder}/samples",
    "SADIR": "${containerWorkspaceFolder}/analysis",
    "INCDIR": "${containerWorkspaceFolder}/include"
  },
  "customizations": {
    "vscode": {
      "extensions": ["kunstmusik.csound-vscode-plugin"]
    }
  }
}
```

The `<CsOptions>` block of `hello.csd` must not contain `-odac`. The template
renders to a file by default.

Test: create a repository from the template, open it in a dev container, and
run `csd render pieces/hello.csd`. Do the same in a GitHub Codespace.

### 6. Keep the template current

1. Add a step to the release workflow that opens a pull request on the
   template to change the image tag. Or change the tag by hand after each
   release.
2. Add a workflow to the template that renders every file in `pieces/` in the
   image. A user gets this workflow with the template, and it then renders
   their own pieces on each push.

### 7. Documentation

1. Add a section to `.devcontainer/README.md` that names the workspace image
   and the template, and says which container to use for which work.
2. Add the workspace image to the release notes that `release.yml` writes.

## Part 2: work for a user

### Start a project

1. On GitHub, open `mjladd/csound-min-template` and click Use this template.
2. Clone your new repository.
3. Open the folder in VS Code and run Dev Containers: Reopen in Container. Or
   open the repository in a Codespace.
4. Run `csd render pieces/hello.csd`, and play `renders/hello.wav` on your
   computer.

If your computer is a Linux machine with PulseAudio or PipeWire, pick the
host audio configuration. Then `csd play` and `csd live` reach your speakers.

### Add samples

1. Put sound files in `samples/`.
2. In a piece, name the file without a folder: `diskin2 "kick.wav"`. Csound
   finds it through `SSDIR`.
3. If a sound file is larger than a few megabytes, store it with Git LFS
   (large file storage for Git). The template `.gitattributes` already sends
   `.wav`, `.aif` and `.flac` files in `samples/` to LFS. Run
   `git lfs install` once on your computer.

GitHub limits the LFS storage and download volume of each account. If your
samples are larger than that limit, keep them outside Git and mount them.
Add this to `devcontainer.json`, and set `SSDIR` to the mount point:

```jsonc
"mounts": [
  "source=${localEnv:HOME}/csound-samples,target=/samples,type=bind,readonly"
]
```

The folder must exist on your computer, or the container does not start.

### Make analysis files

Analysis files, such as `pvanal` output, come from your samples. Make them
again from the samples, and do not edit them by hand.

1. Add one line for each file to `analysis/make.sh`, for example
   `pvanal samples/voice.wav analysis/voice.pvx`.
2. Run `csd analyze`.
3. In a piece, name the file without a folder: `pvsfread "voice.pvx"`. Csound
   finds it through `SADIR`.

If an analysis file takes a long time to make, commit it. Otherwise, add it
to `.gitignore` and run `csd analyze` after each clone.

### Move to a newer csound-min

1. Change the image tag in `.devcontainer/devcontainer.json`.
2. Run Dev Containers: Rebuild Container.
3. Render your pieces and listen for changes.

### Change the engine

If you want to change csound-min itself, work in the csound-min repository
and its own dev container. You can render a piece from your project with your
engine build. Copy the piece into the csound-min folder, or add a bind mount
of your project folder to the csound-min `devcontainer.json`. Do not commit
that mount.

## Open questions

1. Is `csound-min-workspace` the right image name?
2. Does the release workflow update the template, or do you update it by
   hand?
3. Does the template use Git LFS for samples by default, or a mount?
4. Does the image carry only the program and the analysis utilities, or the
   whole release archive? The plan installs the whole archive, because it is
   small.
