FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Install BentoML
RUN pip install --no-cache-dir bentoml==1.3.5

# Copy your project
COPY . /bento
WORKDIR /bento

# Expose BentoML default port
EXPOSE 3000

# Start the Bento service directly
CMD ["bentoml", "serve", "siteeui_service.py:svc", "--port", "3000", "--host", "0.0.0.0"]
