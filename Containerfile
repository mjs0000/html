FROM registry.access.redhat.com/ubi9/python-311:latest

USER 0
WORKDIR /app

COPY pyproject.toml README.md /app/
COPY src /app/src
COPY templates /app/templates
COPY spec /app/spec
COPY examples /app/examples

RUN pip install --no-cache-dir .
RUN mkdir -p /app/data/uploads /app/data/output && chmod -R 0775 /app/data

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

EXPOSE 8000

CMD ["python", "-m", "sosdiag.web.app"]
