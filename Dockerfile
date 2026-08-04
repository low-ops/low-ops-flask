FROM python:3.13-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x entrypoint.sh \
    && python -c "import compileall; compileall.compile_dir('.', quiet=1)"

ENV PORT=8000
ENV METRICS_PORT=8001
EXPOSE 8000 8001

ENTRYPOINT ["./entrypoint.sh"]
