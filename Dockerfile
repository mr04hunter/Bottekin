FROM python:3.12-slim

WORKDIR /app



COPY . .
RUN pip install --no-cache-dir -e .


RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*


CMD ["python", "-m", "bot"]