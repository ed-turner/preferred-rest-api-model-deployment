import uuid
from datetime import datetime

from sqlalchemy import Float, String, Column, Integer, DateTime

from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Leads(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True)
    lead_uuid = Column(String)
    requested = Column(Float)
    loan_purpose = Column(String)
    credit = Column(String)
    annual_income = Column(Float)


class ClickedOffers(Base):
    # this is the ds_clicks.parquet.gzip dataset
    __tablename__ = "clicked_offers"
    id = Column(Integer, primary_key=True)
    offer_id = Column(Integer, primary_key=True)
    clicked_at = Column(DateTime)


class Offers(Base):
    # This is from ds_offers.parquet.gzip
    __tablename__ = "offers"

    id = Column(Integer, primary_key=True)

    apr = Column(Float)
    lender_id = Column(Integer)  # this is from a lender DB Table

    offer_id = Column(Integer)
    lead_uuid = Column(String)


class ModelChangeAuditHistory(Base):
    __tablename__ = "model_change_audit_history"

    id = Column(String, primary_key=True, default=lambda _: uuid.uuid4().hex)
    changed_at = Column(DateTime, default=datetime.utcnow)
    model_name = Column(String)


class Predictions(Base):

    __tablename__ = "offer_click_predictions"
    id = Column(String, primary_key=True, default=lambda _: uuid.uuid4().hex)

    prediction = Column(Float)
    offer_id = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    model_name = Column(String)
