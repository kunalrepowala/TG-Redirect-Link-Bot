FROM python:3.12-slim

# Install ffmpeg
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt /app/
RUN pip install -r /app/requirements.txt

# Copy your bot code
COPY . /app/

WORKDIR /app

CMD ["python", "main.py"]
