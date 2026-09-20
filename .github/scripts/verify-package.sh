#!/usr/bin/env bash
# Extracts a packaged archive somewhere else and proves that the copy runs.
# The check matters because the archive carries a library, a set of loadable
# back ends and the paths that join them.
#
#     .github/scripts/verify-package.sh dist/csound-min-7.0.0-linux-x86_64.tar.gz
set -euo pipefail

archive=${1:?usage: verify-package.sh ARCHIVE.tar.gz}
archive=$(cd "$(dirname "$archive")" && pwd)/$(basename "$archive")
scripts=$(cd "$(dirname "$0")" && pwd)

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

tar -xzf "$archive" -C "$work"
tree=$(find "$work" -maxdepth 1 -mindepth 1 -type d)
[ -x "$tree/bin/csound" ] || { echo "verify: no bin/csound in the archive" >&2; exit 1; }

cd "$tree"
# shellcheck disable=SC1091
. ./env.sh

echo "==> every linked library resolves"
if command -v ldd > /dev/null; then
    if ldd bin/csound | grep "not found"; then
        echo "verify: bin/csound has an unresolved library" >&2
        exit 1
    fi
else
    otool -L bin/csound
fi

echo "==> the program starts"
csound --version 2>&1 | head -n 3

echo "==> the program renders audio"
cat > sine.csd <<'CSD'
<CsoundSynthesizer>
<CsInstruments>
sr = 44100
ksmps = 32
nchnls = 1
0dbfs = 1
instr 1
  asig oscili 0.5, 440
  out asig
endin
</CsInstruments>
<CsScore>
i 1 0 1
e
</CsScore>
</CsoundSynthesizer>
CSD

# -s writes 16 bit samples, which keeps the check below simple. Csound
# blocks when a reader closes the pipe early, so the log goes to a file.
csound -W -s -o sine.wav sine.csd > render.log 2>&1 || {
    cat render.log
    echo "verify: the render failed" >&2
    exit 1
}

python3 "$scripts/check-audio.py" sine.wav

echo "==> the engine found its loadable back ends"
# The engine reports this when OPCODE7DIR64 points nowhere, and it then runs
# without the audio and MIDI back ends.
if grep -i "Error opening plugin directory" render.log; then
    echo "verify: the archive does not find its own plugin directory" >&2
    exit 1
fi

echo
echo "verify: $(basename "$archive") works from $tree"
