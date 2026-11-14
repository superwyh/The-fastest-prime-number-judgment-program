"""Import stdlib's open prime dataset into the compact lookup file."""

import argparse
from hashlib import sha256
import json
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.request import urlopen

from prime_check_script import DATABASE_PATH, HEADER, MAGIC


SOURCE_COMMIT = "631f9044ddae1ea938c4555960ab9ac6d71635a5"
SOURCE_URL = (
    "https://raw.githubusercontent.com/stdlib-js/datasets-primes-100k/"
    f"{SOURCE_COMMIT}/data/data.json"
)
SOURCE_SHA256 = "e45f6e05dd36a8ac1f4e9e7e3928c741af275aded4b60b65d94c08c35618f608"
SOURCE_COUNT = 100000
SOURCE_LIMIT = 1299709


def read_source(source_file=None):
    if source_file is None:
        with urlopen(SOURCE_URL, timeout=30) as response:
            raw = response.read()
    else:
        raw = Path(source_file).read_bytes()
    if sha256(raw).hexdigest() != SOURCE_SHA256:
        raise ValueError("Source checksum mismatch; the existing database was not changed.")
    primes = json.loads(raw)
    if (
        not isinstance(primes, list)
        or len(primes) != SOURCE_COUNT
        or primes[0] != 2
        or primes[-1] != SOURCE_LIMIT
        or any(type(value) is not int for value in primes)
        or any(a >= b for a, b in zip(primes, primes[1:]))
    ):
        raise ValueError("Invalid source dataset: expected the first 100,000 primes.")
    return primes


def build_database(path=DATABASE_PATH, limit=None, source_file=None):
    limit = SOURCE_LIMIT if limit is None else limit
    if type(limit) is not int or not 2 <= limit <= SOURCE_LIMIT:
        raise ValueError(f"limit must be an integer between 2 and {SOURCE_LIMIT}.")
    primes = read_source(source_file)

    bits = bytearray((limit + 8) // 8)
    count = 0
    for number in primes:
        if number > limit:
            break
        bits[number >> 3] |= 1 << (number & 7)
        count += 1

    path = Path(path)
    # Replace only after download, validation and conversion have all succeeded.
    temporary = None
    try:
        with NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", delete=False) as output:
            temporary = Path(output.name)
            output.write(HEADER.pack(MAGIC, limit) + bits)
        temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return count


def main():
    parser = argparse.ArgumentParser(description="Import stdlib's first 100,000 primes.")
    parser.add_argument("--limit", type=int, default=SOURCE_LIMIT, help=f"inclusive upper bound (default/max: {SOURCE_LIMIT})")
    parser.add_argument("--source-file", type=Path, help="import the pinned upstream data.json without downloading")
    args = parser.parse_args()
    try:
        count = build_database(limit=args.limit, source_file=args.source_file)
    except (OSError, ValueError) as error:
        parser.exit(2, f"Error: {error}\n")
    print(f"Wrote {count} primes through {args.limit} to {DATABASE_PATH} ({DATABASE_PATH.stat().st_size:,} bytes).")


if __name__ == "__main__":
    main()
