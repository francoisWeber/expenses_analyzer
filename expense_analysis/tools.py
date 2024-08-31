import hashlib
from typing import Any


def get_hash(*args: Any) -> str:  # type: ignore
    # Concatenate the string representation of each argument
    sha256_hash = hashlib.sha256()
    for arg in args:
        sha256_hash.update(str(arg).encode())

    # Get the hexadecimal representation of the hash
    hash_value = sha256_hash.hexdigest()

    return hash_value
