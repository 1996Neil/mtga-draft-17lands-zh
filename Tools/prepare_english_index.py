#!/usr/bin/env python3
"""Prepare a minimal local English identity index from your own original game DB.

Run before applying localization, or use an unmodified DB you already own.
The source is read-only. No rules text, flavor text or UI strings are exported.
"""
import argparse
from contextlib import closing
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import constants
from src.arena_english import connect_readonly, prepare_index


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("database", type=Path, help="Unmodified English Arena card database")
    parser.add_argument("--output", type=Path,
                        default=Path(constants.BASE_DIR) / "Names/english-index.json")
    args = parser.parse_args()
    if args.database.resolve() == args.output.resolve():
        parser.error("The output must not overwrite the source database")
    with closing(connect_readonly(args.database)) as connection:
        result = prepare_index(connection, args.output)
    print(f"Prepared {len(result['localizations'])} English identities locally: {args.output}")


if __name__ == "__main__":
    main()
