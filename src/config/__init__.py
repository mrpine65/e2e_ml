"""
Stores auxiliary functions (such as reading a YAML file)
that will be used with the main configuration functions.
"""

from pathlib import Path
from typing import Dict, Any
import yaml


def read_yaml_credentials_file(file_path: Path, file_name: str) -> Dict[str, Any]:
    """
    Reads a YAML file and converts any path-like values (those starting with '/')
    into absolute paths based on the project root directory (auto-detected).

    Args:
        file_path (Path): Directory containing the YAML file.
        file_name (str): Name of the YAML file.

    Returns:
        Dict[str, Any]: Dictionary containing the YAML content with
                        all '/'-prefixed paths converted to absolute paths.
    """
    path = (file_path / file_name).resolve()

    project_root = Path(__file__).resolve().parents[2]

    with path.open("r", encoding="utf-8") as file:
        context = yaml.safe_load(file) or {}

    for key, value in context.items():
        if isinstance(value, str) and value.startswith("/"):
            abs_path = (project_root / value.lstrip("/")).resolve()
            context[key] = str(abs_path)


    return context
