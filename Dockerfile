FROM python:3.8

WORKDIR /app

COPY ["requirements.txt", "/app/"]
RUN pip install -r requirements.txt

COPY ["faucet.py", "/app/"]

ENV PORT 8080
EXPOSE 8080

ENTRYPOINT ["python"]
CMD ["faucet.py"]
