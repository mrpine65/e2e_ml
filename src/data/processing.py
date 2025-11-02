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
from sklearn.preprocessing import StandardScaler, OneHotEncoder, LabelBinarizer

from ..config.aws import aws_credentials
from ..config.kaggle import kaggle_credentials
from ..config.settings import general_settings
from .utils import load_features, save_feature
from ..config.model import model_settings

warnings.filterwarnings("ignore")

def data_processing_inference(dataframe: pd.DataFrame, is_train: bool = False) -> pd.DataFrame:
    """Applies the full data processing pipeline for inference with detailed logging."""

    logger.debug("🔧 Starting `data_processing_inference` function.")
    logger.info(f"Mode: is_train={is_train}")

    # 🧹 Step 1: Data Cleaning
    logger.info("Removing columns ['id', 'NObeyesdad'].")
    dataframe = _drop_features(dataframe, ['id', 'NObeyesdad'])

    # 🧪 Step 2: Feature Engineering
    dataframe = _change_height_units(dataframe)
    dataframe = _create_bmi_feature(dataframe)
    dataframe = _create_inmm_features(dataframe)

    # 🔄 Step 3: Feature Transformation
    if is_train:
        logger.info("computing 'Age' quantile bins using `pd.qcut`.")
        values, bins = pd.qcut(x=dataframe["Age"], q=4, retbins=True, labels=["q1", "q2", "q3", "q4"])
        bins = np.concatenate(([-np.inf], bins[1:-1], [np.inf]))
        save_feature(
            path=general_settings.ARTIFACTS_PATH,
            name="qcut_bins",
            feature=bins,
            send_to_aws=True
        )

    logger.info(f"Loading 'qcut_bins' from aws.")
    age_bins = load_features(
        path=general_settings.ARTIFACTS_PATH,
        features_name="qcut_bins",
        from_aws=True
    )
    dataframe = _categorize_numerical_columns(dataframe, age_bins)
    dataframe = _transform_numerical_columns(dataframe)

    if is_train:
        logger.info("fitting StandardScaler objects for numerical columns.")
        scalers = {}
        for col in dataframe.select_dtypes(include=["number"]).columns.to_list():
            sc = StandardScaler()
            sc.fit(dataframe[col].to_numpy().reshape(-1, 1))
            scalers[col] = sc
        save_feature(
            path=general_settings.ARTIFACTS_PATH,
            name="scalers",
            feature=scalers,
            send_to_aws=True
        )

    logger.info(f"Loading 'scalers' from aws")
    scalers = load_features(
        path=general_settings.ARTIFACTS_PATH,
        features_name='scalers',
        from_aws=True
    )
    dataframe = _scales_numerical_columns(dataframe, scalers)

    # 🔠 Step 4: Feature Encoding
    if is_train:
        logger.info("Training mode: fitting new OneHotEncoder on categorical columns.")
        categorical_columns = dataframe.select_dtypes(include=['object', 'category']).columns.to_list()
        logger.info(f"Categorical columns detected: {categorical_columns}")
        encoder = OneHotEncoder(
            drop='first',
            sparse_output=False,
            handle_unknown='infrequent_if_exist',
            min_frequency=20
        )
        encoder.fit(dataframe[categorical_columns])
        save_feature(
            path=general_settings.ARTIFACTS_PATH,
            name="features_encoder",
            feature=encoder,
            send_to_aws=True
        )

    logger.info(f"Loading 'features_encoder' from aws.")
    features_encoder = load_features(
        path=general_settings.ARTIFACTS_PATH,
        features_name='features_encoder',
        from_aws=True
    )
    dataframe = _encode_categorical_columns(dataframe, features_encoder)

    # # 🎯 Step 5: Feature Selection
    # logger.debug(f"Selecting columns: {model_settings.FEATURES}")
    # dataframe = dataframe.loc[:, model_settings.FEATURES]

    logger.success("✅ Data processing pipeline completed successfully.")
    return dataframe

def label_processing_inference(dataframe: pd.DataFrame, is_train: bool) -> np.ndarray:
    """Encodes target labels for training or inference with detailed logging."""

    logger.debug("🎯 Starting `label_processing_inference` function.")
    logger.info(f"Mode: is_train={is_train}")

    if is_train:
        logger.info("Training mode: fitting new LabelBinarizer on label data.")
        label_encoder = LabelBinarizer(sparse_output=False)
        label_encoder.fit(dataframe)
        save_feature(
            path=general_settings.ARTIFACTS_PATH,
            name="label_encoder",
            feature=label_encoder,
            send_to_aws=True
        )
        logger.info(f"Saved 'label_encoder' to aws.")

    logger.info(f"Loading 'label_encoder' from aws.")
    label_encoder = load_features(
        path=general_settings.ARTIFACTS_PATH,
        features_name='label_encoder',
        from_aws=True
    )
    encoded_data = _encode_label(dataframe, label_encoder)

    logger.success("✅ Label processing pipeline completed successfully.")
    return encoded_data

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
    dataframe['Age'] = dataframe['Age'].astype(object)
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
    # categorical_columns = dataframe.select_dtypes(include=['object', 'category']).columns.to_list()
    categorical_columns = encoder.feature_names_in_
    logger.info(f"Encoding the {categorical_columns} columns.")

    encoded = pd.DataFrame(
        data=encoder.transform(dataframe[categorical_columns]),
        columns=encoder.get_feature_names_out(categorical_columns)
    )

    dataframe = pd.concat([dataframe.drop(columns=categorical_columns), encoded], axis=1)
    return dataframe


def _drop_features(dataframe: pd.DataFrame, features: List) -> pd.DataFrame:

    logger.info(f"drop fratures {features}")
    dataframe = dataframe.copy()
    return dataframe.drop(columns=features, axis=1, errors='ignore').reset_index(drop=True)

def _encode_label(dataframe: pd.DataFrame, label_encoder:LabelBinarizer) -> np.ndarray:
    dataframe = dataframe.copy()
    logger.info(f"Encoding label")
    encoded_data=label_encoder.transform(dataframe)
    return encoded_data


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
# from pprint import pprint
# from pathlib import Path

# df = load_dataset(Path.joinpath(general_settings.DATA_PATH, general_settings.RAW_FILE_NAME), from_aws=False)
# pprint(data_processing_inference(df.head(10)))
