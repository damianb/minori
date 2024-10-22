ARG GROUP_REGISTRY
FROM ${GROUP_REGISTRY}/common-containers/uvicorn-fastapi:3.12

COPY . /app
WORKDIR /app

RUN pip install --editable . --progress-bar off

HEALTHCHECK --interval=3m --start-period=1m \
  CMD wget --no-verbose --tries=1 --spider http://localhost:5000/api/health || exit 1

CMD ["uvicorn", "minori.api:app", "--host", "0.0.0.0", "--port", "5000", "--forwarded-allow-ips", "*"]
