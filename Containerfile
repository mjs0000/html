FROM registry.access.redhat.com/ubi9/python-311:latest

USER 0
WORKDIR /app

COPY pyproject.toml README.md /app/
COPY src /app/src
COPY templates /app/templates
COPY spec /app/spec
COPY examples /app/examples

RUN pip install --no-cache-dir . \
    && mkdir -p /data/uploads /data/output \
    && chgrp -R 0 /data \
    && chmod -R g=u /data

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src
ENV SOSDIAG_DATA_DIR=/data

VOLUME ["/data"]
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3).read()" || exit 1

USER 1001

CMD ["python", "-m", "sosdiag.web.app"]
