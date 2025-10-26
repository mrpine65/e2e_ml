"""
Creates a Person schema with Pydantic's BaseModel, which will be used to
validate the parameter values when passed to the API.
"""

from typing import Literal
from pydantic import BaseModel, Field


class Person(BaseModel):
    """
    Person schema.
    """

    Age: float = Field( gt=0, le=100, description="The person's age.")
    Height: float = Field( gt=0.0, le=2.5, description="The person's height (in meters).")
    Weight: float = Field( gt=0, le=400, description="The person's weight (in kilos).")
    Gender: Literal["Male", "Female"] = Field(
        description="The person's gender."
    )
    CALC: Literal["Frequently", "Sometimes", "no"] = Field(
        description="The person's consumption of alcohol (CALC)."
    )
    FAVC: Literal["yes", "no"] = Field(
        description="The person's frequent consumption of high caloric food (FAVC)."
    )
    family_history_with_overweight: Literal["yes", "no"] = Field(
        description="Whether the person's family has a history with overweight."
    )
    MTRANS: Literal[ "Public_Transportation", "Automobile", "Walking", "Motorbike", "Bike", ] = Field( 
        description="The person's main mode of transportation (MTRANS)."
    )
    FCVC: float = Field( gt=0, le=5, description="Frequency of consumption of vegetables (FCVC).")
    NCP: float = Field( ge=0, le=4, description="The person's number of main meals (NCP).")
    CH2O: float = Field( ge=1, le=3, description="The person's daily water consumption (CH2O).")
    FAF: float = Field( ge=0, le=3, description="The person's physical activity frequency (FAF).")
    TUE: int = Field( ge=0, le=2, description="Time using technology devices (TUE).")
    CAEC: Literal["Frequently", "Sometimes", "Always", "no"] = Field(
        description="The person's consumption of food between meals (CAEC).",
    )
    SCC: Literal["yes", "no"] = Field(
        description="Whether the person monitors their calorie consumption (SCC)."
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "Age": 24.443011,
                    "Height": 1.699998,
                    "Weight": 81.66995,
                    "Gender": "Male",
                    "family_history_with_overweight": "yes",
                    "CALC": "Sometimes",
                    "MTRANS": "Public_Transportation",
                    "FAVC": "yes",
                    "FCVC": 2,
                    "NCP": 2.98,
                    "CH2O": 2.76,
                    "FAF": 0,
                    "TUE": 1,
                    "CAEC": "Sometimes",
                    "SCC": "no",
                }
            ]
        }
    }
