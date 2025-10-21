"""
Stores auxiliary functions (such as for loading features or downloading the dataset)
that will be used with main processing functions.
"""

import os
import pickle
import pathlib
from typing import Union

import boto3
import numpy as np
from loguru import logger
from sklearn.preprocessing import OneHotEncoder, StandardScaler, LabelEncoder

from ..config.aws import aws_credentials
from ..config.kaggle import kaggle_credentials


def load_features(
    path: pathlib.Path,
    features_name: str
) -> Union[np.ndarray, OneHotEncoder, StandardScaler, LabelEncoder]:
    """
    Loads a given feature (might be a NumPy array or a Scikit-learn encoder/scaler).

    Args:
        path (pathlib.Path): The path of the desired feature.
        features_name (str): The feature file's name.

    Returns:
        Union[np.ndarray, StandardScaler, OneHotEncoder]: The feature's content.
    """
    
    with open(pathlib.Path.joinpath(path, f"{features_name}.pkl"), "rb") as f:
        loaded = pickle.load(f)

    return loaded


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
        os.system(f"mv ObesityDataSet.csv {pathlib.Path.joinpath(path, new_name)}")
    elif file_type == "raw":
        os.system(f"kaggle competitions download -c {name}")
        os.system(f"unzip {name}.zip")
        os.system(f"rm {name}.zip sample_submission.csv test.csv")
        os.system(f"mv train.csv {pathlib.Path.joinpath(path, new_name)}")
    else:
        raise ValueError("The value for 'file_type' must be 'raw' or 'current'.\n")

    # Sending the dataset to the AWS S3 bucket
    if send_to_aws:
        if aws_credentials.S3 != "YOUR_S3_BUCKET_URL":
            send_dataset_to_s3(
                file_path=path,
                file_name=new_name,
            )
        else:
            logger.warning(
                "The S3 Bucket URL was not specified in the 'credentials.yaml' file. "
                "Therefore, the dataset will not be sent to S3 and it will be kept saved locally."
            )


@logger.catch
def send_dataset_to_s3(
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
