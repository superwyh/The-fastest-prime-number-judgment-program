import contextlib
import io
from math import isqrt
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import prime_check_script as prime
import generate_primes as dataset
from generate_primes import build_database


SCRIPT = Path(prime.__file__).resolve()


def reference_is_prime(number):
    if number < 2:
        return False
    if number % 2 == 0:
        return number == 2
    return all(number % divisor for divisor in range(3, isqrt(number) + 1, 2))


class PrimeLookupTests(unittest.TestCase):
    def test_entire_shipped_database_against_trial_division(self):
        self.assertEqual(prime.DATABASE_PATH.stat().st_size, 162476)
        limit, _ = prime._load_database(prime.DATABASE_PATH)
        self.assertEqual(limit, 1299709)
        count = 0
        for number in range(limit + 1):
            actual = prime.is_prime(number)
            self.assertEqual(actual, reference_is_prime(number), number)
            count += actual
        self.assertEqual(count, 100000)

    def test_boundaries_and_invalid_input(self):
        for number in (-100, -1, 0, 1, 300000, 1000000, 1299708):
            self.assertFalse(prime.is_prime(number))
        for number in (2, 3, 7, 257, 299993, 1000003, 1299709):
            self.assertTrue(prime.is_prime(number))
        with self.assertRaisesRegex(ValueError, "outside the database range"):
            prime.is_prime(1299710)
        for value in (2.0, "2", None):
            with self.assertRaises(TypeError):
                prime.is_prime(value)

    def test_original_print_and_return_contract(self):
        for number, expected in ((97, True), (100, False)):
            with contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertIs(prime.check_prime(number), expected)
            self.assertEqual(output.getvalue(), f"{number} is {'a prime' if expected else 'not a prime'}\n")

    def test_repeated_queries_reuse_mapping(self):
        prime.is_prime(97)
        with patch.object(Path, "open", side_effect=AssertionError("Database reopened")):
            self.assertFalse(prime.is_prime(100))
            self.assertTrue(prime.is_prime(299993))

    def test_generator_across_byte_boundaries(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "primes.bin"
            for limit in (2, 7, 8, 15, 16, 31, 32, 101):
                with self.subTest(limit=limit):
                    source = [n for n in range(2, 102) if reference_is_prime(n)]
                    with patch.object(dataset, "read_source", return_value=source):
                        count = build_database(path, limit)
                    self.assertEqual(count, sum(reference_is_prime(n) for n in range(limit + 1)))
                    with patch.object(prime, "DATABASE_PATH", path):
                        try:
                            for number in range(limit + 1):
                                self.assertEqual(prime.is_prime(number), reference_is_prime(number))
                            with self.assertRaises(ValueError):
                                prime.is_prime(limit + 1)
                        finally:
                            _, data = prime._load_database(path)
                            data.close()
                            prime._load_database.cache_clear()

    def test_missing_and_invalid_databases(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "primes.bin"
            with self.assertRaises(FileNotFoundError):
                prime._load_database(path)
            for contents in (
                b"",
                b"bad header",
                prime.HEADER.pack(b"INVALID!", 7) + b"\xac",
                prime.HEADER.pack(prime.MAGIC, 1) + b"\x00",
                prime.HEADER.pack(prime.MAGIC, 7),
                prime.HEADER.pack(prime.MAGIC, 7) + b"\xac\x00",
            ):
                path.write_bytes(contents)
                with self.subTest(contents=contents), self.assertRaises(ValueError):
                    prime._load_database(path)

    def test_cli_works_from_another_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run([sys.executable, str(SCRIPT), "97"], cwd=directory, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "97 is a prime\n")

    def test_cli_interactive_and_invalid_input(self):
        result = subprocess.run([sys.executable, str(SCRIPT)], input="100\n", capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("100 is not a prime", result.stdout)
        for argument in ("1299710", "hello"):
            result = subprocess.run([sys.executable, str(SCRIPT), argument], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertTrue(result.stderr)
            self.assertNotIn("is not a prime", result.stdout)

    def test_import_failure_preserves_existing_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "primes.bin"
            source = Path(directory) / "data.json"
            path.write_bytes(b"existing database")
            source.write_bytes(b"[2, 3, 5, 7]")
            with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                build_database(path, source_file=source)
            self.assertEqual(path.read_bytes(), b"existing database")
            self.assertEqual(sorted(p.name for p in Path(directory).iterdir()), ["data.json", "primes.bin"])

    def test_cannot_extend_beyond_source_coverage(self):
        with patch.object(dataset, "read_source", side_effect=AssertionError("Source should not be read")):
            for limit in (1, True, 2.5, 1299710):
                with self.subTest(limit=limit), self.assertRaises(ValueError):
                    build_database(limit=limit)


if __name__ == "__main__":
    unittest.main()
