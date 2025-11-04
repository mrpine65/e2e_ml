import warnings
from datetime import datetime
from pathlib import Path
from typing import Tuple, Literal

import mlflow
import numpy as np
import optuna
import pandas as pd
from datetime import datetime, timezone
from catboost import CatBoostClassifier
from lightgbm import LGBMClassifier
from mlflow.models import infer_signature
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from xgboost import XGBClassifier

from src.config.settings import general_settings
from src.config.aws import aws_credentials
from src.data.processing import (
    data_processing_inference,
    label_processing_inference,
    load_dataset,
)
from src.data.utils import download_dataset
import logging

warnings.filterwarnings("ignore")
logging.getLogger("mlflow").setLevel(logging.ERROR)

mlflow.set_tracking_uri(f"http://{aws_credentials.EC2_URL}:5000")


# ---------------------------------------------------------------------
# Data Pipeline
# ---------------------------------------------------------------------
class DataPipeline:
    """Responsible for downloading, loading, and processing the dataset."""

    def __init__(self, dataset_name: str, raw_name: str, data_path: Path, file_type: Literal["raw", "current"] = "raw"):
        self.dataset_name = dataset_name
        self.raw_name = raw_name
        self.data_path = data_path
        self.file_type = file_type

    def prepare_data(self) -> Tuple[pd.DataFrame, pd.DataFrame, np.ndarray, np.ndarray]:
        """Download, load and preprocess data for training and validation."""
        # Download dataset
        download_dataset(
            name=self.dataset_name,
            new_name=self.raw_name,
            path=self.data_path,
            send_to_aws=True,
            file_type=self.file_type
        )

        # Load dataset
        df = load_dataset(
            Path.joinpath(self.data_path, self.raw_name),
            from_aws=True,
        )

        # Split data
        X = df.drop("NObeyesdad", axis=1)
        y = df["NObeyesdad"]

        X_train, X_val, y_train, y_val = train_test_split(
            X, y, train_size=0.8, stratify=y, random_state=42
        )

        # Reset index
        X_train, X_val = X_train.reset_index(drop=True), X_val.reset_index(drop=True)
        y_train, y_val = y_train.reset_index(drop=True), y_val.reset_index(drop=True)

        # Processing
        X_train = data_processing_inference(X_train, is_train=True)
        X_val = data_processing_inference(X_val, is_train=False)
        y_train = label_processing_inference(y_train, is_train=True)
        y_val = label_processing_inference(y_val, is_train=False)

        return X_train, X_val, y_train, y_val


# ---------------------------------------------------------------------
# Objective Class for Optuna Optimization
# ---------------------------------------------------------------------
class Objective:
    def __init__(
        self,
        run_name: str,
        experiment_id: str,
        X_train: pd.DataFrame,
        y_train: np.ndarray,
        X_valid: pd.DataFrame,
        y_valid: np.ndarray,
    ) -> None:
        self.run_name = run_name
        self.experiment_id = experiment_id
        self.X_train = X_train
        self.y_train = y_train
        self.X_valid = X_valid
        self.y_valid = y_valid
        self.SEED = 42

        if self.run_name in ["decision_tree", "lightgbm", "catboost"]:
            self.y_train = np.argmax(self.y_train, axis=1)
            self.y_valid = np.argmax(self.y_valid, axis=1)

    def __call__(self, trial: optuna.trial.Trial) -> float:
        with mlflow.start_run(experiment_id=self.experiment_id, nested=True):
            # ----------------------------------------------------------
            # Model Selection and Hyperparameter Search
            # ----------------------------------------------------------
            if self.run_name == "decision_tree":
                params = {
                    "max_depth": trial.suggest_int("max_depth", 2, 32, step=2),
                    "min_samples_split": trial.suggest_int("min_samples_split", 2, 8, step=1),
                    "min_samples_leaf": trial.suggest_int("min_samples_leaf", 1, 6, step=1),
                    "min_weight_fraction_leaf": trial.suggest_float(
                        "min_weight_fraction_leaf", 0, 0.5, step=0.1
                    ),
                    "max_leaf_nodes": trial.suggest_int("max_leaf_nodes", 2, 16, step=2),
                    "random_state": self.SEED,
                }
                model = DecisionTreeClassifier(**params)

            elif self.run_name == "random_forest":
                params = {
                    "n_estimators": trial.suggest_int("n_estimators", 100, 1000),
                    "max_depth": trial.suggest_int("max_depth", 10, 50),
                    "min_samples_split": trial.suggest_int("min_samples_split", 2, 32),
                    "min_samples_leaf": trial.suggest_int("min_samples_leaf", 1, 32),
                    "random_state": self.SEED,
                    "n_jobs": -1,
                }
                model = RandomForestClassifier(**params)

            elif self.run_name == "xgboost":
                params = {
                    "booster": trial.suggest_categorical("booster", ["gbtree", "gblinear", "dart"]),
                    "lambda": trial.suggest_float("lambda", 1e-8, 1.0, log=True),
                    "alpha": trial.suggest_float("alpha", 1e-8, 1.0, log=True),
                    "random_state": self.SEED,
                    "n_jobs": -1,
                }
                model = XGBClassifier(**params)

            elif self.run_name == "lightgbm":
                params = {
                    "objective": "multiclass",
                    "verbosity": -1,
                    "random_state": self.SEED,
                    "n_jobs": -1,
                    "lambda_l1": trial.suggest_float("lambda_l1", 1e-8, 10.0, log=True),
                    "lambda_l2": trial.suggest_float("lambda_l2", 1e-8, 10.0, log=True),
                    "num_leaves": trial.suggest_int("num_leaves", 2, 256),
                    "feature_fraction": trial.suggest_float("feature_fraction", 0.4, 1.0),
                    "bagging_fraction": trial.suggest_float("bagging_fraction", 0.4, 1.0),
                    "bagging_freq": trial.suggest_int("bagging_freq", 1, 7),
                    "min_child_samples": trial.suggest_int("min_child_samples", 5, 100),
                }
                model = LGBMClassifier(**params)

            elif self.run_name == "catboost":
                params = {
                    "random_seed": self.SEED,
                    "verbose": 0,
                    "allow_writing_files": False,
                    "colsample_bylevel": trial.suggest_float("colsample_bylevel", 0.01, 0.1),
                    "depth": trial.suggest_int("depth", 1, 12),
                    "boosting_type": trial.suggest_categorical("boosting_type", ["Ordered", "Plain"]),
                    "bootstrap_type": trial.suggest_categorical(
                        "bootstrap_type", ["Bayesian", "Bernoulli", "MVS"]
                    ),
                }
                model = CatBoostClassifier(**params)


            model.fit(X=self.X_train, y=self.y_train)

            # Training F1
            train_prediction = model.predict(self.X_train)
            train_f1 = f1_score(self.y_train, train_prediction, average="weighted")

            # Validation F1
            valid_prediction = model.predict(self.X_valid)
            valid_f1 = f1_score(self.y_valid, valid_prediction, average="weighted")

            # Log metrics
            mlflow.log_metric("train_f1", train_f1)
            mlflow.log_metric("valid_f1", valid_f1)

            # Infer model signature
            signature = infer_signature(self.X_train, train_prediction)

            # ----------------------------------------------------------
            # Model Logging by Framework
            # ----------------------------------------------------------
            if self.run_name in ["decision_tree", "random_forest"]:
                mlflow.sklearn.log_model(model, self.run_name, signature=signature)
                mlflow.log_params(model.get_params(deep=True))

            elif self.run_name == "xgboost":
                mlflow.xgboost.log_model(model, self.run_name, signature=signature)
                mlflow.log_params(model.get_params())

            elif self.run_name == "lightgbm":
                mlflow.lightgbm.log_model(model, self.run_name, signature=signature)
                mlflow.log_params(model.get_params())

            elif self.run_name == "catboost":
                mlflow.catboost.log_model(model, self.run_name, signature=signature)
                mlflow.log_params(model.get_all_params())

        return valid_f1

pipeline = DataPipeline(
    dataset_name="playground-series-s4e2",
    raw_name=general_settings.RAW_FILE_NAME,
    data_path=general_settings.DATA_PATH,
    file_type="raw"
)

X_train, X_val, y_train, y_val = pipeline.prepare_data()

now = datetime.now(timezone.utc)
formatted_time = now.strftime("%Y-%m-%d_%H-%M-%S_UTC")
experiment_name = f"obesity_classification_{formatted_time}"
experiment_id = mlflow.create_experiment(name=experiment_name)

for run_name in ["lightgbm", "decision_tree", "random_forest", "xgboost", "catboost"]:
    with mlflow.start_run(experiment_id=experiment_id, run_name=run_name):
        objective = Objective(
            run_name=run_name,
            experiment_id=experiment_id,
            X_train=X_train,
            y_train=y_train,
            X_valid=X_val,
            y_valid=y_val,
        )

        study = optuna.create_study(direction="maximize")
        study.optimize(objective, n_trials=30)
