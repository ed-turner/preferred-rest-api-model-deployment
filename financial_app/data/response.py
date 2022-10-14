from datetime import datetime

from pydantic import BaseModel


class PredictionResponseModel(BaseModel):

    id: str
    prediction: float


class ModelChangeStatusResponseModel(BaseModel):

    model_name: str
    changed_at: datetime
