"""
Unit test cases to test the API code.
"""
import json
from pathlib import Path
from typing import Dict

import requests

from src.config.model import model_settings
from src.config.report import report_settings
from . import CODE_VERSION


def test_version_endpoint() -> None:
    """
    Unit case to test the API's version endpoint.
    """
    desired_keys = ["model_version", "code_version"]

    response = requests.get("http://localhost:8000/version", timeout=100)
    content = json.loads(response.text)

    assert response.status_code == 200
    assert isinstance(content, Dict)
    assert all(dk in content.keys() for dk in desired_keys)
    assert model_settings.VERSION == content[desired_keys[0]]
    assert CODE_VERSION == content[desired_keys[1]]


def test_model_performance_report_endpoint() -> None:
    """
    Unit case to test the API's model performance report endpoint.
    """
    window_size = 300
    path = Path.joinpath(
        report_settings.REPORTS_PATH, report_settings.MODEL_PERFORMANCE_REPORT_NAME
    )
    headers = {"Accept-Encoding": "identity"}

    response = requests.get(
        f"http://localhost:8000/monitor-model?window_size={window_size}",
        timeout=100,
        headers=headers,
    )

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert Path.exists(Path(path))


def test_target_drift_report_endpoint() -> None:
    """
    Unit case to test the API's target drift report endpoint.
    """
    window_size = 300
    path = Path.joinpath(
        report_settings.REPORTS_PATH, report_settings.TARGET_DRIFT_REPORT_NAME
    )
    headers = {"Accept-Encoding": "identity"}

    response = requests.get(
        f"http://localhost:8000/monitor-target?window_size={window_size}",
        timeout=100,
        headers=headers,
    )

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert Path.exists(Path(path))


def test_data_drift_report_endpoint() -> None:
    """
    Unit case to test the API's data drift report endpoint.
    """
    window_size = 300
    path = Path.joinpath(
        report_settings.REPORTS_PATH, report_settings.DATA_DRIFT_REPORT_NAME
    )
    headers = {"Accept-Encoding": "identity"}

    response = requests.get(
        f"http://localhost:8000/monitor-data?window_size={window_size}",
        timeout=100,
        headers=headers,
    )

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert Path.exists(Path(path))


def test_data_quality_report_endpoint() -> None:
    """
    Unit case to test the API's data quality report endpoint.
    """
    window_size = 300
    path = Path.joinpath(
        report_settings.REPORTS_PATH, report_settings.DATA_QUALITY_REPORT_NAME
    )
    headers = {"Accept-Encoding": "identity"}

    response = requests.get(
        f"http://localhost:8000/monitor-data-quality?window_size={window_size}",
        timeout=100,
        headers=headers,
    )

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert Path.exists(Path(path))


def test_inference_endpoint() -> None:
    """
    Unit case to test the API's inference endpoint.
    """
    desired_classes = ["Overweight_Level_I"]
    desired_keys = ["predictions"]

    data = {
        'Gender': 'Female',
        'Age': 20.0,
        'Height': 1.65,
        'Weight': 65.0,
        'family_history_with_overweight': 'yes',
        'FAVC': 'yes',
        'FCVC': 3.0,
        'NCP': 3.0,
        'CAEC': 'Sometimes',
        'SMOKE': 'no',
        'CH2O': 3.0,
        'SCC': 'no',
        'FAF': 1.0,
        'TUE': 0.0,
        'CALC': 'Sometimes',
        'MTRANS': 'Public_Transportation'
    }

    response = requests.post("http://localhost:8000/predict", json=data, timeout=100)
    content = json.loads(response.text)

    assert response.status_code == 200
    assert isinstance(content, Dict)
    assert all(dk in content.keys() for dk in desired_keys)
    assert content[desired_keys[0]] == desired_classes