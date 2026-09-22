#!/usr/bin/env bash
# Builds the workspace image from the release archives in dist/, and proves
# that the image renders audio.
#
#     .github/scripts/package.sh                     # writes dist/
#     .github/scripts/build-workspace-image.sh
#
# The image holds the archive for the processor of the machine that builds
# it. The release workflow builds for two processors at once with buildx.
set -euo pipefail

root=$(cd "$(dirname "$0")/../.." && pwd)
tag=${1:-csound-min-workspace:local}

ls "$root"/dist/*-linux-*.tar.gz > /dev/null

echo "==> build $tag"
docker build -t "$tag" -f "$root/container/workspace/Dockerfile" "$root"

echo "==> the image renders audio"
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
cp "$root/tests/soak/oscil.csd" "$work/"
cp "$root/.github/scripts/check-audio.py" "$work/"

docker run --rm --user "$(id -u):$(id -g)" -v "$work:/work" -w /work "$tag" bash -c '
    set -e
    csd render oscil.csd
    python3 check-audio.py renders/oscil.wav
    csd info renders/oscil.wav | tail -2
    echo "==> csd build stops, because the image has no engine source"
    if csd build > build.log 2>&1; then
        echo "build-workspace-image: csd build had to stop and did not" >&2
        exit 1
    fi
    cat build.log
'

echo
echo "$tag works"
