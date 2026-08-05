# Low-Ops Flask Default Template

<p align="left">
  <img src="./images/logo.svg" height="50" width="60" alt="Low-Ops logo" style="background: white; padding: 20px; border-radius: 10px; margin-right: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1)"/>
  <img src="./images/flask-logo.svg" height="50" width="60" alt="Flask logo" style="background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1)"/>
</p>

People desk starter: Flask, PostgreSQL, and S3-compatible storage.

## Local development

```bash
cp .env.example .env
pip install -r requirements.txt
flask --app app run --host 0.0.0.0 --port 8000
```

## Docker

```bash
docker compose up --build
```

- App: `PORT` (default `8000`), health `GET /ready`
- Metrics: `METRICS_PORT` (default `8001`) Prometheus `/metrics`
- OpenAPI schema: `/api/schema`
- Compose includes PostgreSQL and MinIO
