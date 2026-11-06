FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app
#Below command is to install ping utility in the container to run ping command in test_health_check.py
RUN apt-get update \
 && apt-get install -y --no-install-recommends iputils-ping \
 && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p reports/logs reports/results
CMD ["pytest", "-v", "-s", "-ra"]