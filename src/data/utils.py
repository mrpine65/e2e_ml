"""
Stores auxiliary functions (such as for loading features or downloading the dataset)
that will be used with main processing functions.
"""

import os
import pickle
import pathlib
from typing import Union
from zipfile import ZipFile
import shutil

import boto3
import numpy as np
from loguru import logger
from sklearn.preprocessing import OneHotEncoder, StandardScaler, LabelEncoder

from ..config.settings import general_settings
from ..config.aws import aws_credentials
from ..config.kaggle import kaggle_credentials


def load_features(
    path: pathlib.Path,
    features_name: str,
    from_aws: bool
) -> Union[np.ndarray, OneHotEncoder, StandardScaler, LabelEncoder]:
    """
    Loads a feature file from local storage or AWS S3.

    Args:
        path: Path to the feature directory.
        features_name: Name of the feature file (without extension).
        from_aws: Whether to load the file from AWS S3.

    Returns:
        The loaded feature object (NumPy array or Scikit-learn transformer).
    """
    if not from_aws:
        with open(pathlib.Path.joinpath(path, f"{features_name}.pkl"), "rb") as f:
            loaded = pickle.load(f)
        return loaded
    
    os.environ["AWS_ACCESS_KEY_ID"] = aws_credentials.AWS_ACCESS_KEY
    os.environ["AWS_SECRET_ACCESS_KEY"] = aws_credentials.AWS_SECRET_KEY

    s3_client = boto3.client(
        "s3",
        aws_access_key_id=aws_credentials.AWS_ACCESS_KEY,
        aws_secret_access_key=aws_credentials.AWS_SECRET_KEY
    )

    local_path = pathlib.Path.joinpath(path, f"{features_name}.pkl")
    s3_client.download_file(aws_credentials.S3, f"{features_name}.pkl", local_path)
    return load_features(path, features_name, from_aws=False)


def save_feature(
    path: pathlib.Path,
    name: str,
    feature: any,
    send_to_aws: bool
) -> None:
    """
    Saves a feature locally and optionally uploads it to AWS S3.

    Args:
        path: Path to save the feature.
        name: Feature file name.
        feature: Feature object to save.
        send_to_aws: Whether to upload the file to AWS S3.
    """
    with open(pathlib.Path.joinpath(path, f"{name}.pkl"), 'wb') as f:
        pickle.dump(feature, f)
    logger.info(f"Saved {name}.pkl")
    if send_to_aws:
        if aws_credentials.S3 != "YOUR_S3_BUCKET_URL":
            send_to_s3(file_path=path, file_name=f"{name}.pkl")
            logger.info(f"Send {name} to aws.")
    else:
        logger.warning(
            "S3 bucket URL not specified. The feature will be saved locally only."
        )

@logger.catch
def download_dataset(
    name: str,
    new_name: str,
    path: pathlib.Path,
    send_to_aws: bool,
    file_type: str
) -> None:
    """
    Download the dataset using Kaggle's API.

    Args:
        name (str): The dataset's name.
        new_name (str): The dataset file's new name.
        path (pathlib.Path): The path where the dataset will be stored locally.
        send_to_aws (bool): Whether the dataset will be sent to an AWS S3 bucket or not.
        file_type (str): The kind of dataset to download ('raw' or 'current').
    """
    os.environ["KAGGLE_USERNAME"] = kaggle_credentials.KAGGLE_USERNAME
    os.environ["KAGGLE_KEY"] = kaggle_credentials.KAGGLE_KEY

    logger.info(f"Downloading dataset {name} and saving into the folder {path}.")

    # Downloading data using the Kaggle API through the terminal
    if file_type == "current":
        os.system(f"kaggle datasets download -d {name} --unzip")
        shutil.move("ObesityDataSet.csv", pathlib.Path(path) / general_settings.CURRENT_FILE_NAME)
    elif file_type == "raw":
        os.system(f"kaggle competitions download -c {name}")
        with ZipFile(f"{name}.zip", 'r') as zip_ref:
            zip_ref.extractall()
        os.remove(f"{name}.zip")
        for f in ["sample_submission.csv", "test.csv"]:
            os.remove(f)
        shutil.move("train.csv", pathlib.Path(path) / new_name)
    else:
        raise ValueError("The value for 'file_type' must be 'raw' or 'current'.\n")

    # Sending the dataset to the AWS S3 bucket
    if send_to_aws:
        if aws_credentials.S3 != "YOUR_S3_BUCKET_URL":
            send_to_s3(
                file_path=path,
                file_name=new_name,
            )
        else:
            logger.warning(
                "The S3 Bucket URL was not specified in the 'credentials.yaml' file. "
                "Therefore, the dataset will not be sent to S3 and it will be kept saved locally."
            )


@logger.catch
def send_to_s3(
    file_path: pathlib.Path,
    file_name: str,
) -> None:
    """
    Sends a given dataset to the AWS S3 bucket.

    Args:
        file_path (pathlib.Path): The dataset file's path.
        file_name (str): The file's name.
    """
    bucket = boto3.client(
        "s3",
        aws_access_key_id=aws_credentials.AWS_ACCESS_KEY,
        aws_secret_access_key=aws_credentials.AWS_SECRET_KEY,
    )

    bucket.upload_file(
        str(pathlib.Path.joinpath(file_path, file_name)),
        aws_credentials.S3,
        file_name,
    )

    os.remove(pathlib.Path.joinpath(file_path, file_name))
