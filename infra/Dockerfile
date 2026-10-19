# Production container image (in this demo repo, scripts/deploy.sh does the local deployment instead)
FROM python:3.12-slim
WORKDIR /srv/app
COPY requirements.txt ./
RUN pip install --no-cache-dir fastapi "uvicorn[standard]"
COPY app ./app
COPY db ./db
COPY scripts/migrate.py ./scripts/migrate.py
COPY VERSION ./VERSION
ENV APP_ENV=production DB_PATH=/data/orders.db
EXPOSE 8100
CMD ["sh", "-c", "python scripts/migrate.py $DB_PATH && uvicorn app.main:app --host 0.0.0.0 --port 8100"]
