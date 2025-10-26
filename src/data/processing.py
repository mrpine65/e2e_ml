"""
Stores data processing functions, such as for cleaning the data, creating new features,
encoding category columns, add on
"""

import os
import pathlib
from typing import List, Dict
import warnings

import boto3
import pandas as pd
import numpy as np
from loguru import logger
from sklearn.preprocessing import StandardScaler, OneHotEncoder

from ..config.aws import aws_credentials
from ..config.kaggle import kaggle_credentials
from ..config.settings import general_settings
from .utils import load_features
from ..config.model import model_settings

# warnings.filterwarnings("ignore", category=pd.errors.SettingWithCopyWarning)

def data_processing_inference(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Applies the full data processing pipeline for inference."""

    # 🧹 Step 1: Data Cleaning
    logger.info("STEP 1: Data Cleaning - Removing unnecessary columns.")
    dataframe = _drop_features(dataframe, ['id', 'NObeyesdad'])

    # 🧪 Step 2: Feature Engineering
    logger.info("STEP 2: Feature Engineering - Creating new derived features.")
    dataframe = _change_height_units(dataframe)
    dataframe = _create_bmi_feature(dataframe)
    dataframe = _create_inmm_features(dataframe)

    # 🔄 Step 3: Feature Transformation
    logger.info("STEP 3: Feature Transformation - Categorizing and transforming numeric columns.")
    logger.info(f"Loading 'qcut_bins' (Age quantile bins) from {general_settings.ARTIFACTS_PATH}")
    age_bins = load_features(
        path=general_settings.ARTIFACTS_PATH,
        features_name="qcut_bins"
    )
    dataframe = _categorize_numerical_columns(dataframe, age_bins)
    dataframe = _transform_numerical_columns(dataframe)

    logger.info(f"Loading 'scalers' (StandardScaler objects) from {general_settings.ARTIFACTS_PATH}")
    scalers = load_features(
        path=general_settings.ARTIFACTS_PATH,
        features_name='scalers'
    )
    dataframe = _scales_numerical_columns(dataframe, scalers)

    # 🔠 Step 4: Feature Encoding
    logger.info("STEP 4: Feature Encoding - Applying OneHotEncoder to categorical columns.")
    logger.info(f"Loading 'features_encoder' (OneHotEncoder) from {general_settings.ARTIFACTS_PATH}")
    features_encoder = load_features(
        path=general_settings.ARTIFACTS_PATH,
        features_name='features_encoder'
    )
    dataframe = _encode_categorical_columns(dataframe, features_encoder)

    # 🎯 Step 5: Feature Selection
    logger.info("STEP 5: Feature Selection - Keeping only selected model features.")
    dataframe = dataframe.loc[:, model_settings.FEATURES]
    logger.info(f"Filtering the feature columns, keeping only {model_settings.FEATURES} columns.")

    logger.success("✅ Data processing pipeline completed successfully.")
    return dataframe



def _change_height_units(dataframe: pd.DataFrame) -> pd.DataFrame:
    logger.info("Changing the height units to centimeters.")
    dataframe = dataframe.copy()
    dataframe.loc[:, 'Height'] = dataframe['Height'] * 100
    return dataframe


def _create_bmi_feature(dataframe: pd.DataFrame) -> pd.DataFrame:
    logger.info("Creating a new column for the BMI (Body Mass Index) values from data samples.")
    dataframe = dataframe.copy()
    dataframe.loc[:, "BMI"] = dataframe["Weight"] / (dataframe["Height"] ** 2)
    return dataframe


def _create_inmm_features(dataframe: pd.DataFrame) -> pd.DataFrame:
    logger.info("Creating a new column for the INMM (Ideal Number of Main Meals?) values from data sample.")
    dataframe = dataframe.copy()
    dataframe.loc[:, "INMM"] = (dataframe["NCP"] == 3).astype(int).astype("object")
    return dataframe


def _transform_numerical_columns(dataframe: pd.DataFrame) -> pd.DataFrame:
    dataframe = dataframe.copy()
    numerical_columns = dataframe.select_dtypes(include=["number"]).columns.to_list()
    logger.info(f"Transforming (Log + 1 transformation) to the {numerical_columns} columns.")

    for col in numerical_columns:
        dataframe.loc[:, col] = np.log1p(dataframe[col])

    return dataframe


def _categorize_numerical_columns(dataframe: pd.DataFrame, bins: np.ndarray) -> pd.DataFrame:
    dataframe = dataframe.copy()
    logger.info("Categorizing the 'Age' column into discrete categories.")
    dataframe.loc[:, 'Age'] = pd.cut(
        x=dataframe['Age'],
        bins=bins,
        labels=['q1', 'q2', 'q3', 'q4']
    ).astype("object")
    return dataframe


def _scales_numerical_columns(dataframe: pd.DataFrame, scalers: Dict[str, StandardScaler]) -> pd.DataFrame:
    dataframe = dataframe.copy()
    numerical_columns = dataframe.select_dtypes(include=["number"]).columns.to_list()
    logger.info(f"Scaling the {numerical_columns} columns.")

    for col in numerical_columns:
        dataframe.loc[:, col] = scalers[col].transform(dataframe[col].to_numpy().reshape(-1, 1))

    return dataframe


def _encode_categorical_columns(dataframe: pd.DataFrame, encoder: OneHotEncoder) -> pd.DataFrame:
    dataframe = dataframe.copy()
    categorical_columns = dataframe.select_dtypes(include=['object', 'category']).columns.to_list()
    logger.info(f"Encoding the {categorical_columns} columns.")

    encoded = pd.DataFrame(
        data=encoder.transform(dataframe[categorical_columns]),
        columns=encoder.get_feature_names_out(categorical_columns),
        index=dataframe.index
    )

    dataframe = pd.concat([dataframe.drop(columns=categorical_columns), encoded], axis=1)
    return dataframe


def _drop_features(dataframe: pd.DataFrame, features: List) -> pd.DataFrame:

    logger.info(f"drop fratures {features}")
    dataframe = dataframe.copy()
    return dataframe.drop(columns=features, axis=1).reset_index(drop=True)


def load_dataset(path: pathlib.Path, from_aws: bool) -> pd.DataFrame:
    logger.info(f"Loading the dataset from {path}.")

    if not from_aws:
        return pd.read_csv(path)

    os.environ["AWS_ACCESS_KEY_ID"] = aws_credentials.AWS_ACCESS_KEY
    os.environ["AWS_SECRET_ACCESS_KEY"] = aws_credentials.AWS_SECRET_KEY

    s3_client = boto3.client(
        "s3",
        aws_access_key_id=aws_credentials.AWS_ACCESS_KEY,
        aws_secret_access_key=aws_credentials.AWS_SECRET_KEY
    )

    local_path = pathlib.Path.joinpath(general_settings.DATA_PATH, path.name)
    s3_client.download_file(aws_credentials.S3, path.name, local_path)
    return load_dataset(local_path, from_aws=False)


# Debug/demo usage
from pprint import pprint
from pathlib import Path

df = load_dataset(Path.joinpath(general_settings.DATA_PATH, general_settings.RAW_FILE_NAME), from_aws=False)
pprint(data_processing_inference(df.head(10)))
