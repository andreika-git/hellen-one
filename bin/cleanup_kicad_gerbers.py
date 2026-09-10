#!/usr/bin/env python3
"""Remove obsolete KiCad 8 inner-layer exports when KiCad 10 replacements exist."""

import argparse
from pathlib import Path


def cleanup(directory, board, dry_run=False):
    for layer in (1, 2):
        current = directory / (board + "-In%d_Cu.g%d" % (layer, layer))
        obsolete = directory / (board + "-In%d_Cu.g%d" % (layer, layer + 1))
        if current.is_file() and obsolete.is_file():
            print("%s %s (replaced by %s)" % (
                "Would remove" if dry_run else "Removing", obsolete, current.name))
            if not dry_run:
                obsolete.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path, help="Gerber export directory")
    parser.add_argument("board", help="PCB basename, e.g. uaefi-pro")
    parser.add_argument("--dry-run", action="store_true", help="Only list obsolete files")
    args = parser.parse_args()
    if not args.directory.is_dir():
        parser.error("Gerber directory does not exist: %s" % args.directory)
    if not args.board or Path(args.board).name != args.board or args.board in (".", ".."):
        parser.error("board must be a basename without a directory")
    cleanup(args.directory, args.board, args.dry_run)


if __name__ == "__main__":
    main()
