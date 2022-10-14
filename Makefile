ifneq (,$(wildcard ./.profile.env))
	include .profile.env
	export
endif

init:
	pip install --upgrade pip
	pip install --upgrade poetry
	poetry init

init.data.loc:
	mkdir data
	mkdir data/db
	mkdir data/models

init.data.tables:
	poetry run python -m financial_app.data.sql.init

init.data.load:
	poetry run python -m financial_app.data.sql.load --dataLoc=${OFFER_DATA_LOC} --tableName=offers
	poetry run python -m financial_app.data.sql.load --dataLoc=${CLICKED_OFFER_DATA_LOC} --tableName=clicked_offers
	poetry run python -m financial_app.data.sql.load --dataLoc=${LEADS_DATA_LOC} --tableName=leads

install.all:
	poetry install -E serving -E training

install.training:
	poetry install -E training

install.serving:
	poetry install -E serving

model.train:
	poetry run python -m financial_app.ml.training

deploy.image.build.lasso:
	poetry run mlflow models build-docker --model-uri ${MLFLOW_LASSO_MODEL_URI} --name "lasso-log"

deploy.image.build.ridge:
	poetry run mlflow models build-docker --model-uri ${MLFLOW_RIDGE_MODEL_URI} --name "ridge-log"

requirements.add:
	poetry add $(argument)

mlflow.server.launch:
	poetry run mlflow server --backend-store-uri ${MLFLOW_DB_URI} --default-artifact-root ${MLFLOW_ARTIFACT_URI}

app.server.build:
	poetry build --format wheel

api.server.launch:
	poetry run uvicorn financial_app.api.__main__:create_app

clean:
	rm -r data
