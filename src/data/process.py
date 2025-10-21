"""
Stores data processing functions, such as for cleaning the data, creating new features,
encoding category columns, add on
"""

import os
import pathlib
from typing import List, Dict

import boto3
import pandas as pd
import numpy as np
from loguru import logger
from sklearn.preprocessing import StandardScaler, OneHotEncoder

from ..config.aws import aws_credentials
from ..config.kaggle import kaggle_credentials
from ..config.settings import general_settings
from .util import load_features
from ..config.model import model_settings

def data_processing_inference(datafrane: pd.DataFrame) -> np.ndarray:
    """ Applies the data processing pipeline

    Args:
        dataframe (pd.Dataframe): the dataframe
    
    Return:
        np.ndarray: the news features
    """

    # Step 1: Changing height units
    dataframe = _change_height_units(dataframe)

    # Step 2: Features engineering
    dataframe = _create_bmi_feature(dataframe)
    dataframe = _create_inmm_features(dataframe)

    #Step 3: Features tranformation
    f"Loading 'qcut_bins' (pd.qcut bin edges for splitting 'Age' into quartiles) from path: {general_settings.ARTIFACTS_PATH}"
    age_bins = load_features(
        path=general_settings.ARTIFACTS_PATH,
        features_name="qcut_bins"
    )
    dataframe = _categorize_numerical_columns(dataframe, age_bins)

    dataframe = _transform_numerical_columns(dataframe)

    logger.info(f"Loading feature 'scalers' (instance of StandardScaler) from path {general_settings.ARTIFACTS_PATH}")
    scalers = load_features(
        path=general_settings.ARTIFACTS_PATH,
        features_name='scalers'
    )
    dataframe = _scales_numerical_columns(dataframe, scalers)

    logger.info(f"Loading 'features_encoder' (instance of OneHotEndcoder) from path {general_settings.ARTIFACTS_PATH}")
    features_encoder = load_features(
        path=general_settings.ARTIFACTS_PATH,
        features_name='features_encoder'
    )
    dataframe = _encode_categorical_columns(dataframe, features_encoder)

        # Selecting only the features that are important for the model
    dataframe = dataframe[model_settings.FEATURES]
    logger.info(
        f"Filtering the features columns, keeping only {model_settings.FEATURES} columns."
    )

    features = dataframe.values
    return features



def _change_height_units(dataframe: pd.DataFrame) -> pd.DataFrame:
    """ Changes the Height unit to cetimeters, so will easier to caculate other features from it

    Args:
        dataframe (pd.DataFrame): the dataframe.
    
    Returns:
        pd.DataFrame: the dataframe with the 'height' column transformed.
    """
    logger.info(f"Changing the height units to centimeters.")
    dataframe['Height'] *= 100
    return dataframe

def _create_bmi_feature(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Calculates the Body Mass Index (BMI) feature.

    Args:
        dataframe (pd.DataFrame): the dataframe.

    Returns:
        pd.DataFrame: the dataframe with a new column corresponding to the value of BMI for each data.
    """
    logger.info(f"Creating a new column for the BMI (Body Mass Index) values from data samples.")
    dataframe["BMI"] = dataframe["Weight"] / (dataframe["Height"] ** 2)
    return dataframe

def _create_inmm_features(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Calculates and adds the Ideal Number of Main Meals (INMM) feature.

    Args:
        dataframe (pd.DataFrame): the dataframe.

    Returns:
        pd.DataFrame: The dataframe with a new 'INMM' column.
    """

    logger.info(f"Creating a new column for the IMMM (Ideal Number of Main Meals?) values from data sample.")
    dataframe["INMM"] = dataframe["NCP"] == 3
    dataframe["INMM"] = dataframe["INMM"].astype(int)
    return dataframe

def _transform_numerical_columns(dataframe: pd.DataFrame) -> pd.DataFrame:
    """ Transform the numerical columns using the (Log + 1) transform technique.

    Args:
        dataframe (pd.Dataframe): the dataframe

    Returns:
        pd.Dataframe (pd.Dataframe): the dataframe with all numerical columns tranformed.
    """
    logger.info(f"Tranforming (Log + 1 transfomation) to the {numerical_columns} columns.")
    numerical_columns = dataframe.select_dtypes(include=["number"]).columns.to_list()

    for col in numerical_columns:
        dataframe[col] = np.log1p(dataframe[col])

    return dataframe

def _categorize_numerical_columns(
    dataframe: pd.DataFrame,
    bins: np.ndarray
) -> pd.DataFrame:
    """
    Categorize numerical columns by converting continuous values into discrete categories.

    Args:
        dataframe (pd.DataFrame): Input DataFrame.
        bins (np.ndarray): Bin edges used to split the numerical values into categories.

    Returns:
        pd.DataFrame: DataFrame with the 'Age' column categorized into bins.
    """

    logger.info(f"Categorizing the 'Age' column into discrete categories.")
    dataframe['Age'] = pd.cut(
        x=dataframe['Age'],
        bins=bins,
        labels=['q1', 'q2', 'q3', 'q4']
    )
    dataframe["Age"] = dataframe["Age"].astype("object")
    return dataframe


def _scales_numerical_columns(
        dataframe: pd.DataFrame,
        scalers: Dict[str, StandardScaler]) -> pd.DataFrame:
    """ Scales numerical columns using standard technique

    Args:
        dataframe (pd.Dataframe): the dataframe
        scales (Dict[str, OneHotEncoder]): a dict containing the corresponding encoder for each feature.

    Return:
        dataframe (pd.Dataframe): the dataframe with all numerical columns encoded.
    """
    numerical_columns = dataframe.select_dtypes(include=["number"]).columns.to_list()
    logger.info(f"Scaling the {numerical_columns} columns.")

    for col in numerical_columns:
        dataframe[col] = scalers[col].transform(dataframe[col].to_numpy().reshape(-1,1))
    
    return dataframe

def _encode_categorical_columns(
        dataframe: pd.DataFrame,
        encoder: OneHotEncoder) -> pd.DataFrame:
    """Encodes the categorical columns using the OneHot technique.

    Args:
        dataframe (pd.DataFrame): The DataFrame.
        encoder (OneHotEncoder): A fitted OneHotEncoder.

    Returns:
        pd.DataFrame: DataFrame with categorical columns encoded.
    """
    categorical_columns = dataframe.select_dtypes(include=['object', 'category']).columns.to_list()
    logger.info(f"Ecoding the {categorical_columns} columns.")

    dataframe_with_categorical_columns = pd.DataFrame(
        data=encoder.transform(dataframe[categorical_columns]),
        columns=encoder.get_feature_names_out(categorical_columns)
    )

    new_dataframe = pd.concat([dataframe.drop(labels=categorical_columns, axis=1), dataframe_with_categorical_columns], axis=1)

    return new_dataframe

def _drop_features(dataframe: pd.DataFrame, features: List) -> pd.DataFrame:
    """Excludes features from the given dataframe.

    Args:
        dataframe (pd.DataFrame): the dataframe.

    Returns:
        pd.DataFrame: the dataframe without the given columns.
    """
    return dataframe.drop(columns=features).reset_index(drop=True)

def _load_dataset(
    path: pathlib.Path,
    from_aws: bool
) -> pd.DataFrame:
    """ Load a dataset from a specific path.
    Args:
        path (pathlib.Path): The path where the dataset is located.
        from_aws (bool): whether the dataset is located in an AWS S3 bucket.
    
    Return:
        pa.Dataframe: the dataframe.
    """
    logger.info(f"Loading the dataset from {path}.")

    if not from_aws:
        return pd.read_csv(path)
    
    # Configuring AWS credentials
    os.environ("AWS_ACCESS_KEY_ID") = aws_credentials.AWS_ACCESS_KEY
    os.environ("AWS_SECRET_ACCESS_KEY") = aws_credentials.AWS_SECRET_KEY

    #downloading the dataset
    s3_client = boto3.client(
        "s3",
        aws_access_key_id = aws_credentials.AWS_ACCESS_KEY,
        aws_secret_access_key = aws_credentials.AWS_SECRET_KEY
    )

    local_path = pathlib.Path.joinpath(general_settings.DATA_PATH, path.name())
    s3_client.download_file(
        aws_credentials.S3,
        path.name(),
        local_path
    )

    return _load_dataset(local_path, from_aws=False)