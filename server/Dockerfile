FROM node:20-alpine AS dashboard-builder

WORKDIR /dashboard
COPY dashboard/package*.json ./
RUN npm ci
COPY dashboard/ ./
RUN npm run build

FROM python:3.11-slim

WORKDIR /app
RUN apt-get update \
    && apt-get install -y --no-install-recommends iptables \
    && rm -rf /var/lib/apt/lists/*

COPY server/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY server/ /app/
COPY --from=dashboard-builder /dashboard/dist /app/app/static

ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "app.main"]
