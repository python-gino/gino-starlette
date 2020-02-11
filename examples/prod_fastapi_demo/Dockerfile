FROM tiangolo/uvicorn-gunicorn:python3.7-alpine3.8

LABEL Name=gino-starlette Version=0.0.1
EXPOSE 8000

WORKDIR /app
ADD . /app

# Using pip:
RUN python3 -m pip install -r requirements.txt
