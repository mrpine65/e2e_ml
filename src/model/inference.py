"""
Stores a model serve clas that will be used to make predictions with traned model.
"""

import mlflow
import numpy as np
import pandas as pd
from loguru import logger

from ..config.aws import aws_credentials
from ..config.settings import general_settings
from ..data.utils import load_features
from ..data.processing import data_processing_inference
from ..config.model import model_settings

logger.info(f"Loading 'label_encoder' (instance of LabelBinarizer) from path {general_settings.ARTIFACTS_PATH}.")
label_encoder = load_features(
    path=general_settings.ARTIFACTS_PATH,
    features_name='label_encoder'
)

if aws_credentials.EC2_URL != "YOUR_EC2_INSTANCE_URL":
    mlflow.set_tracking_uri(f"http://{aws_credentials.EC2_URL}:5000")
else:
    mlflow.set_tracking_uri("http://mlflow:5000")

class ModelServe:
    """The trained model's class."""

    def __init__(
        self,
        model_name: str,
        model_flavor: str,
        model_version: str,
    ) -> None:
        """Model's instance initializer.

        Args:
            model_name (str): the model's name.
            model_flavor (str): the model's MLflow flavor.
            model_version (str): the model's version.
        """
        self.model_name = model_name
        self.model_flavor = model_flavor
        self.model_version = model_version
        self.model = None

    @logger.catch
    def load(self) -> None:
        """Loads the trained model.

        Raises:
            NotImplementedError: raises NotImplementedError if the model's flavor value.
        """
        logger.info(
            f"Loading the model {model_settings.MODEL_NAME} with version {model_settings.VERSION}."
        )

        model_uri = f"models:/{model_settings.MODEL_NAME}/{model_settings.VERSION}"

        if self.model_flavor == "lightgbm":
            self.model = mlflow.lightgbm.load_model(model_uri)
        elif self.model_flavor == "sklearn":
            self.model = mlflow.sklearn.load_model(model_uri)
        elif self.model_flavor == "xgboost":
            self.model = mlflow.xgboost.load_model(model_uri)
        elif self.model_flavor == "catboost":
            self.model = mlflow.catboost.load_model(model_uri)
        else:
            logger.critical(
                f"Couldn't load the model using the flavor {model_settings.MODEL_FLAVOR}."
            )
            raise NotImplementedError()

    def predict(
        self, features: pd.DataFrame, transform_to_str: bool = True
    ) -> np.ndarray:
        """Uses the trained model to make a prediction on a given feature array.

        Args:
            features (pd.Dataframe): the dataframe
            transform_to_str (bool): whether to transform the prediction integer to
                string or not. Defaults to True.

        Returns:
            np.ndarray: the predictions array.
        """
        prediction = self.model.predict(features)

        if transform_to_str:
            prediction = label_encoder.classes_[prediction]

        logger.info(f"Prediction: {prediction}.")
        return prediction