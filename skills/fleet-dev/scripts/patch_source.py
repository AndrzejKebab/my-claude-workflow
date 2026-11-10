#!/usr/bin/env python3
"""Line-ending-safe literal replacement in source files.

Written because the same class of edit failed three times in one session: a
multi-line `str.replace` against a CRLF file silently did nothing, and a
`.replace` that did match left the file's line endings mixed. This does the
match on whitespace-normalised text, reports every site before touching disk,
and writes the file back with its ORIGINAL newline style.

Usage:
  patch_source.py <file> --find <literal> --replace <literal> [--all] [--apply]
  patch_source.py <file> --line <n> --insert-before <literal> [--apply]
  patch_source.py <file> --line <n> --delete [--apply]
  patch_source.py <file> --find-lines <path-to-file-with-text> --replace-lines <path> [--apply]

Without --apply it prints what it WOULD change and exits 0 (dry run by default,
because a source edit is not something to discover afterwards).
Exit codes: 0 changed or would change, 1 no match, 2 usage or IO error.

--find and the *_lines form accept the text as written on LF; matching is done
on text with \r removed, so a CRLF file is not a special case.
"""

import argparse
import io
import sys


def read_text(path):
    with io.open(path, encoding='utf-8', newline='') as handle:
        raw = handle.read()
    newline = '\r\n' if '\r\n' in raw else '\n'
    return raw, newline


def normalise(text, newline):
    """Bring inserted text to the file's newline style."""
    return text.replace('\r\n', '\n').replace('\n', newline)


def write_text(path, text):
    with io.open(path, 'w', encoding='utf-8', newline='') as handle:
        handle.write(text)


def find_sites(haystack, needle):
    flat_hay = haystack.replace('\r\n', '\n')
    flat_needle = needle.replace('\r\n', '\n')
    sites = []
    start = 0
    # Bounded: each hit advances start by at least one, so len(flat_hay) + 1 passes is the most possible.
    for _ in range(len(flat_hay) + 1):
        index = flat_hay.find(flat_needle, start)
        if index < 0:
            break
        sites.append(index)
        start = index + 1
    return sites


def flat_to_raw_offset(raw, flat_offset):
    """Translate an offset in the \\r-stripped text back to the raw text."""
    seen = 0
    for index, char in enumerate(raw):
        if seen == flat_offset:
            return index
        if char != '\r':
            seen += 1
    return len(raw)


def apply_literal(path, needle, replacement, replace_all, apply):
    raw, newline = read_text(path)
    flat = raw.replace('\r\n', '\n')
    flat_needle = needle.replace('\r\n', '\n')

    if flat_needle not in flat:
        print('no match in %s' % path)
        return 1

    count = flat.count(flat_needle)
    if count > 1 and not replace_all:
        print('refusing: %d matches in %s, pass --all to replace every one' % (count, path))
        return 2

    flat_replacement = replacement.replace('\r\n', '\n')
    flat_new = flat.replace(flat_needle, flat_replacement) if replace_all else \
        flat.replace(flat_needle, flat_replacement, 1)

    print('%s %d site(s) in %s' % ('replacing' if apply else 'would replace', count, path))
    if apply:
        write_text(path, normalise(flat_new, newline))
    return 0


def apply_lines(path, operand, apply):
    raw, newline = read_text(path)
    lines = raw.split(newline)
    _, text = read_text(operand)
    text = text.replace('\r\n', '\n')
    block = text.split('\n')
    if block and block[-1] == '':
        block.pop()
    index = int(operand_line)
    print('%s %d line(s) at %d in %s' % ('inserting' if apply else 'would insert', len(block), index, path))
    if apply:
        lines[index:index] = block
        write_text(path, newline.join(lines))
    return 0


def delete_line(path, line_number, apply):
    raw, newline = read_text(path)
    lines = raw.split(newline)
    if not 1 <= line_number <= len(lines):
        print('line %d out of range in %s (%d lines)' % (line_number, path, len(lines)))
        return 2
    print('%s line %d of %s: %s' % ('deleting' if apply else 'would delete', line_number, path,
                                    lines[line_number - 1].strip()[:100]))
    if apply:
        del lines[line_number - 1]
        write_text(path, newline.join(lines))
    return 0


def main(argv):
    parser = argparse.ArgumentParser(description='Line-ending-safe literal replacement in source files.')
    parser.add_argument('file')
    parser.add_argument('--find')
    parser.add_argument('--replace', default='')
    parser.add_argument('--all', action='store_true', help='replace every match, not just the first')
    parser.add_argument('--line', type=int, help='1-based line number for --delete')
    parser.add_argument('--insert-before', help='file whose text is inserted at --line')
    parser.add_argument('--delete', action='store_true', help='delete --line')
    parser.add_argument('--apply', action='store_true', help='write the change; default is a dry run')
    args = parser.parse_args(argv)

    global operand_line
    operand_line = args.line

    if args.delete:
        if not args.line:
            parser.error('--delete needs --line')
        return delete_line(args.file, args.line, args.apply)

    if args.insert_before:
        if not args.line:
            parser.error('--insert-before needs --line')
        return apply_lines(args.file, args.insert_before, args.apply)

    if args.find is None:
        parser.error('one of --find, --delete or --insert-before is required')

    return apply_literal(args.file, args.find, args.replace, args.all, args.apply)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
