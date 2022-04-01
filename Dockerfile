FROM python:3.8

WORKDIR /app

COPY ["requirements.txt", "/app/"]
RUN pip install -r requirements.txt

COPY ["app/faucet.py", "/app/"]

WORKDIR /app
ENTRYPOINT ["python"]
CMD ["faucet.py"]
