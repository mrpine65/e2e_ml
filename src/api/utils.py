"""
Auxiliary functions used to generate monitorings reports.
"""

from typing import List, Text
from pathlib import Path

import pandas as pd
from loguru import logger

from evidently.report import Report
from evidently import ColumnMapping
from evidently.metric_preset import (
    ClassificationPreset,
    TargetDriftPreset,
    DataDriftPreset,
    DataQualityPreset
)

def column_mapping(
    dataframe: pd.DataFrame,
    target_column: str,
    predict_column: str
) -> ColumnMapping:
    """
    Generate an Evidently `ColumnMapping` object from a given pandas DataFrame.
    
    Args:
        dataframe (pd.DataFrame): The input dataframe.
        target_column (str): Name of the target column.
        predict_column (str): Name of the prediction column.
    
    Returns:
        ColumnMapping: The generated Evidently column mapping.
    """
    numerical_columns = dataframe.select_dtypes('number').columns.to_list()
    categorical_columns = dataframe.select_dtypes(['object', 'category']).columns.to_list()
    logger.info(f"Creating ColumnMapping for {dataframe.columns.to_list()}")

    schema = ColumnMapping(
        categorical_features=categorical_columns,
        numerical_features=numerical_columns,
        target= target_column,
        prediction = predict_column
    )
    return schema

def build_model_performance_report(
    current_data: pd.DataFrame,
    reference_data: pd.DataFrame,
    schema: ColumnMapping,
    report_path: Path
) -> Text:
    """Builds a model performance report

    Args:
        current_data (pd.DataFrame): The current data
        reference_data (pd.DataFrame): The reference data
        schema (ColumnMapping): the ColumnMapping
        report_path (Path): Where the reported will be saved

    Returns:
        Text: The reported path
    """
    logger.info(f"Creating model performance report at {report_path}")
    rp = Report(
        metrics=[ClassificationPreset()]
    )

    rp.run(
        current_data=current_data,
        reference_data=reference_data,
        column_mapping=schema
    )

    rp.save_html(str(report_path))
    return report_path

def build_target_drift_report(
    current_data: pd.DataFrame,
    reference_data: pd.DataFrame,
    schema: ColumnMapping,
    report_path: Path
) -> Text:
    """Builds a target drift report

    Args:
        current_data (pd.DataFrame): The current data
        reference_data (pd.DataFrame): The reference data
        schema (ColumnMapping): the ColumnMapping
        report_path (Path): Where the reported will be saved

    Returns:
        Text: The reported path
    """
    logger.info(f"Creating target drift report at {report_path}")
    rp = Report(
        metrics=[TargetDriftPreset()]
    )

    rp.run(
        current_data=current_data,
        reference_data=reference_data,
        column_mapping=schema
    )

    rp.save_html(str(report_path))
    return report_path

def build_data_drift_report(
    current_data: pd.DataFrame,
    reference_data: pd.DataFrame,
    schema: ColumnMapping,
    report_path: (Path)
) -> Text:
    """ Build a data drift report

    Args:
        current_data (pd.DataFrame): the dataframe
        rereference_data (pd.DataFrame): the reference dataframe
        schema (ColumnMapping): the ColumnMapping
        report_path (Path): where the reported will be saved
    
    Returns:
        Text: the reported path
    """
    logger.info(f"Creating data drift report at {report_path}")
    rp = Report(
        metrics=[DataDriftPreset()]
    )

    rp.run(
        current_data=current_data,
        reference_data=reference_data,
        column_mapping=schema
    )

    rp.save_html(str(report_path))
    return report_path

def build_data_quality_report(
    current_data: pd.DataFrame,
    reference_data: pd.DataFrame,
    schema: ColumnMapping,
    report_path: Path
) -> Text:
    """ Build a model data quality report

    Args:
        current_data (pd.DataFrame): the dataframe
        reference_data (pd.DataFrame): the reference dataframe
        schema (ColumnMapping): the ColumnMapping
        report_path (Path): where reported will be saved
    
    Returns:
        Text: the reported path
    """
    logger.info(f"Creating model data quality report at {report_path}")
    rp = Report( metrics=[DataQualityPreset()] )

    rp.run(
        current_data=current_data,
        reference_data=reference_data,
        column_mapping=schema
    )

    rp.save_html(str(report_path))
    return report_path