"""Validation utilities for input and configuration validation."""

from typing import Any, Dict, List, Optional


def validate_string(value: Any, min_length: Optional[int] = None,
                    max_length: Optional[int] = None,
                    allow_empty: bool = False) -> str:
    """Validate a value is a string with length constraints.

    Args:
        value: Value to validate
        min_length: Minimum string length
        max_length: Maximum string length
        allow_empty: Whether empty string is allowed

    Returns:
        The validated string value

    Raises:
        TypeError: If value is not a string
        ValueError: If validation fails
    """
    if not isinstance(value, str):
        raise TypeError(f"Expected string, got {type(value).__name__}")

    if not allow_empty and len(value) == 0:
        raise ValueError("String cannot be empty")

    if min_length is not None and len(value) < min_length:
        raise ValueError(f"String length must be at least {min_length}, got {len(value)}")

    if max_length is not None and len(value) > max_length:
        raise ValueError(f"String length must be at most {max_length}, got {len(value)}")

    return value


def validate_port(port: Any, min_port: int = 1024, max_port: int = 65535) -> int:
    """Validate a value is a valid port number.

    Args:
        port: Value to validate
        min_port: Minimum valid port number
        max_port: Maximum valid port number

    Returns:
        The validated port number

    Raises:
        TypeError: If value is not an integer
        ValueError: If port number is invalid
    """
    if not isinstance(port, int):
        raise TypeError(f"Expected integer, got {type(port).__name__}")

    if port < min_port or port > max_port:
        raise ValueError(f"Port must be between {min_port} and {max_port}")

    return port


def validate_directory(path: Any, must_exist: bool = True) -> str:
    """Validate a value is a valid directory path.

    Args:
        path: Value to validate
        must_exist: Whether directory must exist

    Returns:
        The validated directory path as string

    Raises:
        TypeError: If value is not a string
        ValueError: If validation fails
    """
    if not isinstance(path, str):
        raise TypeError(f"Expected string, got {type(path).__name__}")

    from pathlib import Path
    path_obj = Path(path).expanduser().resolve()

    if must_exist:
        if not path_obj.exists():
            raise ValueError(f"Directory does not exist: {path}")
        if not path_obj.is_dir():
            raise ValueError(f"Path is not a directory: {path}")

    return str(path_obj)


def validate_file(path: Any, must_exist: bool = True) -> str:
    """Validate a value is a valid file path.

    Args:
        path: Value to validate
        must_exist: Whether file must exist

    Returns:
        The validated file path as string

    Raises:
        TypeError: If value is not a string
        ValueError: If validation fails
    """
    if not isinstance(path, str):
        raise TypeError(f"Expected string, got {type(path).__name__}")

    from pathlib import Path
    path_obj = Path(path).expanduser().resolve()

    if must_exist:
        if not path_obj.exists():
            raise ValueError(f"File does not exist: {path}")
        if not path_obj.is_file():
            raise ValueError(f"Path is not a file: {path}")

    return str(path_obj)


def validate_project_name(name: Any, allow_hyphens: bool = True) -> str:
    """Validate a value is a valid project name.

    Args:
        name: Value to validate
        allow_hyphens: Whether hyphens are allowed

    Returns:
        The validated project name as string

    Raises:
        TypeError: If value is not a string
        ValueError: If validation fails
    """
    if not isinstance(name, str):
        raise TypeError(f"Expected string, got {type(name).__name__}")

    name = name.strip()

    if len(name) == 0:
        raise ValueError("Project name cannot be empty")

    if not name[0].isalpha():
        raise ValueError("Project name must start with a letter")

    if len(name) < 3:
        raise ValueError("Project name must be at least 3 characters")

    if len(name) > 50:
        raise ValueError("Project name must be at most 50 characters")

    invalid_chars = []
    for char in name:
        if not char.isalnum() and char not in ('_', '-'):
            invalid_chars.append(char)

    if invalid_chars:
        raise ValueError(
            f"Project name contains invalid characters: {', '.join(invalid_chars)}"
        )

    return name


def validate_email(email: Any) -> str:
    """Validate an email address.

    Args:
        email: Value to validate

    Returns:
        The validated email address as string

    Raises:
        TypeError: If value is not a string
        ValueError: If validation fails
    """
    if not isinstance(email, str):
        raise TypeError(f"Expected string, got {type(email).__name__}")

    if '@' not in email or '.' not in email.split('@')[-1]:
        raise ValueError("Invalid email address format")

    return email


def validate_dict(value: Any, required_keys: Optional[List[str]] = None) -> Dict[str, Any]:
    """Validate a value is a dictionary.

    Args:
        value: Value to validate
        required_keys: List of required keys

    Returns:
        The validated dictionary

    Raises:
        TypeError: If value is not a dictionary
        ValueError: If required keys are missing
    """
    if not isinstance(value, dict):
        raise TypeError(f"Expected dictionary, got {type(value).__name__}")

    if required_keys:
        missing = [key for key in required_keys if key not in value]
        if missing:
            raise ValueError(f"Missing required keys: {', '.join(missing)}")

    return value


def validate_bool(value: Any) -> bool:
    """Validate a value is a boolean.

    Args:
        value: Value to validate

    Returns:
        The validated boolean

    Raises:
        TypeError: If value is not a boolean
    """
    if not isinstance(value, bool):
        raise TypeError(f"Expected boolean, got {type(value).__name__}")

    return value
