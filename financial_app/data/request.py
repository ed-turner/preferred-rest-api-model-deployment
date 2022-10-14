from pydantic import BaseModel


class OfferRequestPydanticModel(BaseModel):

    lead_id: str
    lender_id: int
    offer_id: int
    apr: float
