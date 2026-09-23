# Development image for csound-min.
#
# The base image carries git, curl, zsh, sudo and a non-root "vscode" user.
# Everything added here is either a build dependency from docs/BUILD.md, a
# tool for working with the rendered audio, a debugger, or a released
# csound-min that runs before you build your own. libasound2-plugins is the
# ALSA plugin package. Without it, ALSA cannot use the pulse device that
# /etc/asound.conf names below.
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
    libasound2-plugins \
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

# A released csound-min goes into /usr/local, so that you can render .csd
# files before you build the engine. After 'ninja -C build', the csound
# wrapper in .devcontainer/bin runs your build instead.
#
# To move to a newer release, change the tag and both checksums. A checksum
# is in the .sha256 file next to the archive on the release page. An empty
# checksum means that the release has no archive for that processor, and you
# then build the engine in the container before you render.
ARG CSOUND_MIN_RELEASE=v7.0.0-min.3
ARG CSOUND_MIN_SHA256_AMD64=dcfcb04f18d075796ba090d679fe33040d1b985ce3fbf599d3d8800fb7bfcf9d
ARG CSOUND_MIN_SHA256_ARM64=f18636b406b39ea1fcffc95c5d288dfcd6c68295993aad8209d27f6a71ae66d3
RUN arch=$(dpkg --print-architecture) \
 && case "$arch" in \
        amd64) machine=x86_64;  sha=$CSOUND_MIN_SHA256_AMD64 ;; \
        arm64) machine=aarch64; sha=$CSOUND_MIN_SHA256_ARM64 ;; \
        *)     machine=;        sha= ;; \
    esac \
 && if [ -z "$sha" ]; then \
        echo "No csound-min release archive for $arch. Build it in the container."; \
    else \
        name=csound-min-${CSOUND_MIN_RELEASE#v}-linux-$machine \
     && curl -fsSL -o /tmp/$name.tar.gz \
        https://github.com/mjladd/csound-min/releases/download/$CSOUND_MIN_RELEASE/$name.tar.gz \
     && echo "$sha  /tmp/$name.tar.gz" | sha256sum -c - \
     && tar -xzf /tmp/$name.tar.gz -C /tmp \
     && cp -a /tmp/$name/bin /tmp/$name/lib /tmp/$name/include /tmp/$name/share /usr/local/ \
     && rm -rf /tmp/$name /tmp/$name.tar.gz \
     && ldconfig; \
    fi
