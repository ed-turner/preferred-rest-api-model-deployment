# Financial Application

The goal is to:

    1. Load Data into a DB
    2. Create "High-Level" Features, and Label from the Data
    3. Train two logistic regressions on the data
    4. Deploy model servers and a web server to handle processing requests

# Installation Guide

For all of these tools, you will need:

    1. Python 3.8
    2. Docker
    3. An IDE like PyCharm

# Tutorial

## From the Go

    1. Unzip file
    2. Run make.install.all
    3. Run Docker Desktop
    4. Run make deploy.image.build.lasso
    5. Run make deploy.image.build.ridge
    6. Run the bash script ./test.sh

## From Scratch

Follow these steps before continuing:

    1. init the entire project and Install your requirements
    2. Update the .profile.env with th appropirate *DATA_LOC variables 
    3. Upload data into the SQLite DB 

The first point is done by `make init`, `make.init.data.loc`, `make install.all`, `make init.data.load` and `init.data.tables`.
The second point must be done manually. 

Afterwards, you want to train the model. This is done by running
`mlflow.server.launch` in one open terminal tab and `make model.train` in the other.

These will generate the models required for the serving component.
Each model will be stored under a folder similar to `data/models/{EXPERIMENT_ID}/{RUN_ID}/artifacts/best_{MODEL_NAME}`.
Set `MLFLOW_{MODEL_LABEL}_MODEL_URI` with the appropriate `data/models/{EXPERIMENT_ID}/{RUN_ID}/artifacts/best_{MODEL_NAME}`
Afterwards, execute `make deploy.image.build.lasso` and `make deploy.image.build.ridge` to build the docker images.

If changes were made to the `*_MODEL_URI`, `DB_URI` or `MLFLOW_DB_URI`, then need to be updated in the
`docker-compose.yml` in their respective places. 

Finally, run the `test.sh`

The docker-compose also uses prometheus, which helps captures HTTP metrics for each of the micro-services

# Additional Notes

There are a few considerations to make sure this is a more production ready application design

    1. Use remote Docker repositories (e.g. AWS ECR, Google Container Registry, Artifactory)
    2. Use remote SQL Database (e.g. Postgres on AWS Redshift, AWS RDS)
    3. Ensure there is a process to train the model in a remote compute environment 
        (e.g. AWS EC2, Google Compute Engine)
    4. Ensure we are using a remote object storage for the model registry 
        (e.g AWS S3, Google Cloud Service)
    5. Use Kubernetes instead of docker-compose for deploying the services, 
        which enables auto-scaling (up or down) of each of these services
    6. Use MLServer to optimize model runtime performance
    7. Resource Usage Metrics for Logging, Monitoring, Alerting defined on each micro-service
    8. Error Status Code Metrics for Alerting define on each micro-service
    9. Add a dedicated CI/CD Pipeline for testing the code, and then deployment
