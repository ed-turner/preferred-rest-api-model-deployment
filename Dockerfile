FROM python:3.8

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN python -m pip install --upgrade pip

COPY ./dist/financial_app-0.3.5-py3-none-any.whl .

RUN python -m pip install "financial_app-0.3.5-py3-none-any.whl[serving]"
