"""Check primality using the separate, memory-mapped primes.bin lookup table."""

import argparse
from functools import lru_cache
import mmap
from pathlib import Path
import struct


DATABASE_PATH = Path(__file__).resolve().with_name("primes.bin")
MAGIC = b"PRIMES01"
HEADER = struct.Struct("<8sI")  # Format identifier and inclusive upper bound.


@lru_cache(maxsize=1)
def _load_database(path):
    """Validate and map the database once; subsequent queries reuse the mapping."""
    with Path(path).open("rb") as database:
        header = database.read(HEADER.size)
        if len(header) != HEADER.size:
            raise ValueError("Invalid prime database: incomplete header.")
        magic, limit = HEADER.unpack(header)
        if magic != MAGIC or limit < 2:
            raise ValueError("Invalid prime database: unsupported header.")
        expected_size = HEADER.size + (limit + 8) // 8
        if database.seek(0, 2) != expected_size:
            raise ValueError("Invalid prime database: incorrect file size.")
        data = mmap.mmap(database.fileno(), 0, access=mmap.ACCESS_READ)
    return limit, data


def is_prime(n):
    """Return a bool; raise ValueError if n exceeds the database's upper bound."""
    if not isinstance(n, int):
        raise TypeError("n must be an integer.")
    if n < 2:
        return False
    limit, data = _load_database(DATABASE_PATH)
    if n > limit:
        raise ValueError(f"{n} is outside the database range (0..{limit}).")
    return bool(data[HEADER.size + (n >> 3)] & (1 << (n & 7)))


def check_prime(n):
    """Keep the original function's printed result and boolean return value."""
    result = is_prime(n)
    print(f"{n} is {'a prime' if result else 'not a prime'}")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description="Look up primality in primes.bin.")
    parser.add_argument("number", nargs="?", type=int, help="integer to check")
    args = parser.parse_args(argv)
    try:
        number = args.number if args.number is not None else int(input("Enter a number: "))
        check_prime(number)
    except FileNotFoundError:
        parser.exit(2, f"Prime database not found: {DATABASE_PATH}\nRun generate_primes.py to create it.\n")
    except (OSError, ValueError, EOFError) as error:
        parser.exit(2, f"Error: {error}\n")


if __name__ == "__main__":
    main()
