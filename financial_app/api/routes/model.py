from typing import Callable, Optional
import json

from fastapi import Depends, HTTPException
from fastapi.routing import APIRouter

import httpx

from sqlalchemy.sql import select
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio.result import AsyncResult

from financial_app.data.request import OfferRequestPydanticModel
from financial_app.data.response import PredictionResponseModel, ModelChangeStatusResponseModel
from financial_app.data.sql.orm import Leads, Predictions, ModelChangeAuditHistory
from financial_app.settings import ServingSettings


def define_model_routes(get_session: Callable, settings: ServingSettings) -> APIRouter:
    """

    :param get_session:
    :param settings:
    :return:
    """

    model_router = APIRouter()

    @model_router.get("/status")
    async def model_status(session: AsyncSession = Depends(get_session)) -> ModelChangeStatusResponseModel:
        """

        :return:
        """
        stmt = select(ModelChangeAuditHistory).order_by(
            ModelChangeAuditHistory.changed_at.desc()
        )

        model_change_name: ModelChangeAuditHistory = (await session.execute(stmt)).first()

        if model_change_name is None:
            # this is the default model to work with
            model_change_name = ModelChangeAuditHistory(model_name="even-financial-ridge-log")

            session.add(model_change_name)
            await session.flush()
            await session.commit()
        else:
            model_change_name = model_change_name[0]

        response = ModelChangeStatusResponseModel(
            model_name=model_change_name.model_name,
            changed_at=model_change_name.changed_at
        )

        return response

    @model_router.post("/change")
    async def model_change(model_name: str, session: AsyncSession = Depends(get_session)):
        """

        :return:
        """

        # TODO This is temporary.  Later we will remove this

        if model_name in ["ridge-log", "lasso-log"]:
            model_change_name = ModelChangeAuditHistory(model_name=model_name)

            session.add(model_change_name)
            await session.commit()

        else:
            raise HTTPException(404, detail="The model name is not one of the two we will use in production")

    @model_router.post("/inference")
    async def model_inference(
            data: OfferRequestPydanticModel, session: AsyncSession = Depends(get_session),
            override_model_name: Optional[str] = None
    ) -> PredictionResponseModel:
        """

        :return:
        """
        # the offer id was added to the signature of the model but was not
        # used by the model.  Need to remove this later
        data_dict = {"apr": data.apr, "lender_id": data.lender_id}

        stmt = select(Leads).filter(
            Leads.lead_uuid == data.lead_id
        )

        lead_data = (await session.execute(stmt)).first()

        if lead_data is None:
            raise HTTPException(404, detail="The lead data is missing")
        else:
            lead_data = lead_data[0]

        data_dict["requested"] = lead_data.requested
        data_dict["credit"] = lead_data.credit
        data_dict["annual_income"] = lead_data.annual_income
        data_dict["loan_purpose"] = lead_data.loan_purpose

        if override_model_name:
            model_name = override_model_name
        else:
            stmt = select(ModelChangeAuditHistory).order_by(
                ModelChangeAuditHistory.changed_at.desc()
            )

            model_change_name: ModelChangeAuditHistory = (await session.execute(stmt)).first()

            if model_change_name:
                model_name = model_change_name[0].model_name
            else:
                raise HTTPException(404, detail="""
                The production model has to be set. 
                This can be done so with a curl to the '/model/status' path
                """)

        if model_name == "even-financial-ridge-log":
            http_url = settings.RIDGE_MODEL_URI
        else:
            http_url = settings.LASSO_MODEL_URI

        _data = {"instances": [data_dict]}

        async with httpx.AsyncClient() as client:

            response = await client.post(
                url=http_url, data=json.dumps(_data),
                headers={"Content-Type": "application/json;"}
            )

            predicted_class = response.json()[0][1]

        pred_db: Predictions = Predictions(
            prediction=predicted_class,
            model_name=model_name,
            offer_id=data.offer_id
        )

        session.add(pred_db)

        await session.flush()

        response = PredictionResponseModel(id=pred_db.id, prediction=predicted_class)

        await session.commit()

        return response

    return model_router
