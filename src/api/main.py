"""
API's main file
"""

from pathlib import Path

from loguru import logger
from typing import Dict
import pandas as pd
from fastapi import FastAPI, Depends
from fastapi.responses import FileResponse

from .utils import (
    column_mapping,
    build_data_drift_report,
    build_data_quality_report,
    build_target_drift_report,
    build_model_performance_report,
)
from ..config.model import model_settings
from ..config.report import report_settings
from ..config.settings import general_settings
from ..schema.person import Person
from ..schema.monitoring import Monitoring
from ..data.processing import data_processing_inference
from . import current_dataset,reference_dataset ,loaded_model

app = FastAPI()

@app.get("/monitor-model")
def monitor_model_performance(monitoring: Monitoring = Depends()) -> FileResponse:
    """ This endpoint is used to create a report for monitoring model performance

    Returns:
        FileReponse: the report HTML file
    """
    windown_size = monitoring.windown_size
    logger.info(f"Loading current dataset and selecting the first {windown_size} rows.")
    logger.info(f"================== PREPROCESSING THE DATA =====================")
    current_data = current_dataset.head(windown_size).copy()
    current_data = data_processing_inference(current_data)

    current_data["prediction"] = loaded_model.predict(current_data)
    current_data[general_settings.TARGET_COLUMN] = current_dataset[ general_settings.TARGET_COLUMN ].copy()
    
    reference_data = reference_dataset.head(windown_size).copy()
    reference_data = data_processing_inference(reference_data)

    reference_data["prediction"] = loaded_model.predict(reference_data)
    reference_data[general_settings.TARGET_COLUMN] = reference_dataset[ general_settings.TARGET_COLUMN ].copy()
    
    schema = column_mapping(
        dataframe=current_data,
        target_column=general_settings.TARGET_COLUMN,
        predict_column='prediction'
    )

    report_path = build_model_performance_report(
        current_data=current_data,
        reference_data=reference_data,
        schema=schema,
        report_path=Path.joinpath(report_settings.REPORTS_PATH, report_settings.MODEL_PERFORMANCE_REPORT_NAME)
    )

    logger.info(f"Returning report as HTML file in location {report_path}.")
    return FileResponse(report_path)

@app.get("/monitor-target")
def monitor_target_drift(monitoring: Monitoring = Depends()) -> FileResponse:
    """ This endpoint is used to create a report for monitoring target drift

    Returns:
        FileReponse: The report HTML file
    """
    windown_size = monitoring.windown_size
    logger.info(f"Loading current dataset and selecting the first {windown_size} rows.")
    logger.info(f"================== PREPROCESSING THE DATA =====================")
    current_data = current_dataset.head(windown_size).copy()
    current_data = data_processing_inference(current_data)

    current_data["prediction"] = loaded_model.predict(current_data)
    current_data[general_settings.TARGET_COLUMN] = current_dataset[ general_settings.TARGET_COLUMN ].copy()

    reference_data = reference_dataset.head(windown_size).copy()
    reference_data = data_processing_inference(reference_data)

    reference_data["prediction"] = loaded_model.predict(reference_data)
    reference_data[general_settings.TARGET_COLUMN] = reference_dataset[ general_settings.TARGET_COLUMN ].copy()
    
    schema = column_mapping(
        dataframe=current_data,
        target_column=general_settings.TARGET_COLUMN,
        predict_column='prediction'
    )

    report_path = build_target_drift_report(
        current_data=current_data,
        reference_data=reference_data,
        schema=schema,
        report_path=Path.joinpath(report_settings.REPORTS_PATH, report_settings.TARGET_DRIFT_REPORT_NAME)
    )

    logger.info(f"Returning report as HTML file in location {report_path}.")
    return FileResponse(report_path)

@app.get("/monitor-data")
def monitor_data_drift(monitoring: Monitoring = Depends()) -> FileResponse:
    """ This endpoint is used to create report for monitoring data drift

    Returns:
        FileReponse: the report HTML file.
    """
    windown_size = monitoring.windown_size
    logger.info(f"Loading current dataset and selecting the first {windown_size} rows.")
    logger.info(f"================== PREPROCESSING THE DATA =====================")
    current_data = current_dataset.head(windown_size).copy()
    current_data = data_processing_inference(current_data)

    current_data["prediction"] = loaded_model.predict(current_data)
    current_data[general_settings.TARGET_COLUMN] = current_dataset[ general_settings.TARGET_COLUMN ].copy()

    reference_data = reference_dataset.head(windown_size).copy()
    reference_data = data_processing_inference(reference_data)

    reference_data["prediction"] = loaded_model.predict(reference_data)
    reference_data[general_settings.TARGET_COLUMN] = reference_dataset[ general_settings.TARGET_COLUMN ].copy()
    
    schema = column_mapping(
        dataframe=current_data,
        target_column=general_settings.TARGET_COLUMN,
        predict_column='prediction'
    )

    report_path = build_data_drift_report(
        current_data=current_data,
        reference_data=reference_data,
        schema=schema,
        report_path=Path.joinpath(report_settings.REPORTS_PATH, report_settings.DATA_DRIFT_REPORT_NAME)
    )

    logger.info(f"Returning report as HTML file in location {report_path}.")
    return FileResponse(report_path)

@app.get("/monitor-data-quality")
def monitor_data_quality(monitoring: Monitoring = Depends()) -> FileResponse:
    """ This endpoint is used to create report for monitoring data quality

    Returns:
        FileResponse: The report HTML file.
    """
    windown_size = monitoring.windown_size
    logger.info(f"Loading current dataset and selecting the first {windown_size} rows.")
    logger.info(f"================== PREPROCESSING THE DATA =====================")
    current_data = current_dataset.head(windown_size).copy()
    current_data = data_processing_inference(current_data)

    current_data["prediction"] = loaded_model.predict(current_data)
    current_data[general_settings.TARGET_COLUMN] = current_dataset[ general_settings.TARGET_COLUMN ].copy()

    reference_data = reference_dataset.head(windown_size).copy()
    reference_data = data_processing_inference(reference_data)

    reference_data["prediction"] = loaded_model.predict(reference_data)
    reference_data[general_settings.TARGET_COLUMN] = reference_dataset[ general_settings.TARGET_COLUMN ].copy()

    schema = column_mapping(
        dataframe=current_data,
        target_column=general_settings.TARGET_COLUMN,
        predict_column='prediction'
    )

    report_path = build_data_quality_report(
        current_data=current_data,
        reference_data=reference_data,
        schema=schema,
        report_path=Path.joinpath(report_settings.REPORTS_PATH, report_settings.DATA_QUALITY_REPORT_NAME)
    )

    logger.info(f"Returning report as HTML file in location {report_path}.")
    return FileResponse(report_path)

@app.get("/version")
def check_versions() -> Dict:
    """ This endpoint will return the current model and code versions.

    Returns:
        Dict: the model and code versions.
    """
    with open(f"{general_settings.RESEARCH_ENVIRONMENT_PATH}/VERSION", "r", encoding='utf-8') as f:
        code_version = f.readline().strip()

    return {
        "code_version": code_version,
        "model_version": model_settings.VERSION
    }


@app.post("/predict")
async def prediction(person: Person) -> Dict:
    """
    This endpoint is used to make a prediction (with the trained model)
    with the given data.

    Args:
        person (Person): a person's data.

    Returns:
        Dict: the predictions.
    """
    data = pd.DataFrame.from_dict([person.model_dump()])
    features = data_processing_inference(data)

    return {"predictions": loaded_model.predict(features, transform_to_str=True).tolist()}