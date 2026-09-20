#!/usr/bin/env bash
# Prune a Csound 7 checkout to a CLI-only tree for Linux and macOS.
#
# Removes platform ports, language bindings, packaging, translations and the
# two extra frontend programs, then removes the dead platform branches from
# the CMake files. Keeps the engine, every opcode, the analysis utilities in
# util/, and the test suite.
#
# Usage: prune.sh <repo-root> <path-to-prune_cmake.py>
set -euo pipefail

ROOT=${1:?usage: prune.sh <repo-root> <prune_cmake.py>}
PRUNER=${2:?usage: prune.sh <repo-root> <prune_cmake.py>}
cd "$ROOT"

say() { printf '\n== %s\n' "$*"; }

say "step 1: platform ports"
rm -rf iOS Android wasm Bela Daisy Zynq

say "step 2: language bindings"
rm -rf Java Python Lisp tests/python

say "step 3: packaging and CI images"
rm -rf installer platform DockerFiles vcpkg

say "step 4: translations"
rm -rf po

say "step 4b: self-referential symlink left by a code scanner"
rm -f _codeql_detected_source_root

say "step 5: extra frontend programs"
rm -rf Frontends/beats Frontends/debugger

say "step 5b: legacy score tools, Tcl widgets and dead CI"
rm -rf util1 util2 .github azure-pipelines.yml .travis.yml nsliders.tk

say "step 5c: unreferenced files at the repository root"
# longline.c and its file list are a line-length helper in no build.
# INSTALLING points at releases this fork does not publish.
# README.md.in is a template CMake used to overwrite README.md.
rm -f longline.c all_string_files INSTALLING README.md.in
rm -rf Release_Notes doc/How_to_Build_Csound_on_Windows.doc
# etc holds a 2012 ChangeLog and a .csoundrc sample. Csound 7 reads
# .csound7rc from $HOME or the current directory, never from etc.
rm -rf etc

say "step 5d: stop CMake overwriting README.md from its template"
python3 - <<'PY_INNER'
import pathlib
p = pathlib.Path("CMakeLists.txt")
text = p.read_text()
line = ("configure_file(${CMAKE_CURRENT_SOURCE_DIR}/README.md.in "
        "${CMAKE_CURRENT_SOURCE_DIR}/README.md)\n")
if line not in text:
    raise SystemExit("CMakeLists.txt: README configure_file rule not found")
p.write_text(text.replace(line, ""))
print("removed the README.md configure_file rule")
PY_INNER

say "step 6: audio back ends for other systems"
rm -f InOut/rtwinmm.c InOut/rtwasapi.c \
      InOut/rthaiku.cpp InOut/HaikuAudio.cpp InOut/HaikuMidi.cpp

say "step 7: drop subdirectories that no longer exist"
python3 - <<'PY'
import re, pathlib
p = pathlib.Path("CMakeLists.txt")
text = p.read_text()
for name in ("Python", "Bela", "po", "tests/python", "util1"):
    text = re.sub(r"^add_subdirectory\(%s\)[ \t]*\r?\n" % re.escape(name),
                  "", text, flags=re.M)
p.write_text(text)
print("removed add_subdirectory for Python, Bela, po, tests/python")
PY

say "step 8: stop writing version.h into the deleted Android tree"
python3 - <<'PY'
import pathlib
p = pathlib.Path("include/CMakeLists.txt")
text = p.read_text()
dead = ('# copy version.h for Android\n'
        'configure_file(${CMAKE_CURRENT_SOURCE_DIR}/version.h.in '
        '${CMAKE_SOURCE_DIR}/Android/CsoundAndroid/jni/version.h)\n')
if dead not in text:
    raise SystemExit("include/CMakeLists.txt: Android configure_file not found")
p.write_text(text.replace(dead, ""))
print("removed the Android version.h copy")
PY

say "step 9: drop the two extra frontend targets from Frontends/CMakeLists.txt"
python3 - <<'PY'
import pathlib, re
p = pathlib.Path("Frontends/CMakeLists.txt")
text = p.read_text()
# csbeats: its option, its dependency check, and its whole if block.
text = re.sub(r'^option\(BUILD_CSBEATS.*?\n', '', text, flags=re.M)
text = re.sub(r'^# CsBeats\n', '', text, flags=re.M)
text = re.sub(r'^check_deps\(BUILD_CSBEATS.*?\n', '', text, flags=re.M)
text = re.sub(r'\nif\(BUILD_CSBEATS\).*?\nendif\(\)\n', '\n', text, flags=re.S)
# csdebugger: the make_executable line and the comment above it.
text = re.sub(r'^\s*# debugger command line app\n', '', text, flags=re.M)
text = re.sub(r'^\s*make_executable\(csdebugger.*?\n', '', text, flags=re.M)
p.write_text(text)
for dead in ("BUILD_CSBEATS", "csdebugger", "beats"):
    if dead in text:
        raise SystemExit("Frontends/CMakeLists.txt still mentions %s" % dead)
print("removed csbeats and csdebugger")
PY

say "step 10: remove dead platform branches from the CMake files"
python3 "$PRUNER" \
    CMakeLists.txt \
    InOut/CMakeLists.txt \
    Opcodes/CMakeLists.txt \
    Frontends/CMakeLists.txt \
    util/CMakeLists.txt \
    include/CMakeLists.txt \
    tests/c/CMakeLists.txt \
    tests/commandline/CMakeLists.txt \
    tests/regression/CMakeLists.txt \
    tests/soak/CMakeLists.txt \
    util/SDIF/CMakeLists.txt

say "step 11: drop build options that no longer reach any code"
python3 - <<'PY'
import pathlib, re
dead_options = [
    "USE_VCPKG", "BARE_METAL", "CUSTOM_MALLOC", "BUILD_BELA",
    "BUILD_WASI_BROWSER", "USE_STATIC_DEPS", "BUILD_INSTALLER",
    "USE_GETTEXT",
]
p = pathlib.Path("CMakeLists.txt")
text = p.read_text()
removed = []
for name in dead_options:
    new, n = re.subn(r'^option\(%s\b.*?\n' % re.escape(name), '', text, flags=re.M)
    if n:
        removed.append(name)
        text = new
p.write_text(text)
print("removed options:", ", ".join(removed) or "none")
leftover = [o for o in dead_options if "option(%s" % o in text]
if leftover:
    raise SystemExit("options still declared: %s" % leftover)

# The gettext lookups are stranded now that the USE_GETTEXT block is gone.
for line in ("find_package(Intl)", "find_package(Gettext)"):
    text = text.replace(line + "\n", "")
text = re.sub(r'^check_deps\(USE_GETTEXT.*?\n', '', text, flags=re.M)
p.write_text(text)
print("removed the stranded gettext lookups")
PY

say "step 12: report"
printf 'CMakeLists.txt is now %s lines\n' "$(wc -l < CMakeLists.txt)"
echo "remaining references to deleted trees (should be empty):"
grep -rnE '(^|[^A-Za-z])(iOS|Android|wasm|Bela|Daisy|Zynq|Lisp|DockerFiles|vcpkg)/' \
    --include='CMakeLists.txt' --include='*.cmake' . || echo "  none"
