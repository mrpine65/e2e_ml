"""
Creates a Pydantic's base model for the general configuration settings.
"""
from pathlib import Path
from pydantic import BaseModel
import os

from . import read_yaml_credentials_file


class GeneralSettings(BaseModel):
    """Creates a Pydantic base model for general settings."""

    DATA_PATH: Path
    RAW_FILE_NAME: str
    CURRENT_FILE_NAME: str
    ARTIFACTS_PATH: Path
    FEATURES_PATH: Path
    TARGET_COLUMN: str
    RESEARCH_ENVIRONMENT_PATH: Path



general_settings = GeneralSettings(
    **read_yaml_credentials_file(
        file_path=Path(__file__).resolve().parents[0],
        file_name="settings.yaml",
    )
)

os.makedirs(general_settings.DATA_PATH, exist_ok=True)
os.makedirs(general_settings.ARTIFACTS_PATH, exist_ok=True)
os.makedirs(general_settings.FEATURES_PATH, exist_ok=True)
os.makedirs(general_settings.RESEARCH_ENVIRONMENT_PATH, exist_ok=True)