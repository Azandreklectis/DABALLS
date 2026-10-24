FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN python -m pip install --upgrade pip && python -m pip install .

RUN useradd --create-home --uid 10001 daballs \
    && mkdir -p /data/artifacts /data/job-runtime \
    && chown -R daballs:daballs /app /data /home/daballs

ENV HOME=/home/daballs \
    DABALLS_DATABASE_PATH=/data/controller.sqlite3 \
    DABALLS_ARTIFACT_DIR=/data/artifacts \
    DABALLS_JOB_RUNTIME_DIR=/data/job-runtime

USER daballs
EXPOSE 8000

CMD ["uvicorn", "daballs.controller.main:app", "--host", "0.0.0.0", "--port", "8000"]
