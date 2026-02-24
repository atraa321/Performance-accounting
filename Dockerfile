FROM mcr.microsoft.com/playwright/python:v1.48.0-jammy

ENV PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/ \
    PIP_TRUSTED_HOST=mirrors.aliyun.com

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt \
    && sed -i 's|archive.ubuntu.com|mirrors.aliyun.com|g; s|security.ubuntu.com|mirrors.aliyun.com|g' /etc/apt/sources.list \
    && apt-get update \
    && (apt-get install -y --no-install-recommends fonts-noto-cjk || true) \
    && rm -rf /var/lib/apt/lists/*

COPY app /app/app
COPY alembic /app/alembic
COPY alembic.ini /app/alembic.ini

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
