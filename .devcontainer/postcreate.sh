#!/usr/bin/env bash
# Runs once, when the container is created. It configures the build tree and
# says what to do next. It does not compile, because the first build takes a
# few minutes on a small machine and you may want other options first.
set -euo pipefail

cd "$(dirname "$0")/.."
workspace=$PWD

if [ -f build/CMakeCache.txt ]; then
    cached=$(sed -n 's/^CMAKE_HOME_DIRECTORY:INTERNAL=//p' build/CMakeCache.txt)
    if [ "$cached" != "$workspace" ]; then
        echo "build/ was configured for $cached, not for $workspace."
        echo "That cache comes from a build outside the container."
        echo "Run 'rm -rf build' and then '.devcontainer/postcreate.sh' again."
        exit 0
    fi
fi

cmake -S . -B build -G Ninja \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_C_COMPILER_LAUNCHER=ccache \
    -DCMAKE_CXX_COMPILER_LAUNCHER=ccache

cat <<'NEXT'

The build tree is configured. Next:

    ninja -C build           # compile the library, the program and the utilities
    csd render tests/soak/oscil.csd
    csd play tests/soak/oscil.csd

Run 'csd help' for the other subcommands.
NEXT
