"""
Unit test cases to test the model functions code.
"""
# import numpy as np
import pandas as pd

# from sklearn.metrics import f1_score
from xgboost import XGBClassifier
from catboost import CatBoostClassifier
from lightgbm import LGBMClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier

from src.config.model import model_settings
from src.data.processing import data_processing_inference
from src.model.inference import ModelServe
from .. import loaded_model


def test_load_model() -> None:
    """
    Unit case to test loading a trained model from MLflow.
    """
    assert loaded_model.model is not None
    if model_settings.MODEL_FLAVOR == "xgboost":
        assert isinstance(loaded_model.model, XGBClassifier)
    elif model_settings.MODEL_FLAVOR == "lightgbm":
        assert isinstance(loaded_model.model, LGBMClassifier)
    elif model_settings.MODEL_FLAVOR == "sklearn":
        assert isinstance(loaded_model.model, RandomForestClassifier) or isinstance(loaded_model.model, DecisionTreeClassifier)
    elif model_settings.MODEL_FLAVOR == "catboost":
        assert isinstance(loaded_model.model, CatBoostClassifier)


def test_prediction() -> None:
    """
    Unit case to test making a prediction with the loaded model.
    """
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
    correct_prediction = "Overweight_Level_I"

    data = pd.DataFrame.from_dict([data])
    features = data_processing_inference(data)
    prediction = loaded_model.predict(features).tolist()[0]

    assert isinstance(prediction, str)
    assert prediction == correct_prediction