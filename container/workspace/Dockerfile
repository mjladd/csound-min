# The workspace image: csound-min for people who write .csd files.
#
# It holds the released engine, the command line program, the analysis
# utilities, the csd helper and the tools to play and inspect audio. It holds
# no compiler and no engine source. To change the engine, use the dev
# container in .devcontainer instead.
#
# The build context is the repository root, and the release archives are in
# dist/. Build the image with .github/scripts/build-workspace-image.sh.
FROM mcr.microsoft.com/devcontainers/base:ubuntu-24.04

ARG DEBIAN_FRONTEND=noninteractive

# The run time libraries are the ones that the archive README lists, plus the
# ALSA plugin package and git-lfs. A music project keeps its samples in Git
# LFS, and neither a clone in the container nor actions/checkout works
# without that program. Without that package, ALSA cannot use the pulse device
# that /etc/asound.conf names below, and every render that opens an audio
# device fails.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libsndfile1 \
    libsamplerate0 \
    libcurl4t64 \
    libasound2t64 \
    libasound2-plugins \
    libjack-jackd2-0 \
    libpulse0 \
    libportaudio2 \
    alsa-utils \
    pulseaudio-utils \
    sox \
    libsox-fmt-all \
    python3 \
    git-lfs \
 && rm -rf /var/lib/apt/lists/*

# The image renders to a file by default. When you mount the host audio
# socket, these two files let the ALSA and PulseAudio clients find it.
RUN printf 'pcm.!default pulse\nctl.!default pulse\n' > /etc/asound.conf \
 && printf 'default-server = unix:/run/user/1000/pulse/native\nautospawn = no\ndaemon-binary = /bin/true\n' \
    > /etc/pulse/client.conf

# The archives of every processor go in, and the one for this processor gets
# installed. The layout of the archive matches /usr/local.
COPY dist/*.tar.gz /tmp/archives/
RUN case "$(dpkg --print-architecture)" in \
        amd64) machine=x86_64 ;; \
        arm64) machine=aarch64 ;; \
        *) echo "no csound-min archive for $(dpkg --print-architecture)" >&2; exit 1 ;; \
    esac \
 && set -- /tmp/archives/*-linux-$machine.tar.gz \
 && if [ $# -ne 1 ]; then echo "dist/ must hold one archive for $machine, and it holds $#" >&2; exit 1; fi \
 && archive=$1 \
 && name=$(basename "$archive" .tar.gz) \
 && tar -xzf "$archive" -C /tmp \
 && cp -a /tmp/$name/bin /tmp/$name/lib /tmp/$name/include /tmp/$name/share /usr/local/ \
 && ldconfig \
 && rm -rf /tmp/archives /tmp/$name \
 && csound --version 2>&1 | head -n 2

COPY .devcontainer/bin/csd /usr/local/bin/csd

LABEL org.opencontainers.image.source=https://github.com/mjladd/csound-min \
      org.opencontainers.image.description="Csound engine and tools for writing .csd files, without the compiler." \
      org.opencontainers.image.licenses=LGPL-2.1-or-later
