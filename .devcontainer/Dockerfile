# Development image for csound-min.
#
# The base image carries git, curl, zsh, sudo and a non-root "vscode" user.
# Everything added here is either a build dependency from docs/BUILD.md, a
# tool for working with the rendered audio, or a debugger.
FROM mcr.microsoft.com/devcontainers/base:ubuntu-24.04

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ccache \
    cmake \
    ninja-build \
    pkg-config \
    flex \
    bison \
    gdb \
    python3 \
    libsndfile1-dev \
    libsamplerate0-dev \
    libcurl4-openssl-dev \
    libasound2-dev \
    libjack-jackd2-dev \
    libpulse-dev \
    libpipewire-0.3-dev \
    portaudio19-dev \
    alsa-utils \
    pulseaudio-utils \
    sox \
    libsox-fmt-all \
 && rm -rf /var/lib/apt/lists/*

# The container renders to a file by default. When you mount the host audio
# socket, these two files let the ALSA and PulseAudio clients find it.
# See .devcontainer/README.md for the mount.
RUN printf 'pcm.!default pulse\nctl.!default pulse\n' > /etc/asound.conf \
 && printf 'default-server = unix:/run/user/1000/pulse/native\nautospawn = no\ndaemon-binary = /bin/true\n' \
    > /etc/pulse/client.conf
