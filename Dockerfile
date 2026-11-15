FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PYTHONPATH=/app/src VAULT_LIBRARY_ROOT=/library VAULT_DB_PATH=/data/vault.sqlite3
RUN mkdir -p /library /data
VOLUME ["/library","/data"]
EXPOSE 8000
CMD ["uvicorn","vault.api:app","--host","0.0.0.0","--port","8000"]
