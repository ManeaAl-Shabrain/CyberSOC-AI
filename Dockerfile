FROM python:3.11-slim
WORKDIR /app
RUN useradd --system --create-home --uid 10001 cybersoc
COPY pyproject.toml ./
COPY src/ src/
COPY apps/ apps/
RUN python -m pip install --no-cache-dir .
USER 10001
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
