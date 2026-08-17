FROM registry.access.redhat.com/ubi9/python-311:latest

USER 0
WORKDIR /app

COPY pyproject.toml README.md /app/
COPY src /app/src
COPY templates /app/templates
COPY spec /app/spec
COPY examples /app/examples

# The web container runs directly from /app/src, so installing the project wheel is
# unnecessary. Installing runtime dependencies explicitly avoids PEP 517 build
# isolation trying to download hatchling before the application dependencies.
# Optional private PyPI/proxy settings can be passed as build args by run.sh.
ARG SOSDIAG_PIP_INDEX_URL=""
ARG SOSDIAG_PIP_TRUSTED_HOST=""
ARG SOSDIAG_PIP_CERT=""

RUN set -eu; \
    if [ -n "$SOSDIAG_PIP_INDEX_URL" ]; then export PIP_INDEX_URL="$SOSDIAG_PIP_INDEX_URL"; fi; \
    if [ -n "$SOSDIAG_PIP_TRUSTED_HOST" ]; then export PIP_TRUSTED_HOST="$SOSDIAG_PIP_TRUSTED_HOST"; fi; \
    if [ -n "$SOSDIAG_PIP_CERT" ]; then export PIP_CERT="$SOSDIAG_PIP_CERT"; fi; \
    python -m pip install --no-cache-dir --retries 10 --timeout 60 \
      "PyYAML>=6.0" \
      "Jinja2>=3.1" \
      "pydantic>=2.7" \
      "typer>=0.12" \
      "fastapi>=0.115" \
      "uvicorn[standard]>=0.30" \
      "python-multipart>=0.0.9"; \
    mkdir -p /data/uploads /data/output; \
    chgrp -R 0 /data; \
    chmod -R g=u /data

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src
ENV SOSDIAG_DATA_DIR=/data

VOLUME ["/data"]
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3).read()" || exit 1

USER 1001

CMD ["python", "-m", "sosdiag.web.app"]
