# 운영용 컨테이너 이미지 (데모 저장소의 로컬 배포는 scripts/deploy.sh 가 대신한다)
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
