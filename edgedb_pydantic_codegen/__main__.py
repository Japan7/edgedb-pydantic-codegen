import argparse
from pathlib import Path

from edgedb_pydantic_codegen.generator import Generator


def cli():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "directory",
        type=Path,
        help="Directory to process recursively",
    )
    parser.add_argument(
        "--no-parallel",
        dest="parallel",
        action="store_false",
        default=True,
        help="Don't process files in parallel",
    )
    args = parser.parse_args()
    generator = Generator()
    generator.process_directory(args.directory, parallel=args.parallel)


if __name__ == "__main__":
    cli()
