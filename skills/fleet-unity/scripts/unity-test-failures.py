#!/usr/bin/env python3
"""Read a Unity test results XML: totals, staleness, and the stack trace of each failure.

Why this exists: a batch run can report a result for a run that never collected your tests (a fresh
import makes `-testFilter` miss), and a process that stalled leaves the PREVIOUS run's XML behind.
So the file's own timestamp matters as much as its totals.

Usage
    python unity-test-failures.py Logs/EditMode-results.xml
    python unity-test-failures.py Logs/EditMode-results.xml --totals
    python unity-test-failures.py Logs/EditMode-results.xml --namespace VoxelGame.Tests --totals
    python unity-test-failures.py Logs/EditMode-results.xml --stale 15

`--stale MINUTES` exits 2 when the file is older than that, which is how you catch "I read an old
result". Failures plus their stack traces print by default; `--no-traces` prints names only.

Exit codes
    0  fine; 1  file missing; 2  file older than --stale.
"""

import argparse
import datetime
import os
import sys
import xml.etree.ElementTree as ElementTree


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("file", nargs="?", default="Logs/EditMode-results.xml")
    parser.add_argument("--totals", action="store_true", help="print the run's totals line first")
    parser.add_argument("--namespace", help="only count and print cases whose full name starts with this")
    parser.add_argument("--no-traces", action="store_true", help="print failing names, not stack traces")
    parser.add_argument("--stale", type=float, default=0, help="exit 2 when the file is older than this many minutes")
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print("no results file:", args.file)
        return 1

    modified = datetime.datetime.fromtimestamp(os.path.getmtime(args.file))
    age = (datetime.datetime.now() - modified).total_seconds() / 60.0
    root = ElementTree.parse(args.file).getroot()

    if args.totals:
        print("file: %s" % args.file)
        print("written: %s (%.1f min ago)" % (modified.strftime("%Y-%m-%d %H:%M:%S"), age))
        print("total=%s passed=%s failed=%s skipped=%s" % (
            root.get("total"), root.get("passed"), root.get("failed"), root.get("skipped")))

    failures = []
    for case in root.iter("test-case"):
        if case.get("result") != "Failed":
            continue
        name = case.get("fullname") or case.get("name") or "?"
        if args.namespace and not name.startswith(args.namespace):
            continue
        failures.append((name, case))

    for name, case in failures:
        print("=== %s" % name)
        if args.no_traces:
            continue
        for element in case.iter("stack-trace"):
            text = (element.text or "").strip()
            if text:
                for line in text.splitlines()[:12]:
                    print("   ", line)

    if args.namespace:
        outside = sum(1 for case in root.iter("test-case")
                      if case.get("result") == "Failed"
                      and not (case.get("fullname") or case.get("name") or "").startswith(args.namespace))
        print("\n%d failure(s) under %s; %d elsewhere" % (len(failures), args.namespace, outside))
    elif not failures:
        print("no failures")

    if args.stale and age > args.stale:
        print("\nWARNING: the file is %.0f min old, past the %.0f min limit — this is probably the "
              "previous run's result, not the one you just started" % (age, args.stale))
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
