from typing import List

import logging

import mlflow
from mlflow.models.signature import infer_signature

import numpy as np
import pandas as pd

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from sklearn import clone
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, PowerTransformer, RobustScaler, OrdinalEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import f1_score, roc_auc_score

from skopt import BayesSearchCV
from skopt.space import Real, Integer

from financial_app.data.sql.orm import Leads, ClickedOffers, Offers
from financial_app.settings import TrainingSettings

logger = logging.getLogger(__name__)


def assemble_training_data(db_uri: str) -> pd.DataFrame:
    """
    This will assemble the training data from the defined query below

    :return: The data we will use for training
    """
    engine = create_engine(db_uri)

    session_maker = sessionmaker(engine)

    with session_maker() as session:
        query = session.query(
            Offers,
            Leads.requested,
            Leads.loan_purpose,
            Leads.credit,
            Leads.annual_income,
            ClickedOffers.clicked_at
        ).join(
            Leads, Offers.lead_uuid == Leads.lead_uuid
        ).join(
            ClickedOffers, ClickedOffers.offer_id == Offers.offer_id, isouter=True
        )

        data = pd.read_sql_query(
            sql=query.statement,
            con=engine
        )

    # the label is to predict whether someone clicked it or now
    # which means the clicked_at must be nonnull
    data["label"] = 1 - data["clicked_at"].isnull().astype(int)

    return data


def init_tree_feature_pipeline():
    """

    :return:
    """
    return ColumnTransformer(
        [
            (
                "categorical_features",
                OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=np.nan),
                ["lender_id", "credit", "loan_purpose"]
             ),
        ],
        remainder="passthrough"
    )


def init_feature_pipeline():
    """
    This is to create a feature engineering pipeline, which will normalize and standardize the data

    :return: A column transformer
    """
    return ColumnTransformer(
        [
            ("lender_one_hot", OneHotEncoder(drop="if_binary", handle_unknown="ignore"), ["lender_id"]),
            ("credit_one_hot", OneHotEncoder(drop="if_binary", handle_unknown="ignore"), ["credit"]),
            ("loan_purpose_hot", OneHotEncoder(drop="if_binary", handle_unknown="ignore"), ["loan_purpose"]),
            (
                "numeric_scaler",
                Pipeline(
                    steps=[
                        # but we will make it simple and look for closest 2 neighbors
                        ("power_transform", PowerTransformer(standardize=False)),
                        ("robust_scale", RobustScaler()),
                        ("data_impute", SimpleImputer(strategy="constant", fill_value=0, add_indicator=True)),
                    ]
                ),
                ["requested", "annual_income", "apr"]
            )
        ]
    )


def init_gbdt_classification():
    return BayesSearchCV(
        refit=True,
        estimator=Pipeline(
            [
                ("feature_engineering_pipeline", init_tree_feature_pipeline()),
                (
                    "clf",
                    CalibratedClassifierCV(
                        base_estimator=HistGradientBoostingClassifier(
                                categorical_features=range(3),
                                early_stopping=False,
                                validation_fraction=None
                            ),
                        cv=5
                    )
                )
            ],
        ),
        search_spaces={
            "clf__base_estimator__learning_rate": Real(1e-16, 1, prior='log-uniform'),
            "clf__base_estimator__l2_regularization": Real(1e-16, 1e16, prior='log-uniform'),
            "clf__base_estimator__max_depth": Integer(1, 10),
            "clf__base_estimator__max_iter": Integer(100, 500)
        },
        cv=5,
        scoring="roc_auc",
        n_iter=50,
        verbose=1
    )


def init_lasso_logistic_regression():
    return BayesSearchCV(
        estimator=Pipeline(
            [
                ("feature_engineering_pipeline", init_feature_pipeline()),
                ("logistic_regression", LogisticRegression(penalty="l1", solver="saga"))
            ],
        ),
        search_spaces={"logistic_regression__C": Real(1e-16, 1e16, prior='log-uniform')},
        cv=5,
        scoring="roc_auc",
        n_iter=50
    )


def init_ridge_logistic_regression():
    return BayesSearchCV(
        estimator=Pipeline(
            [
                ("feature_engineering_pipeline", init_feature_pipeline()),
                ("logistic_regression", LogisticRegression(penalty="l2", solver="saga"))
            ],
        ),
        search_spaces={"logistic_regression__C": Real(1e-16, 1e16, prior='log-uniform')},
        cv=5,
        scoring="roc_auc",
        n_iter=50
    )


def train_model(
        grid_search_model,
        data: pd.DataFrame,
        feature_cols: List[str],
        label_col: str,
        model_name: str,
        experiment_name: str
):

    experiment = mlflow.set_experiment(experiment_name)

    grid_search_model.fit(data[feature_cols], data[label_col])

    result_df = pd.DataFrame.from_dict(grid_search_model.cv_results_)

    print(result_df.head(2).to_string())

    for i in range(result_df.shape[0]):

        with mlflow.start_run():
            mlflow.log_metric(
                "mean_test_score",
                result_df.loc[i, "mean_test_score"]
            )

            mlflow.log_metric(
                "std_test_score",
                result_df.loc[i, "std_test_score"]
            )

            mlflow.log_params(result_df.loc[i, "params"])

            mlflow.log_param("rank_test_score", result_df.loc[i, "rank_test_score"])

    model = grid_search_model.best_estimator_

    train_pred = model.predict_proba(data[feature_cols])

    signature = infer_signature(
        data[feature_cols],
        train_pred
    )

    # manually overriding the predict method for the predict_proba method
    model.predict = model.predict_proba

    with mlflow.start_run():
        mlflow.sklearn.log_model(
            model,
            model_name,
            signature=signature
        )

        mlflow.log_metric(
            "calibrated_roc_auc",
            roc_auc_score(
                data[label_col],
                train_pred[:, 1]
            )
        )

        mlflow.log_metric("calibrated_f1",
                          f1_score(
                              data[label_col],
                              (0.5 <= train_pred[:, 1]).astype(int)
                          )
                          )


if __name__ == "__main__":

    logger.info("Getting settings")

    settings = TrainingSettings()

    mlflow.set_tracking_uri(settings.MODEL_URI)

    logger.info("Assembling training data")
    df = assemble_training_data(settings.DB_URI)

    logger.info("Training Lasso Model")
    train_model(
        init_lasso_logistic_regression(),
        data=df,
        feature_cols=[
            'apr', 'lender_id', 'requested',
            'loan_purpose', 'credit', 'annual_income'
        ],
        label_col="label",
        model_name="best_lasso_log_reg",
        experiment_name="Lasso Model"
    )

    logger.info("Training Ridge Model")
    train_model(
        init_ridge_logistic_regression(),
        data=df,
        feature_cols=[
            'apr', 'lender_id', 'requested',
            'loan_purpose', 'credit', 'annual_income'
        ],
        label_col="label",
        model_name="best_ridge_log_reg",
        experiment_name='Ridge Model'
    )

    logger.info("Training GBDT Model")
    train_model(
        init_gbdt_classification(),
        data=df,
        feature_cols=[
            'lender_id', 'loan_purpose', 'credit', 'requested',
            'annual_income', 'apr'
        ],
        label_col="label",
        model_name="best_gbdt",
        experiment_name='GBDT Model'
    )