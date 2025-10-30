"""
Monitoring's schema.
"""
from pydantic import BaseModel, Field

class Monitoring(BaseModel):
    """
    Monitoring schema.
    """
    windown_size: int = Field(default=300, gt=0, description="The window size. Defaults to 300." )
    