FROM node:20-slim AS frontend-builder
WORKDIR /app/webapp
COPY webapp/package*.json ./
RUN npm ci
COPY webapp/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml constraints.txt ./
RUN pip install --no-cache-dir -e .

COPY --from=frontend-builder /app/webapp/dist ./webapp/dist

COPY api/ ./api/
COPY src/ ./src/

RUN mkdir -p /data/chroma_db

ENV CHROMA_PATH=/data/chroma_db
ENV DATABASE_URL=sqlite:////data/ggpt.db

EXPOSE 8000

CMD ["sh", "-c", "python -m uvicorn api.app:app --host 0.0.0.0 --port ${PORT:-8000}"]
