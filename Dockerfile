FROM python:3.12.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PATH=/opt/venv/bin:$PATH
WORKDIR /app

RUN python -m venv /opt/venv && addgroup --system --gid 10001 civicai && adduser --system --uid 10001 --gid 10001 --home /nonexistent civicai
COPY pyproject.toml alembic.ini ./
COPY backend ./backend
RUN pip install --no-cache-dir .

USER 10001:10001
EXPOSE 8000
CMD ["uvicorn", "civicai.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "172.28.0.10"]
