"""Filesystem utilities for project scaffolding and management."""

import os
from pathlib import Path
from typing import List, Optional


def create_directory(path: str, exist_ok: bool = True) -> Path:
    """Create a directory if it doesn't exist.

    Args:
        path: Directory path to create
        exist_ok: If False, raise error if directory exists

    Returns:
        Path object for the created directory

    Raises:
        FileExistsError: If directory exists and exist_ok is False
    """
    path_obj = Path(path).expanduser().resolve()

    if exist_ok and path_obj.exists():
        return path_obj

    if exist_ok and path_obj.is_file():
        raise FileExistsError(f"Path exists as file: {path}")

    path_obj.mkdir(parents=True, exist_ok=exist_ok)

    return path_obj


def create_file(path: str, content: str) -> Path:
    """Create a file with the given content.

    Args:
        path: File path to create
        content: File content

    Returns:
        Path object for the created file

    Raises:
        FileExistsError: If file already exists
    """
    path_obj = Path(path).expanduser().resolve()

    if path_obj.exists():
        raise FileExistsError(f"File already exists: {path}")

    path_obj.parent.mkdir(parents=True, exist_ok=True)
    path_obj.write_text(content, encoding='utf-8')

    return path_obj


def read_file(path: str) -> str:
    """Read file content.

    Args:
        path: File path to read

    Returns:
        File content as string

    Raises:
        FileNotFoundError: If file doesn't exist
    """
    path_obj = Path(path).expanduser().resolve()

    if not path_obj.exists():
        raise FileNotFoundError(f"File not found: {path}")

    return path_obj.read_text(encoding='utf-8')


def list_files(path: str, recursive: bool = True) -> List[Path]:
    """List files in a directory.

    Args:
        path: Directory path
        recursive: Whether to list recursively

    Returns:
        List of Path objects for files in directory
    """
    path_obj = Path(path).expanduser().resolve()

    if not path_obj.exists() or not path_obj.is_dir():
        return []

    pattern = "**/*" if recursive else "*"

    return sorted([
        p for p in path_obj.glob(pattern)
        if p.is_file()
    ])


def get_project_root(path: str = ".") -> Path:
    """Find the project root directory.

    Args:
        path: Starting path to search from

    Returns:
        Path object for project root

    Raises:
        FileNotFoundError: If project root cannot be found
    """
    current = Path(path).expanduser().resolve()

    # Look for common project markers
    markers = [
        "pyproject.toml",
        "requirements.txt",
        "setup.py",
        "Dockerfile",
        "Makefile"
    ]

    while current != current.parent:
        if any((current / marker).exists() for marker in markers):
            return current
        current = current.parent

    # If no markers found, return current directory
    return Path(path).expanduser().resolve()


def get_relative_path(target: str, base: str = ".") -> Path:
    """Get relative path from base to target.

    Args:
        target: Target file/directory path
        base: Base directory path

    Returns:
        Relative Path object
    """
    target_path = Path(target).expanduser().resolve()
    base_path = Path(base).expanduser().resolve()

    return target_path.relative_to(base_path)


def copy_file(src: str, dst: str) -> Path:
    """Copy a file from source to destination.

    Args:
        src: Source file path
        dst: Destination file path

    Returns:
        Path object for the copied file

    Raises:
        FileNotFoundError: If source file doesn't exist
    """
    if not Path(src).expanduser().resolve().exists():
        raise FileNotFoundError(f"Source file not found: {src}")

    dst_path = Path(dst).expanduser()
    dst_path.parent.mkdir(parents=True, exist_ok=True)

    import shutil
    shutil.copy2(src, dst)

    return dst_path


def delete_file(path: str) -> bool:
    """Delete a file.

    Args:
        path: File path to delete

    Returns:
        True if file was deleted

    Raises:
        FileNotFoundError: If file doesn't exist
        IsADirectoryError: If path is a directory
    """
    path_obj = Path(path).expanduser().resolve()

    if not path_obj.exists():
        raise FileNotFoundError(f"File not found: {path}")

    if path_obj.is_dir():
        raise IsADirectoryError(f"Path is a directory: {path}")

    path_obj.unlink()
    return True


def delete_directory(path: str, recursive: bool = True) -> bool:
    """Delete a directory.

    Args:
        path: Directory path to delete
        recursive: If False, fail if directory is not empty

    Returns:
        True if directory was deleted

    Raises:
        FileNotFoundError: If directory doesn't exist
        NotADirectoryError: If path is not a directory
    """
    path_obj = Path(path).expanduser().resolve()

    if not path_obj.exists():
        raise FileNotFoundError(f"Directory not found: {path}")

    if not path_obj.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {path}")

    if not recursive and list(path_obj.iterdir()):
        raise ValueError(f"Directory is not empty: {path}")

    import shutil
    shutil.rmtree(path_obj)
    return True
