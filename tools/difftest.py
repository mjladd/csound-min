#!/usr/bin/env python3
"""Differential render test for Csound.

Renders a set of .csd files to headerless float samples and records a hash per
file. Run `record` against a known-good build, then `compare` against a changed
build. Files whose output differs between two runs of the same build are marked
nondeterministic and excluded from comparison.

Usage:
  difftest.py record  --csound BIN --plugin-dir DIR --suite DIR --out manifest.json
  difftest.py compare --csound BIN --plugin-dir DIR --suite DIR --baseline manifest.json
"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

RENDER_FLAGS = ["-d", "-m0", "-h", "-f"]


def sample_path(suite, extra):
    """Directories Csound searches for input audio and analysis files.

    Many csd files in tests/soak name an input such as "fox.wav" that lives
    in a sibling directory. Without those directories on the path the file
    fails to open and the test looks broken.
    """
    dirs = [suite]
    root = suite.parent.parent
    for candidate in (suite.parent / "commandline", suite.parent / "regression",
                      root / "samples", root / "tests" / "commandline",
                      root / "tests" / "regression"):
        if candidate.is_dir() and candidate not in dirs:
            dirs.append(candidate)
    for candidate in extra:
        candidate = Path(candidate).resolve()
        if candidate.is_dir() and candidate not in dirs:
            dirs.append(candidate)
    return os.pathsep.join(str(d) for d in dirs)


def render(csound, plugin_dir, csd, workdir, timeout, search):
    """Render one csd to raw float samples. Returns (status, sha256, nbytes)."""
    out = workdir / (csd.stem + ".raw")
    if out.exists():
        out.unlink()
    env = dict(os.environ)
    env["OPCODE7DIR64"] = str(plugin_dir)
    env["SSDIR"] = search
    env["SADIR"] = search
    env["SFDIR"] = str(workdir)
    env["INCDIR"] = search
    cmd = [str(csound)] + RENDER_FLAGS + ["-o", str(out), csd.name]
    try:
        proc = subprocess.run(
            cmd, cwd=str(csd.parent), env=env, timeout=timeout,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        )
    except subprocess.TimeoutExpired:
        return "timeout", None, 0
    if not out.exists():
        return "no-output(rc=%d)" % proc.returncode, None, 0
    data = out.read_bytes()
    out.unlink()
    if not data:
        return "empty", None, 0
    if proc.returncode != 0:
        return "rc=%d" % proc.returncode, hashlib.sha256(data).hexdigest(), len(data)
    return "ok", hashlib.sha256(data).hexdigest(), len(data)


def collect(suite, names):
    if names:
        listed = [suite / (n + ".csd") for n in names]
        return [p for p in listed if p.is_file()]
    return sorted(suite.glob("*.csd"))


def soak_list(suite):
    """Reuse the curated list in the suite's own runtests.py when present."""
    runner = suite / "runtests.py"
    if not runner.is_file():
        return None
    import re
    text = runner.read_text()
    match = re.search(r"testFiles\s*=\s*\[(.*?)^\]", text, re.S | re.M)
    if not match:
        return None
    names = []
    for line in match.group(1).splitlines():
        stripped = line.strip()
        if stripped.startswith('"'):
            names.append(stripped.strip(',').strip('"'))
    return names or None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["record", "compare"])
    ap.add_argument("--csound", required=True)
    ap.add_argument("--plugin-dir", required=True)
    ap.add_argument("--suite", required=True)
    ap.add_argument("--out", default="manifest.json")
    ap.add_argument("--baseline", default="manifest.json")
    ap.add_argument("--timeout", type=int, default=30)
    ap.add_argument("--all", action="store_true",
                    help="render every csd, not just the curated list")
    ap.add_argument("--sample-path", action="append", default=[],
                    metavar="DIR",
                    help="extra directory to search for input audio; "
                         "repeatable")
    args = ap.parse_args()

    suite = Path(args.suite).resolve()
    csound = Path(args.csound).resolve()
    plugin_dir = Path(args.plugin_dir).resolve()
    if not csound.is_file():
        sys.exit("no such binary: %s" % csound)

    names = None if args.all else soak_list(suite)
    files = collect(suite, names)
    if not files:
        sys.exit("no csd files found in %s" % suite)

    search = sample_path(suite, args.sample_path)
    print("sample search path:")
    for entry in search.split(os.pathsep):
        print("   ", entry)
    print()
    workdir = Path(tempfile.mkdtemp(prefix="difftest."))
    try:
        if args.mode == "record":
            manifest = {}
            for i, csd in enumerate(files, 1):
                s1, h1, n1 = render(csound, plugin_dir, csd, workdir,
                                    args.timeout, search)
                s2, h2, _ = render(csound, plugin_dir, csd, workdir,
                                   args.timeout, search)
                if s1 == "ok" and s2 == "ok" and h1 != h2:
                    status = "nondeterministic"
                elif s1 != s2:
                    status = "unstable"
                else:
                    status = s1
                manifest[csd.stem] = {"status": status, "sha256": h1, "bytes": n1}
                print("[%4d/%4d] %-40s %s" % (i, len(files), csd.stem, status),
                      flush=True)
            Path(args.out).write_text(json.dumps(manifest, indent=1, sort_keys=True))
            tally = {}
            for v in manifest.values():
                key = v["status"] if v["status"] in ("ok", "nondeterministic") else "failed"
                tally[key] = tally.get(key, 0) + 1
            print("\nrecorded %d files to %s" % (len(manifest), args.out))
            for k in sorted(tally):
                print("  %-18s %d" % (k, tally[k]))
            return

        baseline = json.loads(Path(args.baseline).read_text())
        compared = matched = 0
        mismatches = []
        skipped = []
        for csd in files:
            ref = baseline.get(csd.stem)
            if ref is None:
                skipped.append((csd.stem, "not in baseline"))
                continue
            if ref["status"] != "ok":
                skipped.append((csd.stem, "baseline " + ref["status"]))
                continue
            status, sha, nbytes = render(csound, plugin_dir, csd, workdir,
                                         args.timeout, search)
            compared += 1
            if status == "ok" and sha == ref["sha256"]:
                matched += 1
            else:
                mismatches.append((csd.stem, ref["status"], status,
                                   ref["bytes"], nbytes))
                print("MISMATCH %-40s %s -> %s" % (csd.stem, ref["status"], status),
                      flush=True)
        print("\ncompared %d, identical %d, mismatched %d, skipped %d"
              % (compared, matched, len(mismatches), len(skipped)))
        if mismatches:
            print("\nmismatched files:")
            for name, was, now, wasb, nowb in mismatches:
                print("  %-40s %s(%d bytes) -> %s(%d bytes)"
                      % (name, was, wasb, now, nowb))
            sys.exit(1)
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


if __name__ == "__main__":
    main()
