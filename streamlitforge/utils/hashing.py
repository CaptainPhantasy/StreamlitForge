"""Hashing utilities for deterministic port assignment"""

import hashlib


def hash_path(path: str) -> str:
    """Generate a deterministic hash from a file path.

    Args:
        path: File or directory path

    Returns:
        Hexadecimal hash string
    """
    absolute_path = path.replace(" ", "").replace("~", "")
    return hashlib.sha256(absolute_path.encode()).hexdigest()


def hash_to_port(hash_str: str, base_port: int = 8501, max_port: int = 8999) -> int:
    """Convert a hash string to a port number.

    Args:
        hash_str: Hexadecimal hash string
        base_port: Base port number
        max_port: Maximum port number

    Returns:
        Port number within range
    """
    hash_int = int(hash_str[:16], 16)
    hash_int = hash_int % (max_port - base_port + 1)
    return base_port + hash_int


def normalize_port(port: int, base_port: int = 8501, max_port: int = 8999) -> int:
    """Normalize port to be within valid range.

    Args:
        port: Port number to normalize
        base_port: Minimum port number
        max_port: Maximum port number

    Returns:
        Normalized port number
    """
    if port < base_port:
        return base_port
    if port > max_port:
        return max_port
    return port
