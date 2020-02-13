FROM tiangolo/uvicorn-gunicorn:python3.7-alpine3.8

RUN sed -i 's/http:\/\/dl-cdn.alpinelinux.org/https:\/\/mirrors.aliyun.com/g' /etc/apk/repositories
ENV PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple
RUN apk update && apk add gcc libffi-dev g++ postgresql-dev make git
RUN pip install -U pip
RUN pip install poetry

WORKDIR /app
COPY poetry.lock pyproject.toml ./
RUN poetry config virtualenvs.create false && poetry install

COPY app ./

RUN apk del libffi-dev g++ make
