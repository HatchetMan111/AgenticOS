FROM python:3.12-slim
WORKDIR /srv
COPY scheduler/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY scheduler/app.py ./app.py
COPY store ./store
CMD ["uvicorn","app:app","--host","0.0.0.0","--port","8001"]
