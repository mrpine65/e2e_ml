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
    SMOKE: Literal["yes", "no"] = Field(
        description="Whether the person smokes (SMOKE)."
    )
    SCC: Literal["yes", "no"] = Field(
        description="Whether the person monitors their calorie consumption (SCC)."
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "Gender": "Female",
                    "Age": 18.0,
                    "Height": 1.56,
                    "Weight": 57.0,
                    "family_history_with_overweight": "yes",
                    "FAVC": "yes",
                    "FCVC": 2.0,
                    "NCP": 3.0,
                    "CAEC": "Frequently",
                    "SMOKE": "no",
                    "CH2O": 2.0,
                    "SCC": "no",
                    "FAF": 1.0,
                    "TUE": 1.0,
                    "CALC": "no",
                    "MTRANS": "Automobile",
                }
            ]
        }
    }
