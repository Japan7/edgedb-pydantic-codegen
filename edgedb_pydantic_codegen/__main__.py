import argparse
import warnings
from pathlib import Path

from edgedb_pydantic_codegen.generator import Generator


def cli():
    warnings.simplefilter("default")
    warnings.warn(
        "If you have migrated to `gel`, please use `gel-pydantic-codegen` instead. "
        "The `edgedb-pydantic-codegen` package is deprecated and is no longer maintained.",
        DeprecationWarning,
    )
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
