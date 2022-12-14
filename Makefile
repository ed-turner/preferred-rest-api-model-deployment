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

deploy.image.build.gbdt:
	poetry run mlflow models build-docker --model-uri ${MLFLOW_GBDT_MODEL_URI} --name "gbdt"

requirements.add:
	poetry add $(argument)

mlflow.server.launch:
	poetry run mlflow server --backend-store-uri ${MLFLOW_DB_URI} --default-artifact-root ${MLFLOW_ARTIFACT_URI}

app.server.build:
	poetry build --format wheel

clean:
	rm -r data


migrate.init:
	poetry run alembic init alembic

migrate:
	poetry run alembic revision --autogenerate -m $(argument)
	poetry run alembic upgrade head

k8s.init.mac:
	curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/darwin/amd64/kubectl"

k8s.test.init:

	kubectl config get-contexts
	kubectl config use-context docker-desktop

	kubectl apply -f ./k8s/gbdt
	kubectl apply -f ./k8s/lassolog
	kubectl apply -f ./k8s/ridgelog
	kubectl apply -f ./k8s/db
	kubectl apply -f ./k8s/app
	kubectl apply -f ./k8s/promstats
	kubectl apply -f ./k8s/prometheus
	kubectl get pods
	kubectl get services --sort-by=.metadata.name
	# kubectl port-forward svc/app 8000:8000 &
	# kubectl port-forward svc/prometheus-service 8080:8080 --namespace monitoring &


k8s.test.clean:
	kubectl delete all --all
