import argparse
from pathlib import Path

from edgedb_pydantic_codegen.generator import Generator

parser = argparse.ArgumentParser()
parser.add_argument('directory', type=Path)

if __name__ == '__main__':
    args = parser.parse_args()
    generator = Generator()
    generator.process_directory(args.directory)
