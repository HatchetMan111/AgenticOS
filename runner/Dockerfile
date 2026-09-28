FROM python:3.12-slim
WORKDIR /srv
COPY runner/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY runner ./runner
COPY store ./store
CMD ["python", "-m", "runner.worker"]
