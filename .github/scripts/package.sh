#!/usr/bin/env bash
# Builds csound-min and packs the result into a tar.gz that a user can
# download, extract and run. It runs on Linux and on macOS, in CI and on your
# own machine:
#
#     .github/scripts/package.sh
#
# The archive lands in dist/. Run .github/scripts/verify-package.sh on it to
# prove that the extracted copy renders audio.
set -euo pipefail

root=$(cd "$(dirname "$0")/../.." && pwd)
build=$root/build-package
stage=$root/build-package/stage
out=$root/dist
version=""
jobs=""

while [ $# -gt 0 ]; do
    case $1 in
        --build-dir) build=$2; stage=$2/stage; shift 2 ;;
        --out)       out=$2; shift 2 ;;
        --version)   version=$2; shift 2 ;;
        --jobs)      jobs=$2; shift 2 ;;
        *) echo "package.sh: unknown argument '$1'" >&2; exit 2 ;;
    esac
done

# A tagged build takes its name from the tag. Any other build carries the
# engine version and the commit it came from.
if [ -z "$version" ]; then
    if ! version=$(git -C "$root" describe --tags 2>/dev/null); then
        if commit=$(git -C "$root" rev-parse --short HEAD 2>/dev/null); then
            version=7.0.0-$commit
        else
            version=7.0.0
        fi
    fi
fi
version=${version#v}

arch=$(uname -m)
case $(uname -s) in
    Linux)  os=linux ;;
    Darwin) os=macos ;;
    *) echo "package.sh: this script builds on Linux and macOS only." >&2; exit 1 ;;
esac

name=csound-min-$version-$os-$arch
prefix=/usr/local

configure=(
    cmake -S "$root" -B "$build" -G Ninja
    -DCMAKE_BUILD_TYPE=Release
    -DCMAKE_INSTALL_PREFIX="$prefix"
    # A downloaded binary runs on machines older than the build machine, so
    # it cannot carry instructions that those machines lack.
    -DUSE_AVX2=OFF
)

if [ "$os" = macos ]; then
    # The library is a framework on macOS. Install it under the prefix, so
    # that the archive holds it and the rpath rewrite below can reach it.
    configure+=(-DCS_FRAMEWORK_DEST="$prefix/Frameworks")
fi

echo "==> configure"
rm -rf "$build"
"${configure[@]}"

echo "==> build"
if [ -n "$jobs" ]; then
    ninja -C "$build" -j "$jobs"
else
    ninja -C "$build"
fi

echo "==> install into a staging tree"
rm -rf "$stage"
DESTDIR="$stage" cmake --install "$build" > /dev/null

tree=$stage$prefix
[ -x "$tree/bin/csound" ] || { echo "package.sh: no csound in the staging tree" >&2; exit 1; }

if [ "$os" = macos ]; then
    echo "==> make the archive relocatable"
    # CMake writes the staging framework path into every executable as an
    # rpath. Replace it with a path relative to the executable, so that the
    # archive runs from wherever the user extracts it. install_name_tool
    # invalidates the signature, so sign each file again.
    relocate() {
        local file=$1 rpath=$2
        install_name_tool -add_rpath "$rpath" "$file" 2>/dev/null || true
        install_name_tool -delete_rpath "$prefix/Frameworks" "$file" 2>/dev/null || true
        codesign --force --sign - "$file" 2>/dev/null || true
    }
    for file in "$tree"/bin/*; do
        [ -f "$file" ] || continue
        relocate "$file" "@executable_path/../Frameworks"
    done
    # From Frameworks/CsoundLib64.framework/Versions/7.0/Resources/Opcodes64
    # back up to Frameworks is five directories.
    for file in "$tree"/Frameworks/*.framework/Versions/*/Resources/Opcodes*/*; do
        [ -f "$file" ] || continue
        relocate "$file" "@loader_path/../../../../.."
    done
fi

echo "==> add the run and install instructions"
cp "$root/docs/COPYING" "$tree/COPYING"
sed "s/@VERSION@/$version/g; s/@OS@/$os/g; s/@ARCH@/$arch/g" \
    "$root/.github/scripts/package-README.md" > "$tree/README.md"

if [ "$os" = macos ]; then
    plugin_dir='$root/Frameworks/CsoundLib64.framework/Versions/7.0/Resources/Opcodes64'
else
    plugin_dir='$root/lib/csound/plugins64-7.0'
fi

cat > "$tree/env.sh" <<ENV
# Source this file to run csound-min from this directory, without installing
# it:
#
#     . ./env.sh
#     csound -W -o out.wav your.csd
#
root=\$(cd "\$(dirname "\${BASH_SOURCE[0]:-\$0}")" && pwd)
PATH="\$root/bin:\$PATH"
OPCODE7DIR64="$plugin_dir"
export PATH OPCODE7DIR64
ENV

echo "==> pack"
mkdir -p "$out"
rm -rf "$stage/$name"
mv "$tree" "$stage/$name"
tar -czf "$out/$name.tar.gz" -C "$stage" "$name"

if command -v shasum > /dev/null; then
    (cd "$out" && shasum -a 256 "$name.tar.gz" > "$name.tar.gz.sha256")
else
    (cd "$out" && sha256sum "$name.tar.gz" > "$name.tar.gz.sha256")
fi

echo
echo "$out/$name.tar.gz"
cat "$out/$name.tar.gz.sha256"
